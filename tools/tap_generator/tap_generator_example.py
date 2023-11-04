import demjson3, json, os
from tools.tap_generator.tap_generator_utils import TapGeneratorUtils
from webtap.tap_manager import TapManager
import json
import os


class TapGeneratorExample:
    def __init__(self, logger):
        self.logger = logger
        self.tap_generator_utils = TapGeneratorUtils(logger)
        self.MIN_TEST_CASES = 3
        self.MAX_VALID_TEST_CASES = 10

    """

    Using LLM to generate raw test cases

    """

    def generate_raw_test_examples(self, tap_dir, actor_id, openai_model):
        tap_test_cases_path = tap_dir / "_test-cases.json"

        # In this case we need every time to generate the raw test cases from scratch
        self.logger.info("Generating raw test input for tap " + actor_id)

        # Load necessary data from files
        with open(tap_dir / "actor-description.json", "r") as file:
            actor_description = json.load(file)
        with open(tap_dir / "actor-input-example.json", "r") as file:
            example_input = json.load(file)
        with open(tap_dir / "actor-output-fields.json", "r") as file:
            list_of_returned_fields = json.load(file)
        with open(tap_dir / "actor-input-json-schema.json", "r") as file:
            input_json_schema = json.load(file)

        # Prepare variables for the prompt
        variables = {
            "actor_name": actor_description["name"],
            "example_input": example_input,
            "list_of_returned_fields": list_of_returned_fields,
            "input_json_schema": input_json_schema,
            "description": actor_description["description"],
            "readme": actor_description["readme_summary"],
        }

        # Run the prompt with LLM
        try:
            test_cases_response = self.tap_generator_utils.run_json_prompt_llm(
                "generate_test.txt", variables, openai_model
            )
        except Exception as e:
            error_message = f"""An error occurred during the execution of `TapGeneratorExample.generate_raw_test_examples` while executing `self.tap_generator_utils.run_json_prompt_llm` the following error was raised: {e}"""
            self.logger.error(error_message)
            raise Exception(error_message) from e

        test_cases = test_cases_response["data_task"]

        # Check if the returned data is an array of strings
        if not isinstance(test_cases, list) or not all(
            isinstance(item, str) for item in test_cases
        ):
            error_message = "Returned data is not an array of strings"
            self.logger.error(error_message)
            raise ValueError(error_message)

        self.logger.debug("Test cases generated: " + str(test_cases))
        self.logger.info("Test cases generated successfully.")

        # Save the test cases into _test-cases.json
        with open(tap_test_cases_path, "w") as file:
            json.dump(test_cases, file, indent=4)
        self.logger.debug("Test cases saved in _test-cases.json.")

    """
    
    Ran the single raw test cases and generate valid examples/test cases
    """

    def generate_test_examples(self, tap_dir, tap_id, openai_model):
        tap_raw_test_cases_path = tap_dir / "_test-cases.json"
        tap_test_cases_path = tap_dir / "test-cases.json"

        min_test_cases = self.MIN_TEST_CASES
        max_valid_test_cases = self.MAX_VALID_TEST_CASES

        # Load existing test cases
        existing_test_cases = []
        if tap_test_cases_path.exists():
            with open(tap_test_cases_path, "r") as json_file:
                existing_test_cases = json.load(json_file)

        # Calculate the number of valid test cases already available
        valid_test_cases = len(existing_test_cases)

        if valid_test_cases < min_test_cases:
            self.logger.info(
                f"{valid_test_cases} valid test cases are already available, generating another max {max_valid_test_cases - valid_test_cases} test cases."
            )
        else:
            self.logger.info(
                f"Success: {valid_test_cases} valid test cases are already available."
            )
            return

        # generate raw test cases
        self.generate_raw_test_examples(tap_dir, tap_id, openai_model)

        # Load raw_test_cases from given file tap_test_cases_path = tap_dir / '_test-cases.json'
        with open(tap_raw_test_cases_path, "r") as json_file:
            raw_test_cases = json.load(json_file)

        # Instantiate TapManager
        tap_manager = TapManager()
        tap = tap_manager.get_tap(tap_id)

        for i, test_case in enumerate(raw_test_cases):
            # Check if test case already exists
            if any(case["data_task"] == test_case for case in existing_test_cases):
                self.logger.info(f"Test case {i} exists.")
                self.logger.debug(f"Test case {i} already exists, skipping...")
                continue

            # Check if the total number of test cases (existing and new) exceeds the maximum limit
            if valid_test_cases >= max_valid_test_cases:
                self.logger.info(f"Max limit of valid test cases reached.")
                self.logger.debug(
                    f"Success: Maximum limit of {max_valid_test_cases} valid test cases reached."
                )
                return

            self.logger.info(f"Generating test example {i}...")
            try:
                if self.run_single_test_case(tap_dir, i, test_case, tap):
                    valid_test_cases += 1
            except Exception as e:
                error_message = f"An error occurred during the execution of `generate_test_examples` while executing `self.run_single_test_case` the following error was raised: {e}"
                self.logger.warning(error_message)
                self.logger.debug(
                    f"Error while generating test example {i}: ", exc_info=True
                )

        # Check if the total number of test cases (existing and new) is less than the minimum limit
        if valid_test_cases < min_test_cases:
            error_message = "Less than min_test_cases valid test cases are available."
            self.logger.warning(error_message)
            raise ValueError(error_message)

        # Log success message if the loop finished correctly with the number of valid test cases generated
        self.logger.info(f"Valid test cases generated: {valid_test_cases}")
        self.logger.debug(f"Success: {valid_test_cases} valid test cases generated.")

    def run_single_test_case(self, tap_dir, i, test_case, tap):
        # Get retriever
        retriever_result = tap.get_retriever(test_case)
        self.logger.info(f"Retriever run ok for test example {i}.")
        self.logger.debug(f"Retriever result for test example {i}: {retriever_result}")

        # If can_fulfill is False, log and continue to next test case
        if not retriever_result.can_fulfill:
            self.logger.info(f"Test case {i} cannot be fulfilled.")
            self.logger.debug(f"Test case {i} cannot be fulfilled, skipping...")
            return False

        # Run actor
        actor_return = tap.run_actor(retriever_result.retriever.input)
        self.logger.info(f"Actor return for test example {i}.")
        self.logger.debug(f"Actor return for test example {i}: {actor_return}")

        # Truncate returned data
        sample_data = tap.truncate_returned_data(actor_return)
        self.logger.info(f"Sample data returned for test example {i}.")
        self.logger.debug(f"Sample data for test example {i}: {sample_data}")

        # Validate data
        validate_data_return = tap.validate_data(test_case, sample_data)
        self.logger.debug(
            f"Validate data return for test example {i}: {validate_data_return}"
        )
        if validate_data_return.is_valid:
            self.logger.info(f"Success: Test case {i} is valid.")
            self.materialize_example_test(
                tap_dir, i, test_case, retriever_result, sample_data
            )
            return True
        else:
            self.logger.info(f"Test case {i} is not valid.")
            return False

    def materialize_example_test(
        self, tap_dir, i, test_case, retriever_result, sample_data
    ):
        # Define file paths
        actor_description_path = tap_dir / "actor-description.json"
        test_cases_path = tap_dir / "test-cases.json"
        tap_examples_path = tap_dir / "tap-examples.json"

        # Load actor_description from file
        with open(actor_description_path, "r") as file:
            actor_description = json.load(file)
        actor_name = actor_description["name"]

        test_case_template = {
            "data_task": test_case,
            "expected_output": {"can_fulfill": True},
        }

        example_template = {
            "title": None,
            "public": True,
            "post_run_chat_message": None,
            "data_task": test_case,
            "final_json_response": {
                "inputCompatibility": f"Only using the params provided {actor_name} INPUT SCHEMA: Yes, I am 100% sure that I can fulfill the params required by given task",
                "outputCompatibility": f"Assuming data returned by {actor_name} is reliable and solely based on compatibility between DATA TASK and {actor_name} OUTPUT RETURN FIELDS: Yes, I am 100% sure that I can fulfill the given task given {actor_name} OUTPUT RETURN FIELDS",
                "can_fulfill": True,
                "explanation": f"The data task requested can be fulfilled: {actor_name} has the options to fulfill the given task. In input_params you can find the params needed to fulfill the given task.",
                "input_params": retriever_result.retriever.input.body,
                "alternative_fulfillable_data_task": None,
            },
        }

        # Save the test case into _test-cases.json
        with open(test_cases_path, "r+") as file:
            data = json.load(file)
            data.append(test_case_template)
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
        self.logger.debug(f"Test case {i} saved in _test-cases.json.")

        # Save the example into tap-examples.json
        with open(tap_examples_path, "r+") as file:
            data = json.load(file)
            data.append(example_template)
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
        self.logger.debug(f"Example {i} saved in tap-examples.json.")

        self.logger.info(f"Test example {i} successfully generated.")
