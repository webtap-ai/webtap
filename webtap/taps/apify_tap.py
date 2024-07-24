from pydantic import BaseModel, validator, PrivateAttr, root_validator
from webtap.base_tap import BaseTap, RetrieverResult, Retriever
from langchain import PromptTemplate, OpenAI, LLMChain
from langchain.chains import create_extraction_chain
import json, logging, os, openai, re, time
from importlib.resources import files
from webtap.custom_chat_openai import CustomChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from typing import Any, Optional
from pathlib import Path
import re, json, copy, demjson3
from typing import List, Dict
from apify_client import ApifyClient


class Actor(BaseModel):
    """
    Actor is a representation of an Apify Actor: it contains original Apify Actor data
    """

    id: str
    name: str
    description: str
    users: str = None
    run: Optional[str] = None
    author: Optional[str] = None
    example_output_response: Optional[dict] = None
    example_input: Optional[dict] = None
    full_readme_text: Optional[str] = None


class ActorParameters(BaseModel):
    """
    ActorParameters is a representation of an Apify Actor API parameters as they are described in Apify API documentation
    (They are usually added as a query string to the actor api url)
    """

    actorId: str  # Actor ID or a tilde-separated owner's username and actor name.
    timeout: int = None  # Optional timeout for the run, in seconds.
    memory: int = None  # Memory limit for the run, in megabytes.
    maxItems: int = (
        None  # The maximum number of items that the actor run should return.
    )
    build: str = None  # Specifies the actor build to run.
    waitForFinish: int = (
        None  # The maximum number of seconds the server waits for the run to finish.
    )
    webhooks: str = None  # Specifies optional webhooks associated with the actor run.


class ActorInput(BaseModel):
    """
    ApifyInput is a representation of an Apify Actor input: it contains the parameters and the body of the actor
    """

    # set parameters as default ActorParameters with default values
    parameters: ActorParameters
    body: dict


class ApifyRetriever(Retriever):
    """
    ApifyRetrieverModel is the rapresentation of a how the data task can be can_fulfilled.
    For apify type will be apify, model id will be the Apify actor id, as exposed on Apify API documentation.
    """

    type: str = "apify"
    input: ActorInput


class ApifyRetrieverResult(RetrieverResult):
    """
    ApifyTapReturn is the abstract schema rappresentation of the return value of a tap.
    """

    retriever: ApifyRetriever = None


class ValidateDataResult(BaseModel):
    """
    ValidateDataResult is the return value of a data validation
    """

    is_valid: bool
    explanation: str


class ApifyTapActor(BaseModel):
    """
    ApifyTapActor is a Tap representation of an Apify Actor: it encapsulate an Apify Actor, its input data and has some additional data useful for Tap purposes
    """

    actor: Actor
    input_body_schema: dict
    input_body_summary: str
    output_fields: str
    output_views: dict = dict({})


