from typing import Optional
from pydantic import BaseModel

class ApifyActorInputSchema(BaseModel):
    '''
    Apify Actor Input Schema is an abstract representation of the input that an Apify actor can receive.
    '''
    pass

class ApifyActorOutputSchema(BaseModel):
    '''
    Apify Actor Output Schema is an abstract representation of the output that an Apify actor can produce.'''
    pass

class ApifyActorExampleRun(BaseModel):
    '''
    Apify Actor Example Run is an abstract representation of an example run of an Apify actor.'''
    actorInput: Optional[ApifyActorInputSchema]
    returnedData: Optional[str]

class ApifyActor(BaseModel):
    '''
    Apify Actor is an abstract representation of a collection of data from an Apify actor.
    Data represented here reflects original data from Apify actor. 
    Any additional data (for example description for LLM should be added in TapActor class)
    '''
    owner_username: Optional[str]
    name: Optional[str]
    title: Optional[str]
    description: Optional[str]
    full_readme: Optional[str]
    attribute: Optional[str]
    example_run: Optional[ApifyActorExampleRun]
    output_schema: Optional[ApifyActorOutputSchema]
    input_schema: Optional[ApifyActorInputSchema]
