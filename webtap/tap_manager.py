from pydantic import BaseModel, validator, root_validator
from typing import Dict, Any
from webtap.taps.apify_tap import ApifyTap, ApifyTapActor, Actor
from importlib.resources import files
from importlib import import_module
import json, os, importlib, logging

class TapParams(BaseModel):
    config_dir: str = None
    class_: str = None
    @validator('config_dir', allow_reuse=True)
    def validate_config_dir(cls, v):
        if v is not None:
            tap_config_dir = files(__package__).joinpath('../data/taps/' + v)
            if not tap_config_dir.is_dir():
                print("tap_config_dir: ", tap_config_dir)
                raise ValueError('config_dir must be an existing directory')
            return v

    @validator('class_', allow_reuse=True)
    def validate_class_(cls, v):
        if v is not None:
            module_name, class_name = v.rsplit('.', 1)
            try:
                module = importlib.import_module(module_name)
                getattr(module, class_name)
            except (ImportError, AttributeError):
                raise ValueError('class_ must be a valid class that can be initiated')
            return v
    
    @root_validator
    def validate_config_or_class(cls, values):
        config_dir = values.get('config_dir')
        class_ = values.get('class_')
        if config_dir is None and class_ is None:
            raise ValueError('Either config_dir or class_ must be provided and valid')
        return values

class TapsIndex(BaseModel):
    __root__: Dict[str, TapParams]

class TapManager:
    tap_index_file = files(__package__).joinpath('../data/tap_manager/taps_index.json')
    tap_index: TapsIndex = None
    taps = []

    def load_json_data(self,json_file):
        with open(json_file) as f:
            return json.load(f)

    def load_index(self):
        json_index = self.load_json_data(self.tap_index_file)
        self.tap_index = TapsIndex(__root__=json_index)
        
    def load_standard_tap(self, tap_config_params: TapParams):
        tap_config_dir = files(__package__).joinpath('../data/taps/' + tap_config_params.config_dir)
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

        # validate if all files exist
        for template_name, template_path in data_templates.items():
            if not template_path.is_file():
                raise FileNotFoundError(f"{template_name} file must be defined in order to instantiate a new Apify tap")
            # check that each file is valid json
            try:
                self.load_json_data(template_path)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"{template_name} is not a valid json file")


        # load templates
        actor_description = self.load_json_data(data_templates['actor_description'])
        actor_input_schema = self.load_json_data(data_templates['actor_input_json_schema'])
        actor_input_body_summary = self.load_json_data(data_templates['actor_input_summary'])["actor_input_summary"]
        actor_output_fields = self.load_json_data(data_templates['actor_output_fields'])["actor_output_fields"]
        tap_description = self.load_json_data(data_templates['tap_description'])
        examples = self.load_json_data(data_templates['examples'])
        test_cases = self.load_json_data(data_templates['test_cases'])

        # create apify_tap and init all values
        tap = ApifyTap(
            examples = examples,
            test_cases = test_cases,
            apify_tap_actor = ApifyTapActor( 
                entities = tap_description['entities'],
                special_instructions = tap_description['special_instructions'],
                actor = Actor(**actor_description),
                input_body_schema = actor_input_schema,
                input_body_summary = actor_input_body_summary,
                output_fields = actor_output_fields
            )
        )
        return tap

    def load_custom_tap(self, tap_config_params: TapParams):
        logger = logging.getLogger(__name__)

        logger.info(f"Loading custom tap with class: {tap_config_params.class_}")
        tap_class = tap_config_params.class_.rsplit('.', 1)
        logger.info(f"Tap class: {tap_class}")
        module_name, class_name = tap_class
        logger.info(f"Importing module: {module_name}, class: {class_name}")
        module = importlib.import_module(module_name)
        # istantiate tap as a new class of type module_name
        tap = getattr(module, class_name)()
        
        logger.info(f"Successfully loaded custom tap: {tap_config_params.class_}")
        return tap

    def load_taps(self):
        taps = {}
        for tap_id, tap_params in self.tap_index.__root__.items():
            if tap_params.class_:
                tap = self.load_custom_tap(tap_params)
            else:
                tap = self.load_standard_tap(tap_params)
            taps[tap_id] = tap
        return taps
    
    def __init__(self):
        self.load_index()
        self.taps = self.load_taps()

    def get_tap(self, tap_id) -> ApifyTap:
        return self.taps.get(tap_id, None)
    
    def get_taps(self) -> Dict[str, ApifyTap]:
        return self.taps