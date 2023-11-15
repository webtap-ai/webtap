import json, os, re, pkg_resources
from importlib.resources import files
from abc import ABC, abstractmethod
from webtap.base_tap import BaseTap
from webtap.taps.apify_tap import ApifyTap, Actor, ApifyTapActor
from pydantic import BaseModel
from langchain.prompts import load_prompt, PromptTemplate
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from typing import List, Any, Optional
import pkg_resources


class UniversalTap(ApifyTap):
    """ """

    output_response_schema_custom: Optional[dict] = None

    # Function to extract version from setup.py
    def get_version_from_setup(self):
        project_setup_file = files(__package__).joinpath("../../../setup.py")
        with open(project_setup_file, "r") as setup_file:
            setup_content = setup_file.read()
            version_match = re.search(r'version="(.*)"', setup_content)
            if version_match:
                return version_match.group(1)
            else:
                return None

    def get_version(self):
        try:
            return pkg_resources.get_distribution("webtap").version
        except pkg_resources.DistributionNotFound:
            return None

    def load_json_data(self, json_file):
        file_content = (files(__package__) / json_file).read_text()
        data = json.loads(file_content)
        return data

    def __init__(self, *args, **kwargs):
        # this is just an example, for this reason we are using the standard taps/tripadvisor directory here
        tap_config_dir = files(__package__).joinpath(
            "../../../data/taps/custom_universal/"
        )
        # define data templates paths
        data_templates: dict = {
            "actor_description": tap_config_dir.joinpath("actor-description.json"),
            "actor_input_json_schema": tap_config_dir.joinpath(
                "actor-input-json-schema.json"
            ),
            "actor_input_summary": tap_config_dir.joinpath("actor-input-summary.json"),
            "actor_output_fields": tap_config_dir.joinpath("actor-output-fields.json"),
            "examples": tap_config_dir.joinpath("tap-examples.json"),
            "test_cases": tap_config_dir.joinpath("test-cases.json"),
            "tap_description": tap_config_dir.joinpath("tap-description.json"),
        }

        # validate if all files exist
        for template_name, template_path in data_templates.items():
            if not template_path.is_file():
                raise FileNotFoundError(
                    f"{template_name} file must be defined in order to instantiate a new Apify tap"
                )
            # check that each file is valid json
            try:
                self.load_json_data(template_path)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"{template_name} is not a valid json file")

        # load templates
        actor_description = self.load_json_data(data_templates["actor_description"])
        actor_input_schema = self.load_json_data(
            data_templates["actor_input_json_schema"]
        )
        actor_input_body_summary = self.load_json_data(
            data_templates["actor_input_summary"]
        )["actor_input_summary"]
        actor_output_fields = self.load_json_data(
            data_templates["actor_output_fields"]
        )["actor_output_fields"]
        tap_description = self.load_json_data(data_templates["tap_description"])
        examples = self.load_json_data(data_templates["examples"])
        test_cases = self.load_json_data(data_templates["test_cases"])

        super().__init__(
            name=tap_description["name"],
            entities=tap_description["entities"],
            filters=tap_description["filters"],
            options=tap_description["options"],
            special_instructions=tap_description["special_instructions"],
            memory_requirement=tap_description["memory_requirement"],
            examples=examples,
            test_cases=test_cases,
            apify_tap_actor=ApifyTapActor(
                actor=Actor(**actor_description),
                input_body_schema=actor_input_schema,
                input_body_summary=actor_input_body_summary,
                output_fields=actor_output_fields,
            ),
        )

        # add an "EXPERIMENTAL" tag and info
        self.description = "EXPERIMENTAL TAP: " + self.description

        # version = self.get_version_from_setup()
        version = self.get_version()
        self.chat_salutation = (
            "This is an experimental tap: use it only if other taps are not available for your use case. Differently from other taps this tap will `try` to fulfill your request, but it may (and will) fail in some cases.\n\n"
            + self.chat_salutation
            + f"\nV{version}"
        )

        # customize prompt template
        prompt_file = tap_config_dir.joinpath("prompt.txt")
        self.prompt_template = prompt_file.read_text()
        # customize output_response_schema
        output_response_schema_file = tap_config_dir.joinpath(
            "output_response_schema.json"
        )
        with open(output_response_schema_file) as f:
            self.output_response_schema_custom = json.load(f)

    def generate_prompt_messages(self, data_task: str) -> List[str]:
        # this is the same code of ApifyTap, only differences are that (1) we are using a custom output_response_schema and (2) in special instructions and examples the variable openaiApiKey input is accordingly formatted
        openai_api_key = os.environ["OPENAI_API_KEY"]

        # generate the chat messages
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            self.prompt_template
        )
        chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
        chat_prompt_formatted = chat_prompt.format_prompt(
            actor_name=self.apify_tap_actor.actor.name,
            examples=self.format_json(
                self.get_prompt_examples(), openai_api_key=openai_api_key
            ),
            output_response_schema=self.format_json(
                self.output_response_schema_custom,
                actor_name=self.apify_tap_actor.actor.name,
            ),
            list_of_returned_fields=self.apify_tap_actor.output_fields,
            input_json_schema=self.apify_tap_actor.input_body_schema,
            special_instructions="\n".join(
                self.format_json(
                    self.special_instructions,
                    actor_name=self.apify_tap_actor.actor.name,
                    openai_api_key=openai_api_key,
                )
            ),
            data_task=data_task,
            actor_input_summary=self.apify_tap_actor.input_body_summary,
        )
        messages = chat_prompt_formatted.to_messages()
        return messages
