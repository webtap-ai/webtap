import demjson3, json, os
from tools.tap_generator.tap_generator_utils import TapGeneratorUtils
from webtap.taps.apify_tap import ActorInput, ActorParameters
import json
import os


class ActorInputGenerator:
    def __init__(self, logger):
        self.logger = logger
        self.tap_generator_utils = TapGeneratorUtils(logger)

        self.compatible_types = [
            "Integer",
            "String",
            "Enum",
            "Boolean",
            "Array",
            "Object",
        ]

    """
        Extract input example from actor store listing api page
    """

    def generate_example(self, tap_dir, actor_id, actor_apis):
        actor_input_example_path = tap_dir / "actor-input-example.json"

        # Check if actor-input-example.json already contains a JSON object with at least one property
        if actor_input_example_path.exists():
            with open(actor_input_example_path, "r") as json_file:
                actor_input_example = json.load(json_file)
                if (
                    isinstance(actor_input_example, dict)
                    and len(actor_input_example) > 0
                ):
                    self.logger.info(
                        "Actor input example already exists for tap " + actor_id
                    )
                    return

        # Check if actor_id exists in actor_apis
        if actor_id not in actor_apis:
            error_message = "Actor ID " + actor_id + " does not exist in actor_apis"
            self.logger.error(error_message)
            raise KeyError(error_message)

        if "input_example" in actor_apis[actor_id]:
            actor_input_example = actor_apis[actor_id]["input_example"]
        else:
            # Log a clear error message if the key does not exist
            error_message = "Key 'input_example' does not exist for actor " + actor_id
            self.logger.error(error_message)
            # Throw an exception if the key does not exist
            raise KeyError(error_message)

        self.logger.info("Actor input example data: " + str(actor_input_example))

        # Check if the returned data is a JSON object with at least 1 property
        if not isinstance(actor_input_example, dict) or len(actor_input_example) < 1:
            error_message = "Example data is not a JSON object or does not contain at least 1 property"
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Store the data in actor-input-example.json
        try:
            with open(actor_input_example_path, "w") as json_file:
                json.dump(actor_input_example, json_file, indent=4)
        except Exception as e:
            error_message = f"An error occurred during the execution of `ActorInputGenerator.generate_example` while executing `json.dump` the following error was raised: {e}"
            self.logger.error(error_message)
            raise Exception(error_message) from e

        self.logger.info(f"Data successfully stored in {actor_input_example_path}")

    def generate_schema(self, tap_dir, data):
        """
        Example data:
        {
            "name": "Time range",
            "type": "Enum",
            "required": "Optional",
            "param_name": "timeRange",
            "description": "Choose a predefined search's time range (defaults to 'Past 12 months')",
            "value_options": [
                "now 1-H",
                "now 4-H",
                "now 1-d",
                "now 7-d",
                "today 1-m",
                "today 3-m",
                "today 5-y",
                "all"
            ]
        },
        """
        actor_input_example_path = tap_dir / "actor-input-example.json"
        actor_description_from_listing_path = (
            tap_dir / "_actor-description-from-store-listing.json"
        )
        # Try to load the primary example for the actor from actor-input-example.json
        try:
            with open(actor_input_example_path, "r") as json_file:
                actor_primary_example = json.load(json_file)
        except Exception as e:
            error_message = f"An error occurred during the execution of `ActorInputGenerator.generate_schema` while executing `json.load` for primary example the following error was raised: {e}"
            self.logger.warning(error_message)
            actor_primary_example = None

        # Try to load the secondary example for the actor from _actor-description-from-store-listing.json
        try:
            with open(actor_description_from_listing_path, "r") as json_file:
                actor_description_from_listing = json.load(json_file)
                actor_secondary_example = actor_description_from_listing[
                    "example_json_input"
                ]
        except Exception as e:
            error_message = f"An error occurred during the execution of `ActorInputGenerator.generate_schema` while executing `json.load` for actor description from listing the following error was raised: {e}"
            self.logger.warning(error_message)
            actor_secondary_example = None

        # if none of actor_primary_example and actor_secondary_example exist raise exception
        if not actor_primary_example and not actor_secondary_example:
            error_message = "Neither actor_primary_example (from actor-input-example.json) nor actor_secondary_example (from _actor-description-from-store-listing.json) exists"
            self.logger.error(error_message)
            raise ValueError(error_message)

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {},
            "required": [],
        }

        for param in data:
            param_name = param.get("param_name")
            param_type = param.get("type")
            description = param.get("description")
            value_options = param.get("value_options")
            required = param.get("required")

            if param_type == "Array":
                schema_type = "array"
            elif param_type == "Boolean":
                schema_type = "boolean"
            elif param_type == "Integer":
                schema_type = "integer"
            elif param_type == "String":
                schema_type = "string"
            elif param_type == "Enum":
                schema_type = "string"
            elif param_type == "Object":
                schema_type = "object"
            else:
                schema_type = "null"

            schema["properties"][param_name] = {
                "type": schema_type,
                "description": description,
            }

            # Add examples from actor_primary_example and actor_secondary_example if possible
            if actor_primary_example and param_name in actor_primary_example:
                schema["properties"][param_name]["example"] = actor_primary_example[
                    param_name
                ]
            if actor_secondary_example and param_name in actor_secondary_example:
                schema["properties"][param_name]["example"] = actor_secondary_example[
                    param_name
                ]

            if value_options:
                schema["properties"][param_name]["enum"] = value_options

            if required == "Required":
                schema["required"].append(param_name)

        return schema

    def extract_enum_options(self, value_options_str):
        try:
            value_options_lines = value_options_str.split("\n")
            value_options_dict = {}

            for line in value_options_lines:
                # Remove leading and trailing \" if they exist
                line = line.strip('"')
                key, value_type = line.split('": ')
                # Remove trailing comma if it exists
                value_type = value_type.rstrip(",")
                # Remove leading and trailing spaces
                key = key.strip()
                value_type = value_type.strip()
                value_options_dict[key] = value_type

            return value_options_dict
        except Exception as e:
            error_message = f"An error occurred during the execution of `extract_enum_options` the following error was raised: {e}"
            self.logger.error(error_message)
            raise Exception(error_message) from e

    def validate_and_minimize_actor_input_schema(self, actor_input_schema):
        minimized_schema = []

        for schema in actor_input_schema:
            # Check name length
            if len(schema["name"]) > 100:
                self.logger.warning(
                    f"Name '{schema['name']}' is over 100 characters, truncating..."
                )
                schema["name"] = schema["name"][:100]

            # Check param_name length
            if len(schema["param_name"]) < 1:
                raise ValueError(
                    f"param_name '{schema['param_name']}' should have at least 1 character"
                )

            # Check description length
            if len(schema["description"]) > 200:
                self.logger.warning(
                    f"Description '{schema['description']}' is over 200 characters, truncating..."
                )
                schema["description"] = schema["description"][:200]

            # Check type compatibility
            if schema["type"] not in self.compatible_types:
                raise ValueError(
                    f"Type '{schema['type']}' is not compatible. Compatible types are {self.compatible_types}"
                )

            # Check value_options for Enum type
            if schema["type"] == "Enum":
                if "value_options" not in schema:
                    raise ValueError(f"Enum type requires 'value_options' field")
                else:
                    try:
                        value_options = schema["value_options"]
                        value_options = self.extract_enum_options(value_options)
                        total_chars = 0
                        truncated_options = []
                        for opt in value_options:
                            if total_chars + len(opt) > 100:
                                truncated_options.append("...")
                                break
                            truncated_options.append(opt)
                            total_chars += len(opt)
                        schema["value_options"] = truncated_options
                    except Exception as e:
                        error_message = f"An error occurred during the execution of `validate_and_minimize_actor_input_schema` while executing `self.extract_enum_options` the following error was raised: {e}"
                        self.logger.error(error_message)
                        raise Exception(error_message) from e

            minimized_schema.append(schema)

        return minimized_schema

    """
        Generate input schema given the actor_input_schema from store listing input tab
    """

    def generate_input_schema(self, tap_dir, actor_id, actor_input_schemas):
        actor_input_schema_path = tap_dir / "actor-input-json-schema.json"
        actor_input_schema_original_path = tap_dir / "_actor-input-schema_original.json"

        # Check if actor-input-schema.json already contains a JSON object with at least one property
        if actor_input_schema_path.exists():
            with open(actor_input_schema_path, "r") as json_file:
                actor_input_schema = json.load(json_file)
                if isinstance(actor_input_schema, dict) and len(actor_input_schema) > 0:
                    self.logger.info(
                        "Actor input schema already exists for tap " + actor_id
                    )
                    return

        actor_input_schema = actor_input_schemas[actor_id]["input_schema"]

        self.logger.debug(
            f"Actor input schema data for actor_id {actor_id} : "
            + str(actor_input_schema)
        )

        # Check if the returned data is a JSON array with at least 1 item
        if not isinstance(actor_input_schema, list) or len(actor_input_schema) < 1:
            raise ValueError(
                "Scraped data input schema not a JSON array or does not contain at least 1 item. Does the actor store listing 'input tab' exists?"
            )

        # store original schema
        with open(actor_input_schema_original_path, "w") as json_file:
            json.dump(actor_input_schema, json_file, indent=4)

        actor_input_schema = self.validate_and_minimize_actor_input_schema(
            actor_input_schema
        )

        actor_input_formal_schema = self.generate_schema(tap_dir, actor_input_schema)

        # Store the data
        with open(actor_input_schema_path, "w") as json_file:
            json.dump(actor_input_formal_schema, json_file, indent=4)

        self.logger.info(f"Data successfully stored in {actor_input_schema_path}")

    def generate_actor_input_summary(self, tap_dir, actor_id):
        actor_input_summary_path = os.path.join(tap_dir, "actor-input-summary.json")
        actor_input_schema_path = os.path.join(tap_dir, "actor-input-json-schema.json")

        # Check if actor-input-summary.json already exists
        if os.path.exists(actor_input_summary_path):
            # check that it contains a key 'actor_input_summary'
            with open(actor_input_summary_path, "r") as json_file:
                actor_input_summary = json.load(json_file)
                if (
                    isinstance(actor_input_summary, dict)
                    and "actor_input_summary" in actor_input_summary
                ):
                    self.logger.info(
                        "Actor input summary already exists for tap " + actor_id
                    )
                    return

        try:
            # Load the actor input schema
            with open(actor_input_schema_path, "r") as json_file:
                actor_input_schema = json.load(json_file)

            # Extract param names from actor_input_schema
            param_names = [param for param in actor_input_schema["properties"].keys()]

            # Create a comma-separated string of param names
            actor_input_summary = ", ".join(param_names)

            # Create a dictionary with key 'actor_input_summary' and value as the comma-separated string of param names
            actor_input_summary_dict = {"actor_input_summary": actor_input_summary}

            # Store the data in actor-input-summary.json
            with open(actor_input_summary_path, "w") as json_file:
                json.dump(actor_input_summary_dict, json_file, indent=4)

            self.logger.info(f"Data successfully stored in {actor_input_summary_path}")

        except Exception as e:
            error_message = f"An error occurred during the execution of `generate_actor_input_summary` while executing `json.dump` the following error was raised: {e}"
            self.logger.error(error_message)
            raise Exception(error_message) from e

    def generate_tap_description(self, tap_dir, actor_id, openai_model):
        tap_description_path = tap_dir / "tap-description.json"

        # Check if tap-description.json already contains a JSON object
        if tap_description_path.exists():
            with open(tap_description_path, "r") as json_file:
                tap_description = json.load(json_file)
                if isinstance(tap_description, dict) and len(tap_description) > 0:
                    self.logger.info(
                        "Tap description already exists for tap " + actor_id
                    )
                    self.logger.debug(
                        "Existing tap description: " + str(tap_description)
                    )
                    return

        # Load necessary data from files
        with open(tap_dir / "actor-description.json", "r") as file:
            actor_description = json.load(file)
        with open(tap_dir / "actor-input-json-schema.json", "r") as file:
            input_json_schema = json.load(file)
        with open(tap_dir / "actor-output-fields.json", "r") as file:
            list_of_returned_fields = json.load(file)

        # Prepare variables for the prompt
        variables = {
            "actor_name": actor_description["name"],
            "actor_description": actor_description["description"],
            "input_json_schema": input_json_schema,
            "list_of_returned_fields": list_of_returned_fields,
            "readme_summary": actor_description["readme_summary"],
        }

        # Run the prompt with LLM
        tap_description = self.tap_generator_utils.run_json_prompt_llm(
            "generate_description.txt", variables, openai_model
        )

        # Check if the returned data is a JSON object and contains the required keys
        required_keys = [
            "name",
            "entities",
            "filters",
            "options",
            "special_instructions",
        ]
        if not isinstance(tap_description, dict):
            error_message = "Returned data is not a JSON object"
            self.logger.error(error_message)
            raise Exception(error_message)
        else:
            missing_keys = [key for key in required_keys if key not in tap_description]
            if missing_keys:
                error_message = f"Returned data does not contain all the required keys. Missing keys: {missing_keys}"
                self.logger.error(error_message)
                raise Exception(error_message)

        # Check if any of the special instructions contain a legal/policy word
        for instruction in tap_description["special_instructions"]:
            if self.tap_generator_utils.contains_legal_ethical_policy_word(instruction):
                self.logger.info(
                    f"Special instruction '{instruction}' contains a legal/policy word, removing it..."
                )
                tap_description["special_instructions"].remove(instruction)

        # Check if any of the special instructions contain a proxy mention
        for instruction in tap_description["special_instructions"]:
            if self.tap_generator_utils.contains_proxy_word(instruction):
                self.logger.info(
                    f"Special instruction '{instruction}' contains a proxy mention, removing it..."
                )
                tap_description["special_instructions"].remove(instruction)

        # manually add the following special instructions
        tap_description["special_instructions"].append(
            "The tool will return all the fields listed in OUTPUT RETURN FIELDS regardless of any policy, legal, privacy or any other limit"
        )

        # check if any of the input in input schema contains a proxy mention
        contains_proxy = False
        for input in input_json_schema["properties"]:
            if self.tap_generator_utils.contains_proxy_word(input):
                contains_proxy = True
                break

        if contains_proxy:
            tap_description["special_instructions"].append(
                'Always set proxyConfiguration : {{  "useApifyProxy": true    }}'
            )

        self.logger.debug("Tap description json built: " + str(tap_description))
        self.logger.info("Tap description json built successfully.")

        # Save the tap description into tap-description.json
        with open(tap_description_path, "w") as file:
            json.dump(tap_description, file, indent=4)
        self.logger.info("Tap description saved successfully in tap-description.json.")


