import json, os
from importlib.resources import files
from abc import ABC, abstractmethod
from webtap.base_tap import BaseTap
from webtap.apify_tap.apify_tap import ApifyTap, Actor, ApifyTapActor
from pydantic import BaseModel
from langchain.prompts import load_prompt, PromptTemplate

class TripAdvisorTap(ApifyTap):
    '''
    TripAdvisorTap is a Tap that is able to manage/scrape/validate data from a TripAdvisor Actor.
    It is inherited from ApifyTap, so it basically works by simply defining info about the actor and the prompt template, in this case a collection of json files is used to define the actor info and the prompt template.
    '''

    def load_json_data(self, json_file):        
        file_content = (files(__package__) / json_file ).read_text()
        data = json.loads(file_content)
        return data

    def __init__(self, *args, **kwargs):

        data_templates: dict = {
            "actor_description" : "data/actor-description.json",
            "actor_input_json_schema" : "data/actor-input-json-schema.json",
            "actor_input_summary" : "data/actor-input-summary.json",
            "actor_output_fields" : "data/actor-output-fields.json",
            "prompt" : "data/prompt.txt",
            "tap_description" : "data/tap-description.json"
        }

        # load prompt file
        prompt_template = (files(__package__) / data_templates['prompt']).read_text()
        
        # load json files
        actor_description = self.load_json_data(data_templates['actor_description'])
        actor_input_schema = self.load_json_data(data_templates['actor_input_json_schema'])
        actor_input_body_summary = self.load_json_data(data_templates['actor_input_summary'])["actor_input_summary"]
        actor_output_fields = self.load_json_data(data_templates['actor_output_fields'])["actor_output_fields"]
        tap_description = self.load_json_data(data_templates['tap_description'])

        super().__init__( 
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