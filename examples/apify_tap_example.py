from abc import ABC, abstractmethod
from webtap.base_tap import BaseTap
from webtap.apify_tap.apify_tap import ApifyTap, ApifyTapActor, Actor, ActorInput
from pydantic import BaseModel
import json, logging, pdb
from langchain.prompts import load_prompt

def load_json_data(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    return data

def load_apify_tap_object():

    data_templates: dict = {
            "actor_description" : "examples/apify_tap_example_data/actor-description.json",
            "actor_input_json_schema" : "examples/apify_tap_example_data/actor-input-json-schema.json",
            "actor_input_summary" : "examples/apify_tap_example_data/actor-input-summary.json",
            "actor_output_fields" : "examples/apify_tap_example_data/actor-output-fields.json",
            "prompt" : "examples/apify_tap_example_data/prompt.json",
            "tap_description" : "examples/apify_tap_example_data/tap-description.json"
        }

    # load prompt template
    prompt_template = load_prompt(data_templates['prompt'])
    
    # get data from json
    actor_description = load_json_data(data_templates['actor_description'])
    actor_input_schema = load_json_data(data_templates['actor_input_json_schema'])
    actor_input_body_summary = load_json_data(data_templates['actor_input_summary'])["actor_input_summary"]
    actor_output_fields = load_json_data(data_templates['actor_output_fields'])["actor_output_fields"]
    tap_description = load_json_data(data_templates['tap_description'])

    # create apify_tap and init all values
    apify_tap = ApifyTap(
        prompt_template = prompt_template,
        apify_tap_actor = ApifyTapActor( 
            entities = tap_description['entities'],
            special_instructions = tap_description['special_instructions'],
            actor = Actor(**actor_description),
            input_body_schema = actor_input_schema,
            input_body_summary = actor_input_body_summary,
            output_fields = actor_output_fields
        )
    )
    
    return apify_tap

def apify_tap_example():
    logging.basicConfig(level=logging.INFO)
    logging.info("Apify tap example")

    apify_tap = load_apify_tap_object()

    print("ApifyTap object:")
    print(apify_tap)

    # Get data for a specific data task
    data_task = "Hotels or vacation rentals in Paris, first week of September 2023, currency in EUR, language in Spanish, with email addresses"
    returnData = apify_tap.getDataModel(data_task)
    
    # Log the returned data
    logging.info("Apify tap return data: %s", returnData)

if __name__ == "__main__":
    apify_tap_example()