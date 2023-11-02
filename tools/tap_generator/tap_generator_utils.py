import logging, demjson3, json, csv, sys, re, os, json, openai, time
from pathlib import Path
from webtap.tap_manager import TapManager
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from webtap.taps.apify_tap import ApifyTap
from apify_client import ApifyClient
from typing import List, Dict
from langchain.chat_models import ChatOpenAI


class TapGeneratorUtils:
    def __init__(self, logger):
        self.logger = logger
        # 1 token should be ~ 3.5 chars; to be safe setting each message length limit to token limit * 3
        self.MESSAGE_LENGTH_GPT3_USE_16k: int = 4097 * 3
        self.MESSAGE_LENGTH_GPT4_USE_32k: int = 8192 * 3

    def load_data_from_json(self, file_path):
        # This function loads data from a given JSON file and returns it as a dictionary
        with open(file_path, "r") as jsonfile:
            data = json.load(jsonfile)
        return data

    def extract_last_json_object(self, text):
        # Initialize stack and json_end
        stack = []
        json_end = None
        # Loop through the text in reverse
        for i in reversed(range(len(text))):
            if text[i] == "}":
                # If json_end is None, set it to the current index
                if json_end is None:
                    json_end = i
                # Append '}' to the stack
                stack.append("}")
            elif text[i] == "{":
                # Pop from the stack
                stack.pop()
                # If the stack is empty, return the JSON object
                if len(stack) == 0:
                    json_string = text[i : json_end + 1]
                    self.logger.debug("Extracted JSON object: " + json_string)
                    try:
                        return demjson3.decode(json_string)
                    except demjson3.JSONDecodeError as e:
                        error_message = "Error while decoding JSON object: " + str(e)
                        self.logger.error(error_message)
                        raise ValueError(error_message)

        # If no valid JSON object is found, raise an error
        self.logger.error("No valid JSON object found in the text.")
        raise ValueError("No valid JSON object found in the text.")

    def run_json_prompt_llm(self, prompt_template_file, input_vars, openai_model):
        # Load the prompt template
        with open(
            Path(__file__).parent.parent.parent
            / "data"
            / "tap_generator"
            / prompt_template_file,
            "r",
        ) as file:
            prompt_template = file.read()

        # generate the chat messages
        human_message_prompt = HumanMessagePromptTemplate.from_template(prompt_template)
        chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
        chat_prompt_formatted = chat_prompt.format_prompt(**input_vars)
        messages = chat_prompt_formatted.to_messages()

        # log the full chat prompt

        debug_output = ""
        for message in messages:
            content_lines = message.content.split("\n")
            for line in content_lines:
                debug_output += line + "\n"
        self.logger.debug("Chat prompt: \n" + debug_output)

        # if with gpt3.5 messages length is over 2000 chars use gpt 16k
        # if with gpt4 messages length is over 32000 chars use gpt4-32k
        messages_length = len("".join(str(message) for message in messages))
        if (
            openai_model == "gpt-3.5-turbo"
            and messages_length > self.MESSAGE_LENGTH_GPT3_USE_16k
        ):
            self.logger.debug(
                "Chat prompt length is over %s, using gpt-3.5-turbo-16k. Current total size of the string is %s",
                self.MESSAGE_LENGTH_GPT3_USE_16k,
                messages_length,
            )
            openai_model = "gpt-3.5-turbo-16k"
        elif (
            openai_model == "gpt-4"
            and messages_length > self.MESSAGE_LENGTH_GPT4_USE_32k
        ):
            self.logger.debug(
                "Chat prompt length is over %s, using gpt-4-32k. Current total size of the string is %s",
                self.MESSAGE_LENGTH_GPT4_USE_32k,
                messages_length,
            )
            openai_model = "gpt-4-32k"
            # currently gpt-4-32k is not yet enabled to use
            openai_model = "gpt-4"

        # Init llm
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY env variable is not set")
        openai.api_key = os.environ["OPENAI_API_KEY"]
        # set langchanin verbose to true if loggin level is info or above
        verbose = self.logger.getEffectiveLevel() <= logging.INFO
        llm = ChatOpenAI(temperature=0, model=openai_model, verbose=verbose)

        # run the chain
        chain_output = llm(messages)

        # Check that chain_output is not empty, is object with content property
        if chain_output is None or not hasattr(chain_output, "content"):
            error_message = (
                "Data returned from LLM is empty or doesn't contain content property"
            )
            self.logger.error(error_message)
            raise ValueError(error_message)

        self.logger.debug("Chain output: %s", chain_output.content)

        # Extract the last JSON object
        last_json_object = self.extract_last_json_object(chain_output.content)
        self.logger.debug("Last JSON object extracted: %s", last_json_object)

        if not last_json_object:
            error_message = "No valid JSON object found in the chain output."
            self.logger.error(error_message)
            raise ValueError(error_message)

        return last_json_object

    def load_json_example_data(self, json_string, key):
        # Remove the ellipsis character if json load doesn't work
        try:
            data = demjson3.decode(json_string)
            self.logger.debug(f"Successfully loaded JSON example data for {key}.")
            return data
        except demjson3.JSONDecodeError as e:
            self.logger.debug(
                f"Failed to load JSON example data for {key}. Attempting to clean the data."
            )
            cleaned_string = json_string.replace("…", "")
            try:
                data = demjson3.decode(cleaned_string)
                self.logger.debug(
                    f"Successfully loaded cleaned JSON example data for {key}."
                )
                return data
            except demjson3.JSONDecodeError as e:
                # log and return
                self.logger.error(
                    f"Error while cleaning JSON example data for {key}: " + str(e)
                )
                self.logger.debug(
                    f"Failed to load cleaned JSON example data for {key}."
                )
                return None

    def contains_legal_ethical_policy_word(self, text):
        legal_ethical_policy_words = ["policy", "privacy", "legal", "complian", "ethic"]
        text_lower = text.lower()
        for word in legal_ethical_policy_words:
            if word in text_lower:
                self.logger.debug(f"Found legal/ethical/policy word '{word}' in text.")
                return True
        self.logger.debug("No legal/ethical/policy words found in text.")
        return False

    def contains_proxy_word(self, text):
        proxy_words = ["proxy"]
        text_lower = text.lower()
        for word in proxy_words:
            if word in text_lower:
                self.logger.debug(f"Found proxy word '{word}' in text.")
                return True
        self.logger.debug("No proxy words found in text.")
        return False

    def delete_tap_index(self, tap_id):
        # Update taps_index.json
        taps_index_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "tap_manager"
            / "taps_index.json"
        )
        with open(taps_index_path, "r+") as f:
            taps_index = json.load(f)
            if tap_id in taps_index:
                # Remove tap_id from the taps_index
                del taps_index[tap_id]
                # Write the updated taps_index back to the file
                f.seek(0)
                self.logger.info("Tap removed from taps_index.json")
                self.logger.debug(f"Tap {tap_id} removed from taps_index.json")

    def apify_run_actor(
        self, actor_id, actor_input_body, max_items: int = 5
    ) -> List[str]:
        # Initialize the ApifyClient with API token
        if "APIFY_API_TOKEN" not in os.environ:
            self.logger.error("APIFY_API_TOKEN env variable is not set")
            raise ValueError("APIFY_API_TOKEN env variable is not set")
        apify_api_token = os.environ["APIFY_API_TOKEN"]

        client = ApifyClient(apify_api_token)
        # Start the actor and immediately return the Run object
        actor_run = client.actor(actor_id).start(run_input=actor_input_body)
        self.logger.info(f"Actor {actor_id} started, waiting for it to finish...")

        self.logger.debug(f"Actor run: {actor_run}")

        # Loop until the actor run is finished
        actor_run_id = actor_run["id"]
        MAX_LOOP = 60
        loops = 0
        while True:
            loops += 1
            if loops > MAX_LOOP:
                self.logger.error(f"Actor run didn't finish in {MAX_LOOP} loops")
                raise Exception(f"Actor run didn't finish in {MAX_LOOP} loops")

            # Get the current actor run state
            # Initialize the RunClient with the actor run ID
            run_client = client.run(actor_run_id)

            run_data = run_client.get()
            actor_run_state = run_data["status"]
            self.logger.info(f"# {loops}")
            self.logger.info(f"Actor run state is: {actor_run_state}")

            # If the actor run is still running or has succeeded, fetch the items from the dataset
            if actor_run_state in ["RUNNING"]:
                dataset_items = (
                    client.dataset(actor_run["defaultDatasetId"]).list_items().items
                )
                self.logger.info(f"Fetched {len(dataset_items)} items from the dataset")

                # If the number of items fetched is greater than or equal to max_items, return the items
                if len(dataset_items) >= max_items:
                    # abort the actor run
                    run_client.abort()
                    self.logger.info(
                        "More than or equal to max_items fetched, aborting actor run"
                    )
                    self.logger.info(f"Actor run aborted")
                    return dataset_items

            if actor_run_state in ["SUCCEEDED"]:
                dataset_items = (
                    client.dataset(actor_run["defaultDatasetId"]).list_items().items
                )
                self.logger.info(f"Fetched {len(dataset_items)} items from the dataset")
                return dataset_items

            # If the actor run is not running and not succeeded, log an error and raise an exception
            # If the actor run is ready, simply wait 5 seconds and continue the loop
            elif actor_run_state not in ["RUNNING", "SUCCEEDED", "READY"]:
                self.logger.error(f"Actor run failed with state: {actor_run_state}")
                raise Exception(f"Actor run failed with state: {actor_run_state}")

            # Wait for a while before checking the actor run state again
            time.sleep(5)

    """
        This method emulates webtap universal scraper without using GPT calls
    """

    def manual_webtap_universal_scraper(self, url, instructions, required_keys):
        actor_id = "drobnikj/extended-gpt-scraper"

        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY env variable is not set")
        openai_api_key = os.environ["OPENAI_API_KEY"]

        actor_input_params = {
            "startUrls": [{"url": url}],
            "openaiApiKey": openai_api_key,
            "instructions": instructions,
            "model": "gpt-3.5-turbo-16k",
        }

        # Use apify_run_actor instead of process_actor
        actor_data_list = self.apify_run_actor(actor_id, actor_input_params)
        self.logger.debug("Actor returned data: " + str(actor_data_list))

        # Check if the first element of data array contains the "jsonAnswer" key
        if "jsonAnswer" not in actor_data_list[0]:
            raise ValueError(
                "First element of data array does not contain 'jsonAnswer' key"
            )

        # Check if "jsonAnswer" is a JSON object
        if not isinstance(actor_data_list[0]["jsonAnswer"], dict):
            raise ValueError("'jsonAnswer' is not a JSON object")

        actor_data_json_answer = actor_data_list[0]["jsonAnswer"]

        # Check if the required keys are in the returned data
        missing_keys = [
            key
            for key in required_keys
            if key not in actor_data_json_answer or not actor_data_json_answer[key]
        ]

        if missing_keys:
            raise ValueError(
                "Returned data does not contain all the required keys. Missing keys: "
                + str(missing_keys)
            )

        return actor_data_json_answer

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


