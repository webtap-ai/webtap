import logging, demjson3, json, csv, sys, re, os, json, openai
from pathlib import Path
from webtap.tap_manager import TapManager
from langchain.prompts import load_prompt
from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import ValidationError
from webtap.taps.apify_tap import Actor
from tools.tap_generator.tap_generator_utils import TapGeneratorUtils
from tools.tap_generator.actor_description_generator import ActorDescriptionGenerator
from tools.tap_generator.actor_input_generator import ActorInputGenerator
from tools.tap_generator.actor_test_run import ActorTestRun
from tools.tap_generator.tap_generator_example import TapGeneratorExample


class TapGenerator:
    def generate_tap_id(self, actor_id):
        # Replace any special characters with underscores
        actor_id_clean = re.sub(r"\W+", "_", actor_id)
        # Generate the directory name
        tap_id = f"atg_{actor_id_clean}"
        return tap_id

    def init_logging(self):
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # Set root logger to DEBUG level

        # Create a file handler for info level
        current_date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = (
            Path(__file__).parent.parent.parent
            / "logs"
            / self.tap_id
            / current_date_time
            / "atg"
        )
        log_dir.mkdir(parents=True, exist_ok=True)
        info_log_path = log_dir / "results.log"
        info_handler = logging.FileHandler(info_log_path)
        info_handler.setLevel(logging.INFO)  # Set handler to INFO level

        # Create a file handler for debug level
        debug_log_path = log_dir / "debug_trace.log"
        debug_handler = logging.FileHandler(debug_log_path)
        debug_handler.setLevel(logging.DEBUG)  # Set handler to DEBUG level

        # Create a logging format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        info_handler.setFormatter(formatter)
        debug_handler.setFormatter(formatter)

        # Create a stdout handler
        stdout_handler = logging.StreamHandler()
        # Set handler to INFO level if debug_mode is False, otherwise set to DEBUG level
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(formatter)

        # Add the handlers to the logger
        self.logger.addHandler(info_handler)
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(stdout_handler)

        # Add ANSI escape sequences for colored output
        logging.addLevelName(
            logging.DEBUG, "\033[1;34m%s\033[1;0m" % logging.getLevelName(logging.DEBUG)
        )
        logging.addLevelName(
            logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO)
        )
        logging.addLevelName(
            logging.WARNING,
            "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING),
        )
        logging.addLevelName(
            logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR)
        )
        logging.addLevelName(
            logging.CRITICAL,
            "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL),
        )

        # log info the log file created
        self.logger.info("Log file created: " + str(info_log_path))
        self.logger.info("Debug trace file created: " + str(debug_log_path))

        self.logger.info("TapGenerator initialized for tap " + self.actor_id)

    def load_apify_actor_data(self):
        # Load actor details from data / scraped_data / actor_details.json
        self.actor_details = self.tap_generator_utils.load_data_from_json(
            Path(__file__).parent.parent.parent
            / "data"
            / "tap_generator"
            / "apify_scraped_data"
            / "actor_details.json"
        )
        self.logger.info(
            "Loaded actor details for " + str(len(self.actor_details)) + " actors."
        )

        # Load actor input schemas from data / scraped_data / actor_input_schemas.json
        self.actor_input_schemas = self.tap_generator_utils.load_data_from_json(
            Path(__file__).parent.parent.parent
            / "data"
            / "tap_generator"
            / "apify_scraped_data"
            / "actor_input_schemas.json"
        )
        self.logger.info(
            "Loaded actor input schemas for "
            + str(len(self.actor_input_schemas))
            + " actors."
        )

        # Load actor APIs from data / scraped_data / actor_apis.json
        self.actor_apis = self.tap_generator_utils.load_data_from_json(
            Path(__file__).parent.parent.parent
            / "data"
            / "tap_generator"
            / "apify_scraped_data"
            / "actor_apis.json"
        )
        self.logger.info(
            "Loaded actor APIs for " + str(len(self.actor_apis)) + " actors."
        )

    def generate_folders_and_flow(self):
        # Create tap_dir if it doesn't exist
        self.tap_dir.mkdir(parents=True, exist_ok=True)

        # List of files to be created
        files = ["__init__.py"]

        # List of JSON files to be created with empty array
        json_files = ["_test-cases.json", "tap-examples.json", "test-cases.json"]

        # List of JSON files to be created with empty object
        json_object_files = [
            "actor-output-fields.json",
            "actor-description.json",
            "actor-input-example.json",
            "actor-input-json-schema.json",
            "actor-input-summary.json",
            "tap-description.json",
            "_actor-description-from-store-listing.json",
        ]

        created_files = []
        created_json_files = []
        created_json_object_files = []

        # Create each file in the list
        for file in files:
            file_path = self.tap_dir / file
            if not file_path.exists():
                # For these files, just create an empty file
                self.logger.debug("Creating file " + str(file_path))
                open(file_path, "a").close()
                created_files.append(str(file_path))

        # Create each JSON file in the list with an empty array
        for json_file in json_files:
            json_file_path = self.tap_dir / json_file
            if not json_file_path.exists():
                # For these JSON files, create an empty JSON array
                self.logger.debug("Creating json file " + str(json_file_path))
                with open(json_file_path, "w") as f:
                    json.dump([], f)
                created_json_files.append(str(json_file_path))

        # Create each JSON file in the list with an empty object
        for json_object_file in json_object_files:
            json_object_file_path = self.tap_dir / json_object_file
            if not json_object_file_path.exists():
                # For these JSON files, create an empty JSON object
                self.logger.debug(
                    "Creating json object file " + str(json_object_file_path)
                )
                with open(json_object_file_path, "w") as f:
                    json.dump({}, f)
                created_json_object_files.append(str(json_object_file_path))

        self.logger.debug("Created files: " + ", ".join(created_files))
        self.logger.debug(
            "Created json files with empty array: " + ", ".join(created_json_files)
        )
        self.logger.debug(
            "Created json object files with empty object: "
            + ", ".join(created_json_object_files)
        )

        self.logger.info(
            f"Folders and files generated for tap {self.actor_id}. Created {len(created_files)} files, {len(created_json_files)} json files, and {len(created_json_object_files)} json object files."
        )

    def __init__(self, actor_id):
        self.debug_mode = False
        self.actor_id = actor_id
        self.tap_id = self.generate_tap_id(actor_id)
        self.tap_dir = (
            Path(__file__).parent.parent.parent / "data" / "taps" / self.tap_id
        )
        self.openai_model = "gpt-4"

        # Load actor_results from a JSON file
        with open(
            Path("data") / "tap_generator" / "results" / "actor_results.json",
            "r",
        ) as f:
            self.actor_results = json.load(f)

        # Initialize logging
        self.init_logging()

        self.tap_generator_utils = TapGeneratorUtils(self.logger)

        self.load_apify_actor_data()

        self.generate_folders_and_flow()

    def generate_tap_index(self):
        # Update taps_index.json
        taps_index_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "tap_manager"
            / "taps_index.json"
        )
        with open(taps_index_path, "r+") as f:
            taps_index = json.load(f)
            if self.tap_id not in taps_index:
                # Add new tap_id to the taps_index
                taps_index[self.tap_id] = {"config_dir": self.tap_id}
                # Write the updated taps_index back to the file
                f.seek(0)  # Reset file position to the beginning
                json.dump(taps_index, f, indent=4)
                f.truncate()  # Remove remaining part
                self.logger.info("Tap added to taps_index.json")
                self.logger.debug(
                    f"Tap {self.tap_id} added to taps_index.json with config_dir: {self.tap_id}"
                )
            else:
                self.logger.info("Tap already exists in taps_index.json")
                self.logger.debug(
                    f"Tap {self.tap_id} already exists in taps_index.json"
                )

    def init_tap(self):
        try:
            # Generate tap index
            self.generate_tap_index()

            # Instantiate TapManager and initialize tap
            tap_manager = TapManager()
            tap = tap_manager.get_tap(self.tap_id)

            self.logger.info("Tap initialized successfully.")
            self.logger.debug(
                f"Tap {self.tap_id} initialized successfully with TapManager."
            )
            return tap
        except Exception as e:
            # If an exception is thrown, delete tap index and re-raise the exception
            self.tap_generator_utils.delete_tap_index(self.tap_id)
            self.logger.error(f"Error while initializing tap: {str(e)}")
            self.logger.debug(f"Error while initializing tap {self.tap_id}: {str(e)}")
            raise

    def generate_tap(self):
        # Instantiate single generator classes
        actor_input_generator = ActorInputGenerator(self.logger)
        actor_test_run = ActorTestRun(self.logger)
        actor_description_generator = ActorDescriptionGenerator(self.logger)
        tap_generator_example = TapGeneratorExample(self.logger)

        steps = [
            {
                # This step will generate a single input example, taking it from scrped data | some gpt-3.5 will be used ( ~10k gpt3.5 tokens * max 5 times)
                "step": actor_input_generator.generate_example,
                "params": (self.tap_dir, self.actor_id, self.actor_apis),
                "generated_files": ["actor-input-example.json"],
                "optional": False,
            },
            {
                # This step will generate a single input example, using `manual` universal scraper | some gpt-3.5 will be used ( ~30k gpt3.5 tokens * max 5 times )
                "step": actor_description_generator.generate_from_store_listing,
                "params": (
                    self.tap_dir,
                    self.actor_id,
                ),
                "generated_files": ["_actor-description-from-store-listing.json"],
                "optional": True,
            },
            {
                # This step will run a test with the inputs generated bt the previous steps; at least one test has to return some item in order to work | some apify cretdit will be used (max 2 runs)
                "step": actor_test_run.test_run,  # Call test_run method of ActorTestRun
                "params": (self.tap_dir, self.actor_id, self.actor_apis),
                "generated_files": ["_actor_example_run_output.json"],
                "optional": False,
            },
            # This step will generate an actor description from scraped data
            {
                "step": actor_description_generator.generate,
                "params": (self.tap_dir, self.actor_id, self.actor_details),
                "generated_files": ["actor-description.json"],
                "optional": False,
            },
            {
                # This step will generate an actor input schema from scraped data and the above examples
                "step": actor_input_generator.generate_input_schema,
                "params": (self.tap_dir, self.actor_id, self.actor_input_schemas),
                "generated_files": ["actor-input-json-schema.json"],
                "optional": False,
            },
            {
                # This step will generate an actor input summary using the above generated data
                "step": actor_input_generator.generate_actor_input_summary,
                "params": (self.tap_dir, self.actor_id),
                "generated_files": ["actor-input-summary.json"],
                "optional": False,
            },
            {
                # This step will generate the actor output fields using the above generated data | some gpt-4 will be used
                "step": actor_description_generator.generate_output_field_names,
                "params": (self.tap_dir, self.actor_id, self.openai_model),
                "generated_files": ["actor-output-fields.json"],
                "optional": False,
            },
            {
                # This step will generate the tap_description
                "step": actor_input_generator.generate_tap_description,
                "params": (self.tap_dir, self.actor_id, self.openai_model),
                "generated_files": ["tap-description.json"],
                "optional": False,
            },
            {
                # This step will finally init the tap
                "step": self.init_tap,
                "params": (),
                "generated_files": [],
                "optional": False,
            },
            {
                # This step will generate_test_examples
                "step": tap_generator_example.generate_test_examples,
                "params": (self.tap_dir, self.tap_id, self.openai_model),
                "generated_files": ["test-cases.json", "tap-examples.json"],
                "optional": False,
            },
        ]

        max_attempts = 4

        if self.debug_mode:
            max_attempts = 1

        count_steps = len(steps)
        i = 0

        for step_dict in steps:
            i += 1
            for attempt in range(max_attempts):
                try:
                    self.logger.info(
                        f"### Step {i}/{count_steps}: `{step_dict['step'].__self__.__class__.__name__}.{step_dict['step'].__self__.__class__.__name__}.{step_dict['step'].__name__}` - attempt number {attempt + 1}."
                    )
                    # Pass the necessary parameters to the step
                    step_dict["step"](*step_dict["params"])
                    self.logger.info(
                        f"SUCCESS: Step `{step_dict['step'].__self__.__class__.__name__}.{step_dict['step'].__self__.__class__.__name__}.{step_dict['step'].__name__}` executed successfully."
                    )
                    files_to_edit = step_dict["generated_files"]
                    # set each file_to_edit as self.tap_dir / file_to_edit
                    files_to_edit = [
                        str((self.tap_dir / file_to_edit).relative_to(Path.cwd()))
                        for file_to_edit in files_to_edit
                    ]

                    if len(files_to_edit) > 0:
                        self.logger.info(
                            f"Data successfully generated in the following files: "
                            + ", ".join(files_to_edit)
                        )

                    break  # If the step is successful, break the loop and move to the next step
                except Exception as e:
                    if attempt < max_attempts - 1:  # If this was not the last attempt
                        self.logger.warning(
                            f"Error while running {step_dict['step'].__self__.__class__.__name__}.{step_dict['step'].__name__}, attempt {attempt + 1} of {max_attempts}",
                            exc_info=True,
                        )
                    else:  # If this was the last attempt
                        if step_dict["optional"]:
                            self.logger.warning(
                                f"Optional step {step_dict['step'].__self__.__class__.__name__}.{step_dict['step'].__name__} failed after {max_attempts} attempts. Continuing with the next step.",
                                exc_info=True,
                            )
                            break
                        else:
                            # delete tap index
                            self.tap_generator_utils.delete_tap_index(self.tap_id)
                            # Store the error message in actor_results
                            self.actor_results[self.actor_id] = {
                                "status": "failure",
                                "message": f"Error in step {step_dict['step'].__self__.__class__.__name__}.{step_dict['step'].__name__}: {str(e)}",
                            }
                            # Write actor_results to a JSON file
                            with open(
                                Path("data")
                                / "tap_generator"
                                / "results"
                                / "actor_results.json",
                                "w",
                            ) as f:
                                json.dump(self.actor_results, f, indent=4)
                            error_message = f"Exiting after {max_attempts} failed attempts on step {step_dict['step'].__self__.__class__.__name__}.{step_dict['step'].__name__}. Error: {str(e)};"
                            self.logger.error(error_message, exc_info=True)
                            # output error message to stdout without raising
                            self.logger.info(f"{error_message}")

                            files_to_edit = step_dict["generated_files"]
                            # set each file_to_edit as self.tap_dir / file_to_edit
                            files_to_edit = [
                                str(
                                    (self.tap_dir / file_to_edit).relative_to(
                                        Path.cwd()
                                    )
                                )
                                for file_to_edit in files_to_edit
                            ]

                            if len(files_to_edit) > 0:
                                self.logger.info(
                                    f"You may try to manually edit the following files \n {', '.join(files_to_edit)} \n and re-run the script."
                                )
                            return

        # If all steps are successful, store the success message in actor_results
        self.actor_results[self.actor_id] = {
            "status": "success",
            "message": "All steps executed successfully",
        }

        # Write actor_results to a JSON file
        with open(
            Path("data") / "tap_generator" / "results" / "actor_results.json",
            "w",
        ) as f:
            json.dump(self.actor_results, f, indent=4)

        ascii_art = """

 .----------------.  .----------------.  .----------------.  .----------------.  .----------------.  .----------------.  .----------------. 
| .--------------. || .--------------. || .--------------. || .--------------. || .--------------. || .--------------. || .--------------. |
| |  ____  ____  | || | _____  _____ | || |  _______     | || |  _______     | || |      __      | || |  ____  ____  | || |              | |
| | |_   ||   _| | || ||_   _||_   _|| || | |_   __ \    | || | |_   __ \    | || |     /  \     | || | |_   ||   _| | || |      _       | |
| |   | |__| |   | || |  | |    | |  | || |   | |__) |   | || |   | |__) |   | || |    / /\ \    | || |   | |__| |   | || |     | |      | |
| |   |  __  |   | || |  | '    ' |  | || |   |  __ /    | || |   |  __ /    | || |   / ____ \   | || |   |  __  |   | || |     | |      | |
| |  _| |  | |_  | || |   \ `--' /   | || |  _| |  \ \_  | || |  _| |  \ \_  | || | _/ /    \ \_ | || |  _| |  | |_  | || |     | |      | |
| | |____||____| | || |    `.__.'    | || | |____| |___| | || | |____| |___| | || ||____|  |____|| || | |____||____| | || |     |_|      | |
| |              | || |              | || |              | || |              | || |              | || |              | || |     (_)      | |
| '--------------' || '--------------' || '--------------' || '--------------' || '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '----------------'  '----------------'  '----------------'  '----------------'  '----------------' 
        
        """

        success_message = (
            f"\n\n\n"
            f"{ascii_art}"
            f"\n"
            f"{'#' * 50}\n"
            f"{'#' * 8} \033[1;32mSUCCESS: Tap Generation Complete!\033[0m {'#' * 7}\n"  # Green color
            f"{'#' * 50}\n"
            f"New tap has been successfully generated from actor id {self.actor_id}.\n"
            f"All steps were executed successfully without any errors.\n"
            f"Please check the generated tap in the directory: {self.tap_dir}\n"
            f"{'#' * 50}\n"
            f"To run a test of the newly generated tap, use the following command:\n"
            f"    python -m tests.apify_tap_test --apify_tap_id={self.tap_id} --model=gpt-4 --test_num=0"
        )
        self.logger.info(success_message)
