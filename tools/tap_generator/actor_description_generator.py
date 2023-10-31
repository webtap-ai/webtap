import demjson3, html2text
import json
from webtap.taps.apify_tap import Actor
from pydantic import ValidationError
from tools.tap_generator.tap_generator_utils import TapGeneratorUtils


class ActorDescriptionGenerator:
    def __init__(self, logger, llm):
        self.logger = logger
        self.tap_generator_utils = TapGeneratorUtils(logger)
        self.llm = llm

    def generate_readme_summary(self, description, full_readme):
        # Convert the readme to markdown
        h = html2text.HTML2Text()
        readme_md = h.handle(full_readme)
        self.logger.debug("Converted readme to markdown")

        # Check that readme has over 1000 characters
        if len(readme_md) < 1000:
            self.logger.debug("Readme has less than 1000 characters")
            return readme_md

        # Truncate readme to max 10.000 characters if needed
        readme_truncated = readme_md[:10000]
        self.logger.debug("Truncated readme to max 10.000 characters if needed")

        # Run the prompt with LLM
        try:
            readme_summary = self.tap_generator_utils.run_json_prompt_llm(
                "generate_readme_summary.txt",
                {"description": description, "readme": readme_truncated},
                self.llm,
                "gpt-3.5-turbo",
            )
        except Exception as e:
            error_message = f"An error occurred during the execution of `ActorDescriptionGenerator.generate_readme_summary` while executing `self.tap_generator_utils.run_json_prompt_llm` the following error was raised: {e}"
            self.logger.error(error_message)
            raise ValueError(error_message) from e
        self.logger.debug("Ran the prompt with LLM")

        # Get the data from json returned key readme_summary
        readme_summary_data = readme_summary.get("readme_summary", "")
        self.logger.debug("Got the data from json returned key readme_summary")

        # Truncate data returned at no more than 1200 characters
        readme_summary_data_truncated = readme_summary_data[:1200]
        self.logger.debug("Truncated data returned at no more than 1200 characters")

        return readme_summary_data_truncated

    def generate(self, tap_dir, actor_id, actor_details):
        actor_description_path = tap_dir / "actor-description.json"

        # Check if actor-description.json already contains an 'id' key
        if actor_description_path.exists():
            with open(actor_description_path, "r") as json_file:
                actor_description = demjson3.decode(json_file.read())
                if "id" in actor_description:
                    self.logger.info(
                        "Actor description already exists for tap " + actor_id
                    )
                    return

        self.logger.debug(
            "Actor details for " + actor_id + ": " + str(actor_details[actor_id])
        )

        actor_data = actor_details[actor_id]

        actor_data["id"] = actor_data["actor_id"]
        # delete actor_id
        del actor_data["actor_id"]

        # Check if the returned data is a JSON object
        if not isinstance(actor_data, dict):
            error_message = "Returned data is not a JSON object"
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Check if the returned data contains 'id' and it's equal to actor_id
        if "id" not in actor_data or actor_data["id"] != actor_id:
            error_message = "Returned data does not contain 'id' or 'id' does not match with actor_id"
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Check if the returned data contains 'name' and it's a string with more than 2 chars
        if (
            "name" not in actor_data
            or not isinstance(actor_data["name"], str)
            or len(actor_data["name"]) < 2
        ):
            error_message = "Returned data does not contain 'name' or 'name' is not a string or has less than 2 chars"
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Check if the returned data contains 'description' and it's a string with more than 10 chars
        if (
            "description" not in actor_data
            or not isinstance(actor_data["description"], str)
            or len(actor_data["description"]) < 5
        ):
            error_message = "Returned data does not contain 'description' or 'description' is not a string or has less than 10 chars"
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Check if the returned data contains 'full_readme_text' and it's a string with more than 10 chars
        if (
            "full_readme" not in actor_data
            or not isinstance(actor_data["full_readme"], str)
            or len(actor_data["full_readme"]) < 10
        ):
            error_message = "Returned data does not contain 'full_readme' or 'full_readme' is not a string or has less than 10 chars"
            self.logger.error(error_message)
            raise ValueError(error_message)

        self.logger.debug("Actor data: " + str(actor_data))

        # Check if 'full_readme_html' exists in actor_details
        if "full_readme_html" not in actor_details[actor_id]:
            error_message = "'full_readme_html' does not exist in actor_details"
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Try to generate the readme summary and handle any exceptions
        try:
            readme_summary = self.generate_readme_summary(
                actor_data["description"], actor_details[actor_id]["full_readme_html"]
            )
            actor_data["readme_summary"] = readme_summary
        except Exception as e:
            error_message = f"An error occurred during the execution of `ActorDescriptionGenerator.generate` while executing `self.generate_readme_summary` the following error was raised: {e}"
            self.logger.error(error_message)
            raise ValueError(error_message) from e

        # remove full_readme_html
        del actor_data["full_readme_html"]

        # Try to initialize a new Actor object
        try:
            actor = Actor(**actor_data)
        except ValidationError as e:
            error_message = f"An error occurred during the execution of `ActorDescriptionGenerator.generate` while initializing `Actor` object the following error was raised: {e}"
            self.logger.error(error_message)
            raise ValueError(error_message) from e

        # Store the data in actor-description.json
        with open(actor_description_path, "w") as json_file:
            json.dump(actor_data, json_file, indent=4)

        self.logger.info(f"Data successfully stored in : {actor_description_path}")

    def generate_from_store_listing(self, tap_dir, actor_id):
        actor_description_from_listing_path = (
            tap_dir / "_actor-description-from-store-listing.json"
        )

        # Check if actor-description.json already contains an 'id' key
        if actor_description_from_listing_path.exists():
            with open(actor_description_from_listing_path, "r") as json_file:
                actor_description = demjson3.decode(json_file.read())
                self.logger.info(
                    "Actor description from store listing already exists for tap "
                    + actor_id
                )
                return

        self.logger.info("Retrieving sample data for tap " + actor_id)
        self.logger.info("This may take a few minutes...")
        # Define the data_task
        listing_url = f"https://apify.com/{actor_id}/"
        instructions = f"Return json object with fields: example_json_input, example_output_json_response"
        required_keys = ["example_json_input"]

        # Try to execute the webtap_universal_scraper method and handle any exceptions
        try:
            actor_data = self.tap_generator_utils.manual_webtap_universal_scraper(
                listing_url, instructions, required_keys
            )
        except Exception as e:
            error_message = f"An error occurred during the execution of `ActorDescriptionGenerator.generate_from_store_listing` while executing `self.tap_generator_utils.manual_webtap_universal_scraper` the following error was raised: {e}"
            self.logger.error(error_message)
            raise Exception(error_message) from e

        self.logger.debug("Actor data: " + str(actor_data))

        # Check if example_output_json_response and example_json_input are JSON strings
        for key in ["example_output_json_response", "example_json_input"]:
            if isinstance(actor_data[key], str):
                # Try to load the JSON data from the string
                try:
                    json_data = self.tap_generator_utils.load_json_example_data(
                        actor_data[key], key
                    )
                except Exception as e:
                    error_message = f"An error occurred during the execution of `ActorDescriptionGenerator.generate_from_store_listing` while executing `self.tap_generator_utils.load_json_example_data` the following error was raised: {e}"
                    self.logger.error(error_message)
                    raise Exception(error_message) from e

                # If the JSON data is None, raise an error
                if json_data is None:
                    raise ValueError(f"Error while transforming {key} to JSON")

                # If the JSON data is not None, assign it back to the actor_data
                actor_data[key] = json_data

                self.logger.debug(f"{key} successfully transformed to JSON.")
            else:
                # If the value of the key is not a string, log the information and keep the data as it is
                self.logger.debug(
                    f"{key} is not a JSON string. Using the data as it is."
                )

        # Store the data in actor-description.json
        with open(actor_description_from_listing_path, "w") as json_file:
            json.dump(actor_data, json_file, indent=4)

        self.logger.info(
            "Data successfully stored in _actor-description-from-store-listing.json"
        )

    def generate_output_field_names(self, tap_dir, actor_id, openai_model):
        actor_output_fields_path = tap_dir / "actor-output-fields.json"

        # Check if actor-output-fields.json already contains a JSON object
        if actor_output_fields_path.exists():
            with open(actor_output_fields_path, "r") as json_file:
                actor_output_fields = json.load(json_file)
                if (
                    isinstance(actor_output_fields, dict)
                    and len(actor_output_fields) > 0
                ):
                    self.logger.info(
                        "Actor output fields already exists for tap " + actor_id
                    )
                    self.logger.debug(
                        "Existing actor output fields: " + str(actor_output_fields)
                    )
                    return

        # Load required fields from actor-description.json
        with open(tap_dir / "actor-description.json", "r") as file:
            actor_description = json.load(file)

            # Check if required fields 'description' and 'readme_summary' are present
            for field in ["description", "readme_summary"]:
                if field not in actor_description:
                    raise ValueError(
                        f"Required field {field} not found in actor-description.json"
                    )

            # Initialize example_output as an array
            example_output = []

            # Load 'example_output_json_response' from _actor-description-from-store-listing.json
            with open(
                tap_dir / "_actor-description-from-store-listing.json", "r"
            ) as file:
                actor_description_from_listing = json.load(file)
                example_output_json_response = actor_description_from_listing.get(
                    "example_output_json_response", {}
                )

            # If 'example_output_json_response' is present, append it to 'example_output'
            if example_output_json_response:
                example_output.append(example_output_json_response)

            # Load 'example_run_output' from _actor_example_run_output.json
            with open(tap_dir / "_actor_example_run_output.json", "r") as file:
                example_run_output = json.load(file)

            # Append 'example_run_output' to 'example_output'
            example_output.append(
                self.tap_generator_utils.truncate_returned_data(example_run_output)
            )

            self.logger.debug("Loaded required fields from actor-description.json.")

        json_output_fields = self.tap_generator_utils.run_json_prompt_llm(
            "generate_output_fields.txt",
            {
                "actor_name": actor_description["name"],
                "description": actor_description["description"],
                "readme": actor_description["readme_summary"],
                "example_output": example_output,
            },
            self.llm,
            openai_model,
        )

        # Check if the returned data is a JSON object with at least 1 property
        if (
            not isinstance(json_output_fields, dict)
            or "actor_output_fields" not in json_output_fields
        ):
            self.logger.error(
                "Returned data is not a JSON object or does not contain 'actor_output_fields' property"
            )
            raise ValueError("Invalid data returned from LLM")

        self.logger.debug("Actor output fields json built: " + str(json_output_fields))
        self.logger.info("Actor output fields json built successfully.")

        # Save the JSON summary into actor-output-fields.json
        with open(actor_output_fields_path, "w") as file:
            json.dump(json_output_fields, file, indent=4)
        self.logger.info(
            "Actor output fields saved successfully in actor-output-fields.json."
        )
