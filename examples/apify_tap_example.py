import json, logging, pdb
from importlib.resources import files
from abc import ABC, abstractmethod
from webtap.base_tap import BaseTap
from pydantic import BaseModel
from langchain.prompts import load_prompt
from webtap.tap_manager import TapManager
from typing import List


def apify_tap_with_tap_manager_example():
    logging.basicConfig(level=logging.INFO)
    logging.info("Apify tap example")
    # Load tap_manager
    tap_manager = TapManager()
    print("Tap manager", tap_manager)
    # get tap "tripadvisor"
    tap = tap_manager.get_tap("twitter")
    print("Tap", tap)
    # set tap to use gpt4
    # tap.openai_model = "gpt-4"

    # Get data for a specific data task
    data_task = "Tweets by @elonmusk"

    # get sample data
    sample_data_return = tap.retrieve_sample_data(data_task)
    logging.info("Apify tap sample data return: %s", sample_data_return)
    sample_data = sample_data_return["data"]

    # validate data
    validate_data_return = tap.validate_data(data_task, sample_data)
    logging.info("Apify tap validate data return: %s", validate_data_return)

if __name__ == "__main__":
    apify_tap_with_tap_manager_example()