from pydantic import BaseModel, validator, PrivateAttr
from webtap.base_tap import BaseTap, RetrieverResult, Retriever
from langchain import PromptTemplate, OpenAI, LLMChain
from langchain.chains import create_extraction_chain
import json, logging, os, openai, re, time
from importlib.resources import files
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from typing import Any, Optional
from pathlib import Path
import re, json
from typing import List, Dict
from apify_client import ApifyClient

class Actor(BaseModel):
    ''' 
    Actor is a representation of an Apify Actor: it contains original Apify Actor data
    '''
    id : str
    name : str
    description: str

class ActorParameters(BaseModel):
    '''
    ActorParameters is a representation of an Apify Actor API parameters as they are described in Apify API documentation 
    (They are usually added as a query string to the actor api url)
    '''
    actorId: str  # Actor ID or a tilde-separated owner's username and actor name.
    timeout: int = None  # Optional timeout for the run, in seconds.
    memory: int = None  # Memory limit for the run, in megabytes. 
    maxItems: int = None  # The maximum number of items that the actor run should return.
    build: str = None  # Specifies the actor build to run.
    waitForFinish: int = None  # The maximum number of seconds the server waits for the run to finish.
    webhooks: str = None  # Specifies optional webhooks associated with the actor run.


class ActorInput(BaseModel):
    '''
    ApifyInput is a representation of an Apify Actor input: it contains the parameters and the body of the actor
    '''
    # set parameters as default ActorParameters with default values
    parameters : ActorParameters
    body : dict

class ApifyRetriever(Retriever):
    '''
    ApifyRetrieverModel is the rapresentation of a how the data task can be can_fulfilled.
    For apify type will be apify, model id will be the Apify actor id, as exposed on Apify API documentation.
    '''
    type: str = "apify"
    input: ActorInput

class ApifyRetrieverResult(RetrieverResult):
    '''
    ApifyTapReturn is the abstract schema rappresentation of the return value of a tap.
    '''
    retriever : ApifyRetriever = None

class ValidateDataResult(BaseModel):
    '''
    ValidateDataResult is the return value of a data validation
    '''
    is_valid : bool
    explanation : str

class ApifyTapActor(BaseModel):
    '''
    ApifyTapActor is a Tap representation of an Apify Actor: it encapsulate an Apify Actor, its input data and has some additional data useful for Tap purposes
    '''
    entities : List[str]
    special_instructions: List[str]
    actor : Actor
    input_body_schema : dict
    input_body_summary: str
    output_fields: str

