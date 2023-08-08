from pydantic import BaseModel, validator
from webtap.base_tap import BaseTap, BaseTapReturn, DataModel
from langchain import PromptTemplate, OpenAI, LLMChain
from langchain.chains import create_extraction_chain
import json, logging, os, openai, re, time
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.callbacks.manager import tracing_v2_enabled


class Actor(BaseModel):
    ''' 
    Actor is a representation of an Apify Actor: it contains original data about the actor
    '''
    id : str
    name : str
    description: str

class ActorParameters(BaseModel):
    '''
    ActorParameters is a representation of an Apify Actor API parameters as they are described in Apify API documentation 
    (They are usually added as a query string to the actor api url)
    '''
    actorId: str  # Actor ID or a tilde-separated owner's username and actor name.
    token: str = None  # API authentication token. 
    timeout: int = None  # Optional timeout for the run, in seconds.
    memory: int = None  # Memory limit for the run, in megabytes. 
    maxItems: int = None  # The maximum number of items that the actor run should return.
    build: str = None  # Specifies the actor build to run.
    waitForFinish: int = None  # The maximum number of seconds the server waits for the run to finish.
    webhooks: str = None  # Specifies optional webhooks associated with the actor run.

    @validator('memory')
    def check_memory(cls, value):
        if value is not None and (value < 128 or (value & (value - 1)) != 0):
            raise ValueError('Memory should be a power of 2 and at least 128')
        return value

    @validator('waitForFinish')
    def check_wait_for_finish(cls, value):
        if value is not None and (value < 0 or value > 60):
            raise ValueError('waitForFinish should be between 0 and 60')
        return value

class ActorInput(BaseModel):
    '''
    ApifyInput is a representation of an Apify Actor input: it contains the parameters and the body of the actor
    '''
    # set parameters as default ActorParameters with default values
    parameters : ActorParameters
    body : dict

class ApifyDataModel(DataModel):
    '''
    ApifyDataModel is the rapresentation of a how the data task can be delivered.
    For apify model type will be apify, model id will be the Apify actor id, as exposed on Apify API documentation.
    '''
    type: str = "apify"
    input: ActorInput

class ApifyTapReturn(BaseTapReturn):
    '''
    ApifyTapReturn is the abstract schema rappresentation of the return value of a tap.
    '''
    data_model : ApifyDataModel = None

class ApifyTapActor(BaseModel):
    '''
    ApifyTapActor is a Tap representation of an Apify Actor: it encapsulate an Apify Actor, its input data and has some additional data useful for Tap purposes
    '''
    entities : str
    special_instructions: str
    actor : Actor
    input_body_schema : dict
    input_body_summary: str
    output_fields: str

class ApifyTap(BaseTap):
    """
    Apify Tap is a generic tap that is able to manage/scrape/validate data from an Apify Actor.
    It works by simply defining info about the actor and the prompt template
    """

    name: str = "Apify Base Actor Tap"
    description: str = "Tap to operate on lots of Apify Actors by simply defining some data input"
    prompt_template: str
    apify_tap_actor: ApifyTapActor

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def extract_last_json_object(self, text):
        stack = []
        json_end = None
        for i in reversed(range(len(text))):
            if text[i] == '}':
                if json_end is None:
                    json_end = i
                stack.append('}')
            elif text[i] == '{':
                stack.pop()
                if len(stack) == 0:
                    return json.loads(text[i:json_end+1])

        raise ValueError('No valid JSON object found in the text.')


    def getDataModel(self, data_task : str) -> ApifyTapReturn:
        
        # init logging, openai
        logger = logging.getLogger(__name__)
        execution_start_time = time.time()
        # check if openai os env variable is set
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY env variable is not set")
        
        openai.api_key = os.environ["OPENAI_API_KEY"]
        # set verbose to true if loggin level is info or above
        verbose = logger.getEffectiveLevel() <= logging.INFO

        # generate the chat messages
        human_message_prompt = HumanMessagePromptTemplate.from_template(self.prompt_template)
        chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
        chat_prompt_formatted = chat_prompt.format_prompt(
            actor_name = self.apify_tap_actor.actor.name,
            list_of_returned_fields = self.apify_tap_actor.output_fields,
            input_json_schema = self.apify_tap_actor.input_body_schema,
            special_instructions = self.apify_tap_actor.special_instructions,
            task_requested_data = data_task,
            actor_input_summary = self.apify_tap_actor.input_body_summary
        )
        messages = chat_prompt_formatted.to_messages()

        # define and run the llm
        
        llm = ChatOpenAI(temperature=0, model="gpt-4", verbose=verbose)
        chain_output = llm( messages )

        # log prompt response
        logger.info("Chain executed correctly, chain plain response: %s", chain_output)        

        # check that chain_output is not empty and is object with content property
        if( chain_output is None or not hasattr(chain_output, "content")):
            raise ValueError("Data returned from LLM is empty or doesn't contain content property")

        # extract list of json values from chain_output
        try:
            prompt_response = self.extract_last_json_object(chain_output.content)
        except ValueError:
            raise ValueError("Data returned from LLM doesn't contain a valid json")

        # check that prompt_response contains can_fulfill and explanation
        if( "can_fulfill" not in prompt_response or "explanation" not in prompt_response):
            raise ValueError("Data returned from LLM doesn't contain can_fulfill or explanation")
        
        # log prompt response
        logger.info("Prompt executed correctly, prompt response: %s", prompt_response) 

        data_model = None
        if prompt_response["can_fulfill"]:
            data_model = ApifyDataModel(
                id=self.apify_tap_actor.actor.id, 
                input=ActorInput(parameters=ActorParameters(actorId=self.apify_tap_actor.actor.id), 
                body=prompt_response["input_params"]
                )
            )

        # create tap return
        tapReturn = ApifyTapReturn(
            can_deliver=prompt_response["can_fulfill"], 
            explanation=prompt_response["explanation"], 
            data_model=data_model, 
            alternative_fulfillable_data_request=prompt_response.get("alternative_fulfillable_data_request", None)
        )

        execution_time = time.time() - execution_start_time
        logger.info("Tap execution time: %s", execution_time)

        return tapReturn

    def validateData(self, aData_task : str, aData_sample : str) -> str:
        '''
        Validates the data returned by Apify Actor
        '''
        pass