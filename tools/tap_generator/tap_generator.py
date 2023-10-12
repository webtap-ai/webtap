import logging, demjson3, json
from pathlib import Path
from webtap.tap_manager import TapManager
from langchain.prompts import load_prompt
from datetime import datetime
import re, os, json, openai
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import ValidationError
from webtap.taps.apify_tap import Actor


class TapGenerator:

    def generate_tap_id(self, actor_id):
        # Replace any special characters with underscores
        actor_id_clean = re.sub(r'\W+', '_', actor_id)
        # Generate the directory name
        tap_id = f"atg_{actor_id_clean}"
        return tap_id
    
    def load_llm(self):
        # check if openai os env variable is set
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY env variable is not set")
        openai.api_key = os.environ["OPENAI_API_KEY"]
        # set langchanin verbose to true if loggin level is info or above
        verbose = self.logger.getEffectiveLevel() <= logging.INFO
        self._llm = ChatOpenAI(temperature=0, model=self.openai_model, verbose=verbose)

    def __init__(self, actor_id):
        self.actor_id = actor_id
        self.tap_id = self.generate_tap_id(actor_id)
        self.tap_dir = Path(__file__).parent.parent.parent / 'data' / 'taps' / self.tap_id
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # set up LLM
        self.openai_model = "gpt-4"
        self.load_llm()

        # Create a file handler
        current_date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path(__file__).parent.parent.parent / 'logs' / self.tap_id / current_date_time / 'atg'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f'{self.tap_id}.log'
        handler = logging.FileHandler(log_path)

        # Create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Create a stdout handler
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(formatter)

        # Add the stdout handler to the logger
        self.logger.addHandler(stdout_handler)

        # Add the handlers to the logger
        self.logger.addHandler(handler)

        self.logger.info("TapGenerator initialized for tap " + self.actor_id)

    def generate_folders_and_flow(self):
        # Create tap_dir if it doesn't exist
        self.tap_dir.mkdir(parents=True, exist_ok=True)

        # List of files to be created
        files = [
            "__init__.py",
        ]

        # List of JSON files to be created with empty array
        json_files = [
            "_test-cases.json",
            "tap-examples.json",
            "test-cases.json"
        ]

        # List of JSON files to be created with empty object
        # objects starting with _ are used doing the tap generator process but not required for the tap initialization
        json_object_files = [
            "_actor-input.json",
            "actor-output-fields.json",
            "actor-description.json",
            "actor-input-example.json",
            "actor-input-json-schema.json",
            "actor-input-summary.json",
            "tap-description.json"
        ]

        # Create each file in the list
        for file in files:
            file_path = self.tap_dir / file
            if not file_path.exists():
                # For these files, just create an empty file
                self.logger.info("Creating file " + str(file_path))
                open(file_path, 'a').close()

        # Create each JSON file in the list with an empty array
        for json_file in json_files:
            json_file_path = self.tap_dir / json_file
            if not json_file_path.exists():
                # For these JSON files, create an empty JSON array
                self.logger.info("Creating json file " + str(json_file_path))
                with open(json_file_path, 'w') as f:
                    json.dump([], f)

        # Create each JSON file in the list with an empty object
        for json_object_file in json_object_files:
            json_object_file_path = self.tap_dir / json_object_file
            if not json_object_file_path.exists():
                # For these JSON files, create an empty JSON object
                with open(json_object_file_path, 'w') as f:
                    json.dump({}, f)

        self.logger.info("Folders and files generated for tap " + self.actor_id)
        
    def _webtap_universal_scraper(self, data_task, required_keys):
        # Instantiate TapManager and get the tap
        tap_manager = TapManager()
        tap = tap_manager.get_tap("universal")

        # Retrieve sample data
        retriever_result = tap.get_retriever(data_task)
        try:
            data = tap.run_actor(retriever_result.retriever.input)
        except Exception as e:
            raise ValueError("Error while getting actor description, while running extended gpt scraper actor: " + str(e))

        # Check if data array is not empty
        if not data:
            raise ValueError("Data array is empty")

        # Check if the first element of data array contains the "jsonAnswer" key
        if "jsonAnswer" not in data[0]:
            raise ValueError("First element of data array does not contain 'jsonAnswer' key")

        # Check if "jsonAnswer" is a JSON object
        if not isinstance(data[0]["jsonAnswer"], dict):
            raise ValueError("'jsonAnswer' is not a JSON object")

        actor_data = data[0]["jsonAnswer"]

        # Check if the required keys are in the returned data
        missing_keys = [key for key in required_keys if key not in actor_data or not actor_data[key]]

        if missing_keys:
            raise ValueError("Returned data does not contain all the required keys. Missing keys: " + str(missing_keys))

        return actor_data
    
    def run_json_prompt_llm(self, prompt_template_file, input_vars):
        # Load the prompt template
        with open(Path(__file__).parent.parent.parent / 'data' / 'tap_generator' / prompt_template_file, 'r') as file:
            prompt_template = file.read()

        # generate the chat messages
        human_message_prompt = HumanMessagePromptTemplate.from_template(prompt_template)
        chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
        chat_prompt_formatted = chat_prompt.format_prompt(**input_vars)
        messages = chat_prompt_formatted.to_messages()
        
        # log the full chat prompt
        self.logger.info("Full chat prompt: %s", messages)

        # run the chain
        # if with gpt3.5 messages length is over 2000 chars use gpt 16k
        messages_length = len("".join(str(message) for message in messages))
        if self.openai_model == "gpt-3.5-turbo" and messages_length > self.MESSAGE_LENGTH_USE_16k:
            self.logger.info("Chat prompt length is over %s, using gpt-3.5-turbo-16k", self.MESSAGE_LENGTH_USE_16k)
            self.set_llm_model("gpt-3.5-turbo-16k")

        chain_output = self._llm( messages )

        # Check that chain_output is not empty, is object with content property
        if chain_output is None or not hasattr(chain_output, "content"):
            raise ValueError("Data returned from LLM is empty or doesn't contain content property")
        
        self.logger.info("Chain output: %s", chain_output.content)

        # Extract the last JSON object
        return self.extract_last_json_object(chain_output.content)
    
    def load_json_example_data(self, json_string, key):
        # Remove the ellipsis character if json load doesn't work
        try:
            data = demjson3.decode(json_string)
            return data
        except demjson3.JSONDecodeError as e:
            cleaned_string = json_string.replace("…", "")
            try:
                data = demjson3.decode(cleaned_string)
                return data
            except demjson3.JSONDecodeError as e:
                #log and return
                self.logger.error(f"Error while cleaning JSON example data for {key}: " + str(e))
                return None

    def generate_actor_original_data(self):
        actor_description_path = self.tap_dir / 'actor-description.json'
        
        # Check if actor-description.json already contains an 'id' key
        if actor_description_path.exists():
            with open(actor_description_path, 'r') as json_file:
                actor_description = demjson3.decode(json_file.read())
                if 'id' in actor_description:
                    self.logger.info("Actor description already exists for tap " + self.actor_id)
                    return

        self.logger.info("Retrieving sample data for tap " + self.actor_id)
        self.logger.info("This may take a few minutes...")
        # Define the data_task
        data_task = f"Go to https://apify.com/{self.actor_id}, return json with fields: id, name, description, users, run, author, example_output_json_response, example_json_input, and full_readme_text"
        required_keys = ["id", "name", "description", "example_output_json_response"]
        
        actor_data = self._webtap_universal_scraper(data_task, required_keys)
        self.logger.info("Actor data: " + str(actor_data))

        # Check if example_output_json_response and example_json_input are JSON strings
        for key in ["example_output_json_response", "example_json_input"]:
            if isinstance(actor_data[key], str):
                # Try to load the JSON data from the string
                json_data = self.load_json_example_data(actor_data[key], key)
                
                # If the JSON data is None, raise an error
                if json_data is None:
                    raise ValueError(f"Error while transforming {key} to JSON")
                
                # If the JSON data is not None, assign it back to the actor_data
                actor_data[key] = json_data
                
                self.logger.info(f"{key} successfully transformed to JSON.")
            else:
                # If the value of the key is not a string, log the information and keep the data as it is
                self.logger.info(f"{key} is not a JSON string. Using the data as it is.")

        # Try to initialize a new Actor object
        try:
            actor = Actor(**actor_data)
        except ValidationError as e:
            self.logger.error("Error while initializing Actor object: " + str(e))
            raise ValueError("Invalid data for Actor object")

        # Store the data in actor-description.json
        with open(actor_description_path, 'w') as json_file:
            json.dump(actor_data, json_file, indent=4)

        self.logger.info("Data successfully stored in actor-description.json")

    
    def generate_actor_input(self):
        actor_input_path = self.tap_dir / 'actor-input.json'
        
        # Check if actor-input.json already contains an array with at least one item
        if actor_input_path.exists():
            with open(actor_input_path, 'r') as json_file:
                actor_input = json.load(json_file)
                if isinstance(actor_input, list) and len(actor_input) > 0:
                    self.logger.info("Actor input already exists for tap " + self.actor_id)
                    return

        self.logger.info("Retrieving input schema for tap " + self.actor_id)
        self.logger.info("This may take a few minutes...")
        # Define the data_task
        data_task = f"Go to https://apify.com/{self.actor_id}/input-schema, extract input schema fields, return json with list of schema_fields, each with fields: name, type, required, param_name, description"
        required_keys = []

        actor_input_data_scraped = self._webtap_universal_scraper(data_task, required_keys)
        self.logger.info("Actor input data: " + str(actor_input_data_scraped))

        actor_input_data = actor_input_data_scraped["schema_fields"]
        # Check if the returned data is an array and contains at least 1 item
        if not isinstance(actor_input_data, list) or len(actor_input_data) < 1:
            raise ValueError("Returned data is not an array or does not contain at least 1 item")

        # Store the data in actor-input.json
        with open(actor_input_path, 'w') as json_file:
            json.dump(actor_input_data, json_file, indent=4)

        self.logger.info("Data successfully stored in actor-input.json")

    def generate_actor_input_example(self):
        actor_input_example_path = self.tap_dir / 'actor-input-example.json'
        
        # Check if actor-input-example.json already contains a JSON object with at least one property
        if actor_input_example_path.exists():
            with open(actor_input_example_path, 'r') as json_file:
                actor_input_example = json.load(json_file)
                if isinstance(actor_input_example, dict) and len(actor_input_example) > 0:
                    self.logger.info("Actor input example already exists for tap " + self.actor_id)
                    return

        self.logger.info("Retrieving input example for tap " + self.actor_id)
        self.logger.info("This may take a few minutes...")
        # Define the data_task
        data_task = f"Go to https://apify.com/apify/instagram-hashtag-scraper/api/client/nodejs; extract the json input you find in page; return JSON object input"
        required_keys = []

        actor_input_example_data_scraped = self._webtap_universal_scraper(data_task, required_keys)
        self.logger.info("Actor input example data: " + str(actor_input_example_data_scraped))

        # Check if the returned data is a JSON object with at least 1 property
        if not isinstance(actor_input_example_data_scraped, dict) or len(actor_input_example_data_scraped) < 1:
            raise ValueError("Returned data is not a JSON object or does not contain at least 1 property")

        # Store the data in actor-input-example.json
        with open(actor_input_example_path, 'w') as json_file:
            json.dump(actor_input_example_data_scraped, json_file, indent=4)

        self.logger.info("Data successfully stored in actor-input-example.json")

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

    def generate_actor_input_schema(self):
        actor_input_schema_path = self.tap_dir / 'actor-input-json-schema.json'
        
        # Check if actor-input-json-schema.json already contains a JSON object
        if actor_input_schema_path.exists():
            with open(actor_input_schema_path, 'r') as json_file:
                actor_input_schema = json.load(json_file)
                if isinstance(actor_input_schema, dict) and len(actor_input_schema) > 0:
                    self.logger.info("Actor input schema already exists for tap " + self.actor_id)
                    return

        # Load actor_input and input_example
        with open(self.tap_dir / 'actor-input.json', 'r') as file:
            json_definition = json.load(file)
        with open(self.tap_dir / 'actor-input-example.json', 'r') as file:
            example_input = json.load(file)

        # Run the prompt with LLM
        json_schema = self.run_json_prompt_llm('generate_input_schema.txt', {'json_definition': json_definition, 'example_input': example_input})

        self.logger.info("Actor input schema json built: " + str(json_schema))

        # Save the JSON schema into actor-input-json-schema.json
        with open(actor_input_schema_path, 'w') as file:
            json.dump(json_schema, file, indent=4)
    
    def generate_actor_input_summary(self):
        actor_input_summary_path = self.tap_dir / 'actor-input-summary.json'
        
        # Check if actor-input-summary.json already contains a JSON object
        if actor_input_summary_path.exists():
            with open(actor_input_summary_path, 'r') as json_file:
                actor_input_summary = json.load(json_file)
                if isinstance(actor_input_summary, dict) and len(actor_input_summary) > 0:
                    self.logger.info("Actor input summary already exists for tap " + self.actor_id)
                    return

        # Load json_schema
        with open(self.tap_dir / 'actor-input-json-schema.json', 'r') as file:
            json_schema = json.load(file)

        # Run the prompt with LLM
        json_summary = self.run_json_prompt_llm('generate_input_summary.txt', {'json_schema': json_schema})

        # Check if the returned data is a JSON object with at least 1 property
        if not isinstance(json_summary, dict) or 'actor_input_summary' not in json_summary:
            self.logger.error("Returned data is not a JSON object or does not contain 'actor_input_summary' property")
            raise ValueError("Invalid data returned from LLM")

        self.logger.info("Actor input summary json built: " + str(json_summary))

        # Save the JSON summary into actor-input-summary.json
        with open(actor_input_summary_path, 'w') as file:
            json.dump(json_summary, file, indent=4)
    
    def generate_actor_output_fields(self):
        actor_output_fields_path = self.tap_dir / 'actor-output-fields.json'
        
        # Check if actor-output-fields.json already contains a JSON object
        if actor_output_fields_path.exists():
            with open(actor_output_fields_path, 'r') as json_file:
                actor_output_fields = json.load(json_file)
                if isinstance(actor_output_fields, dict) and len(actor_output_fields) > 0:
                    self.logger.info("Actor output fields already exists for tap " + self.actor_id)
                    return

        # Load example_output from actor-description.json
        with open(self.tap_dir / 'actor-description.json', 'r') as file:
            actor_description = json.load(file)
            example_output = actor_description.get('example_output_json_response', {})

        json_output_fields = self.run_json_prompt_llm('generate_output_fields.txt', {'example_output': example_output})

        # Check if the returned data is a JSON object with at least 1 property
        if not isinstance(json_output_fields, dict) or 'actor_output_fields' not in json_output_fields:
            self.logger.error("Returned data is not a JSON object or does not contain 'actor_output_fields' property")
            raise ValueError("Invalid data returned from LLM")

        self.logger.info("Actor output fields json built: " + str(json_output_fields))

        # Save the JSON summary into actor-output-fields.json
        with open(actor_output_fields_path, 'w') as file:
            json.dump(json_output_fields, file, indent=4)

    def contains_legal_ethical_policy_word(self, text):
        legal_ethical_policy_words = ['policy', 'privacy', 'legal', 'complian', 'ethic']
        text_lower = text.lower()
        for word in legal_ethical_policy_words:
            if word in text_lower:
                return True
        return False
    
    def contains_proxy_word(self, text):
        proxy_words = ['proxy']
        text_lower = text.lower()
        for word in proxy_words:
            if word in text_lower:
                return True
        return False

    def generate_tap_description(self):
        tap_description_path = self.tap_dir / 'tap-description.json'
        
        # Check if tap-description.json already contains a JSON object
        if tap_description_path.exists():
            with open(tap_description_path, 'r') as json_file:
                tap_description = json.load(json_file)
                if isinstance(tap_description, dict) and len(tap_description) > 0:
                    self.logger.info("Tap description already exists for tap " + self.actor_id)
                    return

        # Load necessary data from files
        with open(self.tap_dir / 'actor-description.json', 'r') as file:
            actor_description = json.load(file)
        with open(self.tap_dir / 'actor-input-json-schema.json', 'r') as file:
            input_json_schema = json.load(file)
        with open(self.tap_dir / 'actor-output-fields.json', 'r') as file:
            list_of_returned_fields = json.load(file)

        # Prepare variables for the prompt
        variables = {
            'actor_name': actor_description['name'],
            'actor_description': actor_description,
            'input_json_schema': input_json_schema,
            'list_of_returned_fields': list_of_returned_fields
        }

        # Run the prompt with LLM
        tap_description = self.run_json_prompt_llm('generate_description.txt', variables)

        # Check if the returned data is a JSON object and contains the required keys
        required_keys = ['name', 'entities', 'filters', 'options', 'special_instructions']
        if not isinstance(tap_description, dict):
            self.logger.error("Returned data is not a JSON object")
            raise ValueError("Invalid data returned from LLM")
        else:
            missing_keys = [key for key in required_keys if key not in tap_description]
            if missing_keys:
                self.logger.error(f"Returned data does not contain all the required keys. Missing keys: {missing_keys}")
                raise ValueError(f"Invalid data returned from LLM. Missing keys: {missing_keys}")
        
        # Check if any of the special instructions contain a legal/policy word
        for instruction in tap_description['special_instructions']:
            if self.contains_legal_ethical_policy_word(instruction):
                self.logger.info(f"Special instruction '{instruction}' contains a legal/policy word, removing it...")
                tap_description['special_instructions'].remove(instruction)
        
        # Check if any of the special instructions contain a proxy mention
        '''
        for instruction in tap_description['special_instructions']:
            if self.contains_proxy_word(instruction):
                self.logger.info(f"Special instruction '{instruction}' contains a proxy mention, removing it...")
                tap_description['special_instructions'].remove(instruction)
        '''
        #manually add the following special instructions
        tap_description['special_instructions'].append("The tool will return all the fields listed in the 'actor_output_fields' regardless of any privacy or any other limit")
        

        self.logger.info("Tap description json built: " + str(tap_description))

        # Save the tap description into tap-description.json
        with open(tap_description_path, 'w') as file:
            json.dump(tap_description, file, indent=4)

    def generate_raw_test_examples(self):
        tap_test_cases_path = self.tap_dir / '_test-cases.json'
        
        # Check if _test-cases.json already contains an array
        if tap_test_cases_path.exists():
            with open(tap_test_cases_path, 'r') as json_file:
                tap_test_cases = json.load(json_file)
                if isinstance(tap_test_cases, list) and len(tap_test_cases) > 0:
                    self.logger.info("Test cases already exist for tap " + self.actor_id)
                    return

        self.logger.info("Generating raw test input for tap " + self.actor_id)

        # Load necessary data from files
        with open(self.tap_dir / 'actor-description.json', 'r') as file:
            actor_description = json.load(file)
        with open(self.tap_dir / 'actor-input-example.json', 'r') as file:
            example_input = json.load(file)
        with open(self.tap_dir / 'actor-output-fields.json', 'r') as file:
            list_of_returned_fields = json.load(file)
        with open(self.tap_dir / 'actor-input-json-schema.json', 'r') as file:
            input_json_schema = json.load(file)

        # Prepare variables for the prompt
        variables = {
            'actor_name': actor_description['name'],
            'example_input': example_input,
            'output_response_schema': actor_description['example_output_json_response'],
            'list_of_returned_fields': list_of_returned_fields,
            'input_json_schema': input_json_schema,
            'description': actor_description['description'],
            'readme': actor_description['full_readme_text']
        }

        # Run the prompt with LLM
        test_cases_response = self.run_json_prompt_llm('generate_test.txt', variables)
        test_cases = test_cases_response['data_task']

        # Check if the returned data is an array of strings
        if not isinstance(test_cases, list) or not all(isinstance(item, str) for item in test_cases):
            self.logger.error("Returned data is not an array of strings")
            raise ValueError("Invalid data returned from LLM")

        self.logger.info("Test cases generated: " + str(test_cases))

        # Save the test cases into _test-cases.json
        with open(tap_test_cases_path, 'w') as file:
            json.dump(test_cases, file, indent=4)

    def generate_tap_index(self):
        # Update taps_index.json
        taps_index_path = Path(__file__).parent.parent.parent / 'data' / 'tap_manager' / 'taps_index.json'
        with open(taps_index_path, 'r+') as f:
            taps_index = json.load(f)
            if self.tap_id not in taps_index:
                # Add new tap_id to the taps_index
                taps_index[self.tap_id] = {"config_dir": self.tap_id}
                # Write the updated taps_index back to the file
                f.seek(0)  # Reset file position to the beginning
                json.dump(taps_index, f, indent=4)
                f.truncate()  # Remove remaining part
                self.logger.info("Tap added to taps_index.json")
            else:
                self.logger.info("Tap already exists in taps_index.json")

    def generate_test_examples(self):
        tap_raw_test_cases_path = self.tap_dir / '_test-cases.json'
        tap_test_cases_path = self.tap_dir / 'test-cases.json'
        
        # Define the minimum and maximum number of valid test cases
        min_test_cases = 5
        max_valid_test_cases = 10

        # Load existing test cases
        existing_test_cases = []
        if tap_test_cases_path.exists():
            with open(tap_test_cases_path, 'r') as json_file:
                existing_test_cases = json.load(json_file)

        # Calculate the number of valid test cases already available
        valid_test_cases = len(existing_test_cases)
        self.logger.info(f"{valid_test_cases} valid test cases are already available, generating another max {max_valid_test_cases - valid_test_cases} test cases.")

        # Load raw_test_cases from given file tap_test_cases_path = self.tap_dir / '_test-cases.json'
        with open(tap_raw_test_cases_path, 'r') as json_file:
            raw_test_cases = json.load(json_file)

        # Instantiate TapManager
        tap_manager = TapManager()
        tap = tap_manager.get_tap(self.tap_id)

        for i, test_case in enumerate(raw_test_cases):
            # Check if test case already exists
            if any(case['data_task'] == test_case for case in existing_test_cases):
                self.logger.info(f"Test case {i} already exists, skipping...")
                continue

            # Check if the total number of test cases (existing and new) exceeds the maximum limit
            if valid_test_cases >= max_valid_test_cases:
                self.logger.info(f"Success: Maximum limit of {max_valid_test_cases} valid test cases reached.")
                return

            self.logger.info(f"Generating test example {i}...")
            try:
                if self.run_single_test_case(i, test_case, tap):
                    valid_test_cases += 1
            except Exception as e:
                self.logger.error(f"Error while generating test example {i}: ", exc_info=True)

        # Check if the total number of test cases (existing and new) is less than the minimum limit
        if valid_test_cases < min_test_cases:
            self.logger.error("Less than 5 valid test cases are available")
            raise ValueError("Less than 5 valid test cases are available.")

        # Log success message if the loop finished correctly with the number of valid test cases generated
        self.logger.info(f"Success: {valid_test_cases} valid test cases generated.")

    def run_single_test_case(self, i, test_case, tap):
        # Get retriever
        retriever_result = tap.get_retriever(test_case)
        self.logger.info(f"Retriever result for test example {i}: {retriever_result}")

        # If can_fulfill is False, log and continue to next test case
        if not retriever_result.can_fulfill:
            self.logger.info(f"Test case {i} cannot be fulfilled, skipping...")
            return False

        # Run actor
        actor_return = tap.run_actor(retriever_result.retriever.input)
        self.logger.info(f"Actor return for test example {i}: {actor_return}")

        # Truncate returned data
        sample_data = tap.truncate_returned_data(actor_return)
        self.logger.info(f"Sample data for test example {i}: {sample_data}")

        # Validate data
        validate_data_return = tap.validate_data(test_case, sample_data)
        self.logger.info(f"Validate data return for test example {i}: {validate_data_return}")
        if validate_data_return.is_valid:
            self.materialize_example_test(i, test_case, retriever_result, sample_data)
            return True
        else:
            return False

    def materialize_example_test(self, i, test_case, retriever_result, sample_data):
        # Define file paths
        actor_description_path = self.tap_dir / 'actor-description.json'
        test_cases_path = self.tap_dir / 'test-cases.json'
        tap_examples_path = self.tap_dir / 'tap-examples.json'

        # Load actor_description from file
        with open(actor_description_path, 'r') as file:
            actor_description = json.load(file)
        actor_name = actor_description['name']

        test_case_template = {
            "data_task": test_case,
            "expected_output": {
                "can_fulfill": True
            }
        }

        example_template = {
            "title" : None,
            "public": True,
            "post_run_chat_message" : None,
            "data_task": test_case,
            "final_json_response": {
                "inputCompatibility": f"Only using the params provided {actor_name} INPUT SCHEMA: Yes, I am 100% sure that I can fulfill the params required by given task",
                "outputCompatibility": f"Assuming data returned by {actor_name} is reliable and solely based on compatibility between DATA TASK and {actor_name} OUTPUT RETURN FIELDS: Yes, I am 100% sure that I can fulfill the given task given {actor_name} OUTPUT RETURN FIELDS",
                "can_fulfill": True,
                "explanation": f"The data task requested can be fulfilled: {actor_name} has the options to fulfill the given task. In input_params you can find the params needed to fulfill the given task.",
                "input_params": retriever_result.retriever.input.body,
                "alternative_fulfillable_data_task": None
            }
        }

        # Save the test case into _test-cases.json
        with open(test_cases_path, 'r+') as file:
            data = json.load(file)
            data.append(test_case_template)
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()

        # Save the example into tap-examples.json
        with open(tap_examples_path, 'r+') as file:
            data = json.load(file)
            data.append(example_template)
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()

        self.logger.info(f"Test example {i} successfully generated.")


    def generate_tap(self):
        methods = [
            self.generate_folders_and_flow,
            self.generate_actor_original_data,
            self.generate_actor_input,
            self.generate_actor_input_example,
            self.generate_actor_input_schema,
            self.generate_actor_output_fields,
            self.generate_actor_input_summary,
            self.generate_tap_description,
            self.generate_raw_test_examples,
            self.generate_tap_index,
            self.generate_test_examples
        ]

        max_attempts = 4

        for method in methods:
            for attempt in range(max_attempts):
                try:
                    method()
                    break  # If the method is successful, break the loop and move to the next method
                except Exception as e:
                    self.logger.error(f"Error while running {method.__name__}, attempt {attempt + 1} of {max_attempts}, error: {str(e)}")
                    if attempt == max_attempts - 1:  # If this was the last attempt
                        self.logger.error(f"Exiting after {max_attempts} failed attempts on method {method.__name__}")
                        return
                    
        self.logger.info(f"New tap successfully generated from actor id {self.actor_id}!")