class ApifyTap(BaseTap):
    
    """
    Apify Tap is a generic tap that is able to manage/scrape/validate data from an Apify Actor.
    It works by simply defining info about the actor and the prompt template
    """

    name: str = "Apify Base Actor Tap"
    description: str = "Tap to operate on lots of Apify Actors by simply defining some data input"
    examples: list
    test_cases: list
    apify_tap_actor: ApifyTapActor
    openai_model : str = "gpt-3.5-turbo"
    MESSAGE_LENGTH_USE_16k : int = 15000
    data_file_dir : Path = Path(files(__package__).joinpath("../../data/apify_tap/"))
    prompt_file : Path = data_file_dir.joinpath("prompt.txt")
    output_response_schema_file : Path = data_file_dir.joinpath("output_response_schema.json")
    prompt_template : str = prompt_file.read_text()
    _llm: ChatOpenAI = PrivateAttr()
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
        self._llm = ChatOpenAI(temperature=0, model=self.openai_model, verbose=verbose)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # init logger
        self._logger = logging.getLogger(__name__)
        # init llm
        self.load_llm()
    
    def set_llm_model( self, model_name: str ):
        self.openai_model = model_name
        # regenerate LLM
        self.load_llm()
        
    def extract_last_json_object(self, text):
        stack = []
        json_end = None
        for i in reversed(range(len(text))):
            if text[i] == '}':
                if json_end is None:
                    json_end = i
                stack.append('}')
            elif text[i] == '{':
                stack.pop()
                if len(stack) == 0:
                    return json.loads(text[i:json_end+1])

        raise ValueError('No valid JSON object found in the text.')
    
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
            json_str = re.sub(r'\{\{' + key + r'\}\}', str(value), json_str)

        # Convert the string back to a JSON object
        formatted_json_obj = json.loads(json_str)

        return formatted_json_obj
    
    def generate_prompt_messages(self, data_task: str) -> List[str]:
        # generate the chat messages
        human_message_prompt = HumanMessagePromptTemplate.from_template(self.prompt_template)
        chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
        chat_prompt_formatted = chat_prompt.format_prompt(
            actor_name = self.apify_tap_actor.actor.name,
            examples = self.examples,
            output_response_schema = self.format_json(self.output_response_schema, actor_name=self.apify_tap_actor.actor.name),
            list_of_returned_fields = self.apify_tap_actor.output_fields,
            input_json_schema = self.apify_tap_actor.input_body_schema,
            special_instructions = "\n".join(self.format_json(self.apify_tap_actor.special_instructions, actor_name=self.apify_tap_actor.actor.name)),
            data_task = data_task,
            actor_input_summary = self.apify_tap_actor.input_body_summary
        )
        messages = chat_prompt_formatted.to_messages()
        return messages
    
    def get_retriever(self, data_task : str) -> ApifyRetrieverResult:
        
        # init execution start time 
        execution_start_time = time.time()
        self._logger.info(" **** Starting retriever retrieval ****")
        
        
        # generate the chat messages
        messages = self.generate_prompt_messages(data_task)
        # log the full chat prompt
        self._logger.info("Full chat prompt: %s", messages)
        
        # run the chain
        # if with gpt3.5 messages length is over 2000 chars use gpt 16k
        messages_length = len("".join(str(message) for message in messages))
        if self.openai_model == "gpt-3.5-turbo" and messages_length > self.MESSAGE_LENGTH_USE_16k:
            self._logger.info("Chat prompt length is over %s, using gpt-3.5-turbo-16k", self.MESSAGE_LENGTH_USE_16k)
            self.set_llm_model("gpt-3.5-turbo-16k")
        
        chain_output = self._llm( messages )

        # log prompt response
        self._logger.info("Chain executed correctly, chain plain response: %s", chain_output)        

        # check that chain_output is not empty and is object with content property
        if( chain_output is None or not hasattr(chain_output, "content")):
            raise ValueError("Data returned from LLM is empty or doesn't contain content property")

        # extract list of json values from chain_output
        try:
            prompt_response = self.extract_last_json_object(chain_output.content)
        except ValueError:
            raise ValueError("Data returned from LLM doesn't contain a valid json")

        # check that prompt_response contains can_fulfill and explanation
        if( "can_fulfill" not in prompt_response or "explanation" not in prompt_response):
            raise ValueError("Data returned from LLM doesn't contain can_fulfill or explanation")
        
        # log prompt response
        self._logger.info("Prompt executed correctly, prompt response: %s", prompt_response) 

        retriever = None
        if prompt_response["can_fulfill"]:
            retriever = ApifyRetriever(
                id=self.apify_tap_actor.actor.id, 
                input=ActorInput(parameters=ActorParameters(actorId=self.apify_tap_actor.actor.id), 
                body=prompt_response["input_params"]
                )
            )

        # create tap return
        tapReturn = ApifyRetrieverResult(
            can_fulfill=prompt_response["can_fulfill"], 
            explanation=prompt_response["explanation"], 
            retriever=retriever, 
            alternative_fulfillable_data_task=prompt_response.get("alternative_fulfillable_data_task", None)
        )

        execution_time = time.time() - execution_start_time
        self._logger.info("Tap execution time: %s", execution_time)

        return tapReturn
    
    def run_actor(self, actor_input : ActorInput, max_items: int = 5) -> List[str]:
        # Initialize the ApifyClient with API token
        if not "APIFY_API_TOKEN" in os.environ:
            raise ValueError("APIFY_API_TOKEN env variable is not set")
        apify_api_token = os.environ["APIFY_API_TOKEN"]

        # Set maxItems in the actor input body to the provided parameter value
        actor_input.body["maxItems"] = max_items

        client = ApifyClient(apify_api_token)
        # Run the actor and wait for it to finish
        actor_call_params = {
            "run_input": actor_input.body,
            "content_type": None,
            "memory_mbytes": "1024"
        }

        actor_call = client.actor(self.apify_tap_actor.actor.id).call(**actor_call_params)
        # Fetch results from the actor's default dataset
        dataset_items = client.dataset(actor_call['defaultDatasetId']).list_items().items

        return dataset_items
    
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
    
    def get_retriever_and_run(self, data_task : str) -> Dict:
        '''
        Given a data task, gets a retriever and then runs the Apify actor with provided model to get the data
        '''
        # get retriever

        retriever_result = self.get_retriever(data_task)
        result = {
            "retriever_result": retriever_result
        }

        if retriever_result.can_fulfill is False:
            return result
        
        # run actor
        try :
            actor_return = self.run_actor(retriever_result.retriever.input)
        except Exception as e:
            self._logger.error("Error while running Apify Aactor: %s", e)
            raise e
        # log actor return
        self._logger.info("Actor data returned: %s", actor_return)
        result["data"] = actor_return

        return result

    def retrieve_sample_data(self, data_task : str) -> Dict:
        # Get the data
        result = self.get_retriever_and_run(data_task)

        if result["retriever_result"].can_fulfill is True:
            actor_return = result["data"]
            # Minimize data
            sample_data = self.truncate_returned_data(actor_return)
            # Prepare the return dictionary
            result["data"] = sample_data

        return result

    def validate_data(self, data_task : str, data_sample : List) -> ValidateDataResult:
        '''
        Validates the data returned by Apify Actor using LLM Chain
        '''
        # init logging, openai
        execution_start_time = time.time()
        
        self._logger.info(" **** Starting data validation ****")
        
        # load the prompt from the external file
        data_validator_prompt_file = self.data_file_dir.joinpath("data_validator_prompt.txt")
        data_validator_prompt = data_validator_prompt_file.read_text()

        # generate the chat messages
        human_message_prompt = HumanMessagePromptTemplate.from_template(data_validator_prompt)
        chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
        chat_prompt_formatted = chat_prompt.format_prompt(
            actor_name = self.apify_tap_actor.actor.name,
            data_task = data_task,
            data_sample = data_sample
        )
        messages = chat_prompt_formatted.to_messages()
        # log the full chat prompt
        self._logger.info("Full chat prompt: %s", messages)

        # run the chain
        chain_output = self._llm( messages )

        # log prompt response
        self._logger.info("Chain executed correctly, chain plain response: %s", chain_output)        

        # check that chain_output is not empty and is object with content property
        if( chain_output is None or not hasattr(chain_output, "content")):
            raise ValueError("Data returned from LLM is empty or doesn't contain content property")

        # extract list of json values from chain_output
        try:
            prompt_response = self.extract_last_json_object(chain_output.content)
        except ValueError:
            raise ValueError("Data returned from LLM doesn't contain a valid json")
        
        # log prompt response
        self._logger.info("Prompt executed correctly, prompt response: %s", prompt_response) 

        execution_time = time.time() - execution_start_time
        self._logger.info("Validation execution time: %s", execution_time)
        
        # check that prompt_response contains is_valid and explanation
        if( "is_valid" not in prompt_response or "explanation" not in prompt_response):
            raise ValueError("Data returned from LLM doesn't contain is_valid or explanation")
        
        return ValidateDataResult(
            is_valid=prompt_response["is_valid"], 
            explanation=prompt_response["explanation"]
        )