"""

    def load_data_from_csv(self, file_path):
        # This function loads data from a given CSV file and returns it as a dictionary
        csv.field_size_limit(sys.maxsize)
        data = {}
        with open(file_path, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                actor_id = row["actor_id"]
                # Create a new dictionary for each row, excluding the 'actor_id' field
                row_dict = {
                    key: value for key, value in row.items() if key != "actor_id"
                }
                data[actor_id] = row_dict
        return data

    def load_data_from_db(self, table_name):
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            "postgresql://stefanopochet@localhost:5432/apify-store-scraper"
        )
        # Create a cursor object
        cur = conn.cursor()
        # Execute the SQL query
        cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
        # Fetch all rows from the cursor
        rows = cur.fetchall()
        # Get the column names from the cursor description
        column_names = [desc[0] for desc in cur.description]
        # Close the cursor and connection
        cur.close()
        conn.close()
        # Create a dictionary for each row, excluding the 'actor_id' field
        data = {}
        for row in rows:
            actor_id = row[column_names.index("actor_id")]
            row_dict = {key: value for key, value in zip(column_names, row)}
            data[actor_id] = row_dict

        return data

 

    def webtap_universal_scraper(self, data_task, required_keys, openai_model):
        # Instantiate TapManager and get the tap
        tap_manager = TapManager()
        tap = tap_manager.get_tap("universal")

        # Retrieve sample data
        # set use gpt4
        tap.set_llm_model(openai_model)
        retriever_result = tap.get_retriever(data_task)
        self.logger.info(f"Retriever result for data task.")
        self.logger.debug(f"Retriever result for data task: {retriever_result}")

        # If can_fulfill is False, log and return None
        if not retriever_result.can_fulfill:
            self.logger.info(
                f"Webtap retriever returned that data task cannot be fulfilled."
            )
            # raise exception
            raise ValueError("Webtap retriever returned that data cannot be fulfilled")

        self.logger.debug(
            "Retriever result is ok, going to run universal scraper apify"
        )

        try:
            data = tap.run_actor(retriever_result.retriever.input)
        except Exception as e:
            raise ValueError(
                "Error while getting actor description, while running extended gpt scraper actor: "
                + str(e)
            )

        # Check if data array is not empty
        if not data:
            raise ValueError("Data array is empty")

        # Check if the first element of data array contains the "jsonAnswer" key
        if "jsonAnswer" not in data[0]:
            raise ValueError(
                "First element of data array does not contain 'jsonAnswer' key"
            )

        # Check if "jsonAnswer" is a JSON object
        if not isinstance(data[0]["jsonAnswer"], dict):
            raise ValueError("'jsonAnswer' is not a JSON object")

        actor_data = data[0]["jsonAnswer"]

        # Check if the required keys are in the returned data
        missing_keys = [
            key for key in required_keys if key not in actor_data or not actor_data[key]
        ]

        if missing_keys:
            raise ValueError(
                "Returned data does not contain all the required keys. Missing keys: "
                + str(missing_keys)
            )

        return actor_data


    def _webtap_universal_scraper(self, data_task, required_keys, openai_model):
        # Instantiate TapManager and get the tap
        tap_manager = TapManager()
        tap = tap_manager.get_tap("universal")

        # Retrieve sample data
        # set use gpt4
        tap.set_llm_model(openai_model)
        retriever_result = tap.get_retriever(data_task)
        self.logger.info(f"Retriever result for data task.")
        self.logger.debug(f"Retriever result for data task: {retriever_result}")

        # If can_fulfill is False, log and return None
        if not retriever_result.can_fulfill:
            self.logger.info(f"Data task cannot be fulfilled.")
            # raise exception
            raise ValueError("Data task cannot be fulfilled")

        return self.process_actor(retriever_result, required_keys, openai_model)

    def _process_actor(self, input, required_keys, openai_model):
        # Instantiate TapManager and get the tap
        tap_manager = TapManager()
        tap = tap_manager.get_tap("universal")
        tap.set_llm_model(openai_model)

        try:
            actor_input = input
            data = tap.run_actor(actor_input)
        except Exception as e:
            raise ValueError(
                "Error while getting actor description, while running extended gpt scraper actor: "
                + str(e)
            )

        # Check if data array is not empty
        if not data:
            raise ValueError("Data array is empty")

        # Check if the first element of data array contains the "jsonAnswer" key
        if "jsonAnswer" not in data[0]:
            raise ValueError(
                "First element of data array does not contain 'jsonAnswer' key"
            )

        # Check if "jsonAnswer" is a JSON object
        if not isinstance(data[0]["jsonAnswer"], dict):
            raise ValueError("'jsonAnswer' is not a JSON object")

        actor_data = data[0]["jsonAnswer"]

        # Check if the required keys are in the returned data
        missing_keys = [
            key for key in required_keys if key not in actor_data or not actor_data[key]
        ]

        if missing_keys:
            raise ValueError(
                "Returned data does not contain all the required keys. Missing keys: "
                + str(missing_keys)
            )

        return actor_data
    """
