import json, os
from importlib.resources import files
from abc import ABC, abstractmethod
from webtap.base_tap import BaseTap
from webtap.taps.apify_tap import ApifyTap, Actor, ApifyTapActor
from pydantic import BaseModel
from langchain.prompts import load_prompt, PromptTemplate

class TripAdvisorCustomTap(ApifyTap):
    '''
    TripAdvisorTap is a Tap that is able to manage/scrape/validate data from a TripAdvisor Actor.
    It is inherited from ApifyTap, so it basically works by simply defining info about the actor and the prompt template, in this case a collection of json files is used to define the actor info and the prompt template.
    '''

    def load_json_data(self, json_file):        
        file_content = (files(__package__) / json_file ).read_text()
        data = json.loads(file_content)
        return data

    def __init__(self, *args, **kwargs):
        # this is just an example, for this reason we are using the standard taps/tripadvisor directory here
        tap_config_dir = files(__package__).joinpath('../../../data/taps/tripadvisor/')
        # define data templates paths
        data_templates: dict = {
            "actor_description" : tap_config_dir.joinpath("actor-description.json"),
            "actor_input_json_schema" : tap_config_dir.joinpath("actor-input-json-schema.json"),
            "actor_input_summary" : tap_config_dir.joinpath("actor-input-summary.json"),
            "actor_output_fields" : tap_config_dir.joinpath("actor-output-fields.json"),
            "examples" : tap_config_dir.joinpath("tap-examples.json"),
            "test_cases" : tap_config_dir.joinpath("test-cases.json"),
            "tap_description" : tap_config_dir.joinpath("tap-description.json")
        }
        
        # load json files
        actor_description = self.load_json_data(data_templates['actor_description'])
        actor_input_schema = self.load_json_data(data_templates['actor_input_json_schema'])
        actor_input_body_summary = self.load_json_data(data_templates['actor_input_summary'])["actor_input_summary"]
        actor_output_fields_data = self.load_json_data(data_templates['actor_output_fields'])
        actor_output_fields = actor_output_fields_data["actor_output_fields"]
        actor_output_views = actor_output_fields_data["actor_output_views"]
        tap_description = self.load_json_data(data_templates['tap_description'])
        examples = self.load_json_data(data_templates['examples'])
        test_cases = self.load_json_data(data_templates['test_cases'])

        super().__init__( 
            examples = examples,
            test_cases = test_cases,
            apify_tap_actor = ApifyTapActor( 
                entities = tap_description['entities'],
                special_instructions = tap_description['special_instructions'],
                actor = Actor(**actor_description),
                input_body_schema = actor_input_schema,
                input_body_summary = actor_input_body_summary,
                output_fields = actor_output_fields,
                output_views = actor_output_views
            )
        )