class ApifyTap(BaseTap):
    """
    Apify Tap is a generic tap that is able to manage/scrape/validate data from an Apify Actor.
    It works by defining info about the actor and the prompt template
    """

    entities: List[str]
    filters: List[str]
    options: List[str]
    special_instructions: List[str]
    examples: list
    test_cases: list
    apify_tap_actor: ApifyTapActor
    memory_requirement: int = None
    openai_model: str = "gpt-3.5-turbo"
    # 1 token should be ~ 3.5 chars; to be safe setting each message length limit to token limit * 3
    MESSAGE_LENGTH_GPT3_USE_16k: int = 4097 * 3
    MESSAGE_LENGTH_GPT4_USE_32k: int = 8192 * 3
    data_file_dir: Path = Path(files(__package__).joinpath("../../data/apify_tap/"))
    prompt_file: Path = data_file_dir.joinpath("prompt.txt")
    output_response_schema_file: Path = data_file_dir.joinpath(
        "output_response_schema.json"
    )
    prompt_template: str = prompt_file.read_text()
    _llm: CustomChatOpenAI = PrivateAttr()
    _logger: logging.Logger = PrivateAttr()

    @property
    def output_response_schema(self):
        with open(self.output_response_schema_file) as f:
            return json.load(f)

    def load_llm(self):
        # check if openai os env variable is set
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY env variable is not set")
        openai.api_key = os.environ["OPENAI_API_KEY"]
        # set langchanin verbose to true if loggin level is info or above
        verbose = self._logger.getEffectiveLevel() <= logging.INFO
        self._llm = CustomChatOpenAI(
            temperature=0, model=self.openai_model, verbose=verbose
        )

    def __init__(self, *args, **kwargs):
        # Extract the necessary attributes from kwargs
        name = kwargs.get("name")
        entities = kwargs.get("entities")
        filters = kwargs.get("filters")
        options = kwargs.get("options")

        entities_joined = ", ".join(entities)
        filters_joined = ", ".join(filters)
        options_joined = ", ".join(options)

        # if description is not provided set in kwargs a default description
        if "description" not in kwargs:
            kwargs["description"] = (
                """This is {{name}}, it can return you data about {{entities_joined}}, filtering results by {{filters_joined}}. Following options are accepted: {{options_joined}}. Data can be returned in Excel, JSON, CSV, and other formats."""
            )

        # if chat_salutation is not provided set in kwargs a default chat_salutation
        if "chat_salutation" not in kwargs:
            kwargs[
                "chat_salutation"
            ] = """
Hi, I'm **{{name}}**. I'm here to assist you in obtaining data about *{{entities_joined}}*. <br>
- You can use the following filters: _{{filters_joined}}_ <br>
- And apply the following options: `{{options_joined}}` <br>
- Ensure your queries closely resemble the provided examples. <br>
- Always specify in query the number of results needed. <br>

**Getting started** <br>
Try running one of the pre-built queries below.  If you get stuck, contact us through our [in app chat](mailto:info+contact@webtap.ai). <br>
"""
        # Call the parent class's init function
        super().__init__(*args, **kwargs)

        # Init logger
        self._logger = logging.getLogger(__name__)
        # format description and chat_salutation
        self.description = self.format_json(
            self.description,
            name=name,
            entities_joined=entities_joined,
            filters_joined=filters_joined,
            options_joined=options_joined,
        )
        self.chat_salutation = self.format_json(
            self.chat_salutation,
            name=name,
            entities_joined=entities_joined,
            filters_joined=filters_joined,
            options_joined=options_joined,
        )
        # sanitize examples
        self.sanitize_examples()
        # Init llm
        self.load_llm()

    def set_llm_model(self, model_name: str):
        self.openai_model = model_name
        # regenerate LLM
        self.load_llm()

    def extract_last_json_object(self, text):
        stack = []
        json_end = None
        for i in reversed(range(len(text))):
            if text[i] == "}":
                if json_end is None:
                    json_end = i
                stack.append("}")
            elif text[i] == "{":
                stack.pop()
                if len(stack) == 0:
                    return json.loads(text[i : json_end + 1])

        raise ValueError("No valid JSON object found in the text.")

    def format_json(self, json_obj, **kwargs):
        """
        Formats a JSON object by replacing placeholders with actual values.

        :param json_obj: The JSON object to format.
        :param kwargs: The values to replace the placeholders with.
        :return: The formatted JSON object.
        """
        # Convert the JSON object to a string
        json_str = json.dumps(json_obj)

        # Use a regular expression to replace placeholders with actual values
        for key, value in kwargs.items():
            json_str = re.sub(r"\{\{" + key + r"\}\}", str(value), json_str)

        # Convert the string back to a JSON object
        formatted_json_obj = json.loads(json_str)

        return formatted_json_obj

    def sanitize_examples(self):
        """
        Sanitize the examples
        """
        # iterate examples
        for example in self.examples:
            # sanitize example
            # build missing optional fields
            if "public" not in example:
                example["public"] = True
            if "post_run_chat_message" not in example:
                example["post_run_chat_message"] = None
            if "title" not in example or example["title"] is None:
                example["title"] = example["data_task"]

    # return a list of examples suitable for use in the prompt: without public, post_run_chat_message and title fields
    def get_prompt_examples(self) -> List[str]:
        prompt_examples = copy.deepcopy(self.examples)
        for example in prompt_examples:
            # remove public, post_run_chat_message and title fields
            if "public" in example:
                del example["public"]
            if "post_run_chat_message" in example:
                del example["post_run_chat_message"]
            if "title" in example:
                del example["title"]
        return prompt_examples

    def generate_prompt_messages(self, data_task: str) -> List[str]:
        # generate the chat messages
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            self.prompt_template
        )
        chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
        chat_prompt_formatted = chat_prompt.format_prompt(
            actor_name=self.apify_tap_actor.actor.name,
            examples=self.get_prompt_examples(),
            output_response_schema=self.format_json(
                self.output_response_schema, actor_name=self.apify_tap_actor.actor.name
            ),
            list_of_returned_fields=self.apify_tap_actor.output_fields,
            input_json_schema=self.apify_tap_actor.input_body_schema,
            special_instructions="\n".join(
                self.format_json(
                    self.special_instructions,
                    actor_name=self.apify_tap_actor.actor.name,
                )
            ),
            data_task=data_task,
            actor_input_summary=self.apify_tap_actor.input_body_summary,
        )
        messages = chat_prompt_formatted.to_messages()
        return messages

    def _run_chain_and_get_response(self, messages: List[str]) -> dict:
        """
        Helper method to run the chain and get the response.
        This method will retry once if an exception occurs or if can_fulfill is false.
        """
        for _ in range(2):  # Retry once
            try:
                # Run the chain
                chain_output = self._llm(messages)

                # Log prompt response
                self._logger.info(
                    "Chain executed correctly, chain plain response: %s", chain_output
                )

                # Check that chain_output is not empty and is object with content property
                if chain_output is None or not hasattr(chain_output, "content"):
                    raise ValueError(
                        "Data returned from LLM is empty or doesn't contain content property"
                    )

                # Extract list of json values from chain_output
                prompt_response = self.extract_last_json_object(chain_output.content)

                # Check that prompt_response contains can_fulfill and explanation
                if (
                    "can_fulfill" not in prompt_response
                    or "explanation" not in prompt_response
                ):
                    raise ValueError(
                        "Data returned from LLM doesn't contain can_fulfill or explanation"
                    )

                # If can_fulfill is true, return the prompt_response
                if prompt_response["can_fulfill"]:
                    return prompt_response
                else:
                    # Log the attempt and the decision to retry or return false
                    if _ == 0:
                        self._logger.info(
                            "can_fulfill is false on first attempt, retrying..."
                        )
                    else:
                        self._logger.info(
                            "can_fulfill is false on second attempt, returning false..."
                        )
                        return prompt_response

            except ValueError as e:
                self._logger.error("Error occurred: %s", e)

        # If the method hasn't returned after 2 attempts, raise an exception
        raise ValueError("Failed to get a valid response after 2 attempts")

    def get_retriever(self, data_task: str) -> ApifyRetrieverResult:
        # Init execution start time
        execution_start_time = time.time()
        self._logger.info(" **** Starting retriever retrieval ****")

        # Generate the chat messages
        messages = self.generate_prompt_messages(data_task)

        # Log the full chat prompt
        self._logger.info("Full chat prompt: %s", messages)

        # If with gpt3.5 messages length is over 2000 chars use gpt 16k
        # If with gpt4 messages length is over 32000 chars use gpt4-32k
        messages_length = len("".join(str(message) for message in messages))
        if (
            self.openai_model == "gpt-3.5-turbo"
            and messages_length > self.MESSAGE_LENGTH_GPT3_USE_16k
        ):
            self._logger.debug(
                "Chat prompt length is over %s, using gpt-3.5-turbo-16k",
                self.MESSAGE_LENGTH_GPT3_USE_16k,
            )
            openai_model = "gpt-3.5-turbo-16k"
            self.set_llm_model(openai_model)
        elif (
            self.openai_model == "gpt-4"
            and messages_length > self.MESSAGE_LENGTH_GPT4_USE_32k
        ):
            self._logger.debug(
                "Chat prompt length is over %s, using gpt-4-32k",
                self.MESSAGE_LENGTH_GPT4_USE_32k,
            )
            openai_model = "gpt-4-32k"
            # Currently gpt-4-32k is not yet enabled to use
            openai_model = "gpt-4"
            self.set_llm_model(openai_model)

        # Run the chain and get the response
        prompt_response = self._run_chain_and_get_response(messages)

        # Log prompt response
        self._logger.info(
            "Prompt executed correctly, prompt response: %s", prompt_response
        )

        retriever = None
        if prompt_response["can_fulfill"]:
            retriever = ApifyRetriever(
                id=self.apify_tap_actor.actor.id,
                input=ActorInput(
                    parameters=ActorParameters(actorId=self.apify_tap_actor.actor.id),
                    body=prompt_response["input_params"],
                ),
            )

        # Create tap return
        tapReturn = ApifyRetrieverResult(
            can_fulfill=prompt_response["can_fulfill"],
            explanation=prompt_response["explanation"],
            retriever=retriever,
            alternative_fulfillable_data_task=prompt_response.get(
                "alternative_fulfillable_data_task", None
            ),
        )

        execution_time = time.time() - execution_start_time
        self._logger.info("Tap execution time: %s", execution_time)

        return tapReturn

    def run_actor(self, actor_input: ActorInput, max_items: int = 5) -> List[str]:
        # Initialize the ApifyClient with API token
        if "APIFY_API_TOKEN" not in os.environ:
            self._logger.error("APIFY_API_TOKEN env variable is not set")
            raise ValueError("APIFY_API_TOKEN env variable is not set")
        apify_api_token = os.environ["APIFY_API_TOKEN"]

        # disabling as it only works for "paid" actors
        #params = {"max_items": max_items}
        params = {}

        if self.memory_requirement is not None:
            params["memory_mbytes"] = self.memory_requirement

        params["run_input"] = actor_input.body

        self._logger.info(f"Actor params: {params}")

        client = ApifyClient(apify_api_token)
        # Start the actor and immediately return the Run object
        actor_run = client.actor(self.apify_tap_actor.actor.id).start(**params)
        self._logger.info("Actor started, waiting for it to finish...")

        self._logger.info(f"Actor run: {actor_run}")

        # Loop until the actor run is finished
        actor_run_id = actor_run["id"]
        MAX_LOOP = 60
        loops = 0
        while True:
            loops += 1
            if loops > MAX_LOOP:
                self._logger.error(f"Actor run didn't finish in {MAX_LOOP} loops")
                raise Exception(f"Actor run didn't finish in {MAX_LOOP} loops")

            # Get the current actor run state
            # Initialize the RunClient with the actor run ID
            run_client = client.run(actor_run_id)

            run_data = run_client.get()
            actor_run_state = run_data["status"]
            self._logger.info(f"# {loops}")
            self._logger.info(f"Actor run state is: {actor_run_state}")

            # If the actor run is still running or has succeeded, fetch the items from the dataset
            if actor_run_state in ["RUNNING"]:
                dataset_items = (
                    client.dataset(actor_run["defaultDatasetId"]).list_items().items
                )
                self._logger.info(
                    f"Fetched {len(dataset_items)} items from the dataset"
                )

                # If the number of items fetched is greater than or equal to max_items, return the items
                if len(dataset_items) >= max_items:
                    # abort the actor run
                    run_client.abort()
                    self._logger.info(
                        "More than or equal to max_items fetched, aborting actor run"
                    )
                    self._logger.info(f"Actor run aborted")
                    return dataset_items

            if actor_run_state in ["SUCCEEDED"]:
                dataset_items = (
                    client.dataset(actor_run["defaultDatasetId"]).list_items().items
                )
                self._logger.info(
                    f"Fetched {len(dataset_items)} items from the dataset"
                )
                return dataset_items

            # If the actor run is not running and not succeeded, log an error and raise an exception
            # If the actor run is ready, simply wait 5 seconds and continue the loop
            elif actor_run_state not in ["RUNNING", "SUCCEEDED", "READY"]:
                self._logger.error(f"Actor run failed with state: {actor_run_state}")
                raise Exception(f"Actor run failed with state: {actor_run_state}")

            # Wait for a while before checking the actor run state again
            time.sleep(5)

    def truncate_returned_data(self, data: List) -> List:
        MAX_CHARS = 1000
        MAX_ITEMS = 5

        # Get only first 5 items
        data = data[:MAX_ITEMS]

        for item in data:
            json_str = json.dumps(item)
            while len(json_str) > MAX_CHARS:
                keys_to_delete = []
                for key, value in item.items():
                    if isinstance(value, (list, dict)):
                        keys_to_delete.append(key)
                if not keys_to_delete:
                    break  # No more keys to delete, break the loop
                # Delete the first key from the keys_to_delete list
                del item[keys_to_delete[0]]
                json_str = json.dumps(item)  # Update the json string

            # if json_str is still too long, eliminate the last property
            while len(json_str) > MAX_CHARS:
                # get the last item of item.items()
                if len(item.items()) == 0:
                    break
                last_item = list(item.items())[-1]
                # delete the last item
                del item[last_item[0]]
                json_str = json.dumps(item)  # Update the json string

        return data

    def load_json_data(self, data):
        """
        Load JSON data using demjson3. If loading fails due to the presence of the ellipsis character,
        the character is removed and loading is attempted again.
        """
        try:
            # Try to load the data as JSON
            loaded_data = demjson3.decode(data)
        except:
            # If loading fails, remove the ellipsis character and try again
            data = data.replace("…", "")
            loaded_data = demjson3.decode(data)

        # Return the loaded data
        return loaded_data

    def get_retriever_and_run(self, data_task: str) -> Dict:
        """
        Given a data task, gets a retriever and then runs the Apify actor with provided model to get the data
        """
        # get retriever
        retriever_result = self.get_retriever(data_task)
        result = {"retriever_result": retriever_result}

        if retriever_result.can_fulfill is False:
            return result

        # run actor
        try:
            actor_return = self.run_actor(retriever_result.retriever.input)
        except Exception as e:
            self._logger.error("Error while running Apify Actor: %s", e)
            raise e
        # log actor return
        self._logger.info("Actor data returned: %s", actor_return)

        # Load the actor return data using the new method
        # loaded_data = self.load_json_data(actor_return)

        # Convert the loaded data to a JSON string
        result["data"] = json.dumps(actor_return)

        return result

    def retrieve_sample_data(self, data_task: str) -> Dict:
        # Get the data
        result = self.get_retriever_and_run(data_task)

        if result["retriever_result"].can_fulfill is True:
            actor_return = result["data"]
            # Minimize data
            sample_data = self.truncate_returned_data(actor_return)
            # Prepare the return dictionary
            result["data"] = sample_data

        return result

    def validate_data(self, data_task: str, data_sample: List) -> ValidateDataResult:
        """
        Validates the data returned by Apify Actor using LLM Chain
        """
        # init logging, openai
        execution_start_time = time.time()

        self._logger.info(" **** Starting data validation ****")

        # load the prompt from the external file
        data_validator_prompt_file = self.data_file_dir.joinpath(
            "data_validator_prompt.txt"
        )
        data_validator_prompt = data_validator_prompt_file.read_text()

        # generate the chat messages
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            data_validator_prompt
        )
        chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
        chat_prompt_formatted = chat_prompt.format_prompt(
            actor_name=self.apify_tap_actor.actor.name,
            data_task=data_task,
            data_sample=data_sample,
        )
        messages = chat_prompt_formatted.to_messages()
        # log the full chat prompt
        self._logger.info("Full chat prompt: %s", messages)

        # run the chain
        chain_output = self._llm(messages)

        # log prompt response
        self._logger.info(
            "Chain executed correctly, chain plain response: %s", chain_output
        )

        # check that chain_output is not empty and is object with content property
        if chain_output is None or not hasattr(chain_output, "content"):
            raise ValueError(
                "Data returned from LLM is empty or doesn't contain content property"
            )

        # extract list of json values from chain_output
        try:
            prompt_response = self.extract_last_json_object(chain_output.content)
        except ValueError:
            raise ValueError("Data returned from LLM doesn't contain a valid json")

        # log prompt response
        self._logger.info(
            "Prompt executed correctly, prompt response: %s", prompt_response
        )

        execution_time = time.time() - execution_start_time
        self._logger.info("Validation execution time: %s", execution_time)

        # check that prompt_response contains is_valid and explanation
        if "is_valid" not in prompt_response or "explanation" not in prompt_response:
            raise ValueError(
                "Data returned from LLM doesn't contain is_valid or explanation"
            )

        return ValidateDataResult(
            is_valid=prompt_response["is_valid"],
            explanation=prompt_response["explanation"],
        )