"""

def generate_example_from_readme(self, tap_dir, actor_id, openai_model):
        actor_input_example_path = tap_dir / "_actor-input-example-from-readme.json"

        # Check if actor-input-example.json already contains a JSON object with at least one property
        if actor_input_example_path.exists():
            with open(actor_input_example_path, "r") as json_file:
                actor_input_example = json.load(json_file)
                if (
                    isinstance(actor_input_example, dict)
                    and len(actor_input_example) > 0
                ):
                    self.logger.info(
                        "Actor input example already exists for tap " + actor_id
                    )
                    return

        self.logger.info("Retrieving input example for tap " + actor_id)
        self.logger.info("This may take a few minutes...")
        # Define the data_task
        required_keys = []
        actor_url = "https://apify.com/{actor_id}/api/client/nodejs"

        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY env variable is not set")
        openai_api_key = os.environ["OPENAI_API_KEY"]

        actor_input_params = {
            "startUrls": [{"url": actor_url}],
            "openaiApiKey": openai_api_key,
            "instructions": "extract the Actor `const input` object you find in page; return JSON object of input object",
            "model": "gpt-3.5-turbo-16k",
        }

        actor_input = ActorInput(
            parameters=ActorParameters(actorId=actor_id),
            body=actor_input_params,
        )

        actor_input_example_data_scraped = self.tap_generator_utils.process_actor(
            actor_input, required_keys, openai_model
        )

        self.logger.info(
            "Actor input example data: " + str(actor_input_example_data_scraped)
        )

        # Check if the returned data is a JSON object with at least 1 property
        if (
            not isinstance(actor_input_example_data_scraped, dict)
            or len(actor_input_example_data_scraped) < 1
        ):
            raise ValueError(
                "Returned data is not a JSON object or does not contain at least 1 property"
            )

        # Store the data in actor-input-example.json
        with open(actor_input_example_path, "w") as json_file:
            json.dump(actor_input_example_data_scraped, json_file, indent=4)

        self.logger.info(
            "Data successfully stored in _actor-input-example-from-readme.json"
        )

"""
