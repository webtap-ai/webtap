import os
import json, time
from pathlib import Path
from typing import List
from apify_client import ApifyClient
from tools.tap_generator.tap_generator_utils import TapGeneratorUtils


class ActorTestRun:
    def __init__(self, logger):
        self.logger = logger
        self.apify_client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
        self.tap_generator_utils = TapGeneratorUtils(logger)

    def apify_call_with_retry(self, actor_id, primary_input_data, secondary_input_data):
        try:
            result = self.tap_generator_utils.apify_run_actor(
                actor_id, primary_input_data
            )
            if not result or len(result) == 0:
                self.logger.error(
                    "No items returned from the actor test run with primary input. Retrying with secondary input."
                )
                error_message = (
                    "No items returned from the actor test run with primary input."
                )
                raise Exception(error_message)
        except Exception as e:
            error_message = f"An error occurred during the execution of `apify_call_with_retry` while executing `self.tap_generator_utils.apify_run_actor` with primary input data. The following error was raised: {e}"
            self.logger.error(error_message)
            try:
                result = self.tap_generator_utils.apify_run_actor(
                    actor_id, secondary_input_data
                )
                if not result or len(result) == 0:
                    self.logger.debug(
                        "No items returned from the actor test run with secondary input."
                    )
                    error_message = "No items returned from the actor test run with secondary input."
                    raise Exception(error_message)
            except Exception as e:
                error_message = f"An error occurred during the execution of `apify_call_with_retry` while executing `self.tap_generator_utils.apify_run_actor` with secondary input data. The following error was raised: {e}"
                self.logger.error(error_message)
                raise Exception(error_message) from e

        return result

    def test_run(self, tap_dir, actor_id, actor_apis, max_items: int = 5):
        actor_input_example_path = tap_dir / "actor-input-example.json"
        actor_description_from_listing_path = (
            tap_dir / "_actor-description-from-store-listing.json"
        )
        actor_output_path = tap_dir / "_actor_example_run_output.json"

        # 0. Check if _actor_example_run_output.json already exists
        if actor_output_path.exists():
            with open(actor_output_path, "r") as json_file:
                actor_output_example = json.load(json_file)
                self.logger.debug(
                    f"{actor_output_path} already exists with valid data."
                )
                return

        # Try to load the primary example for the actor from actor-input-example.json
        try:
            with open(actor_input_example_path, "r") as json_file:
                actor_primary_example = json.load(json_file)
        except Exception as e:
            error_message = f"An error occurred during the execution of `ActorTestRun.test_run` while executing `json.load` for primary example the following error was raised: {e}"
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

        self.logger.info(
            f"Going to run apify actor with primary input example: {actor_primary_example}"
        )
        self.logger.info(f"Secondary input example: {actor_secondary_example}")

        # 2. With this input run actor on Apify, if it fails, retry with secondary input
        result = self.apify_call_with_retry(
            actor_id, actor_primary_example, actor_secondary_example
        )

        # 3. Check that if at least 1 item has been returned
        if not result or len(result) == 0:
            self.logger.error(
                "No items returned from the actor test run with both primary and secondary inputs."
            )
            error_message = "No items returned from the actor test run with both primary and secondary inputs."
            raise Exception(error_message)

        # 4. Store the returned items in file _actor_example_run_output.json
        with open(actor_output_path, "w") as file:
            json.dump(result, file)

        self.logger.info(f"Actor run output stored in {actor_output_path}")

    """
    def apify_call(self, actor_id, input_data, max_items: int = 1):
        # Initialize the ApifyClient with API token
        if "APIFY_API_TOKEN" not in os.environ:
            self.logger.error("APIFY_API_TOKEN env variable is not set")
            raise ValueError("APIFY_API_TOKEN env variable is not set")
        apify_api_token = os.environ["APIFY_API_TOKEN"]

        client = ApifyClient(apify_api_token)
        # Start the actor and immediately return the Run object
        actor_run = client.actor(actor_id).start(run_input=input_data)
        self.logger.info("Actor started, waiting for it to finish...")

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
