import json, logging, pdb
from importlib.resources import files
from abc import ABC, abstractmethod
from webtap.base_tap import BaseTap
from pydantic import BaseModel
from langchain.prompts import load_prompt
from webtap.tap_manager import TapManager
from typing import List


def apify_tap_with_tap_manager_example():
    # Set logging level
    logging.basicConfig(level=logging.WARNING)
    # Set tap_id and data_task to be used
    tap_id = "atg_epctex_gutenberg_scraper" # Project Gutenberg: a collection of 70,000 free ebooks
    data_task = "Search for 'history', maximum 15 items, in Italian language, using Apify Proxy"

    print("Starting Apify Tap <{}> with data task <{}>".format(tap_id, data_task))
    print("...")

    tap_manager = TapManager()
    tap = tap_manager.get_tap( tap_id )
    
    # get data given the data task
    data_return = tap.get_retriever_and_run(data_task)

    print("\n################################\n")
    print("## Sample of data returned ##")
    print(data_return['data'])

if __name__ == "__main__":
    apify_tap_with_tap_manager_example()
