from typing import Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel
from core.actor import ApifyActor, ApifyActorExampleRun, ApifyActorOutputSchema, ApifyActorInputSchema

class ActorInput(BaseModel):
    '''
    Actor Input is an abstract representation of the input needed for an Apify actor to run.
    '''
    actorId: Optional[str] = None
    params: Optional[str] = None
    body: Optional[str] = None


class TapActorInputPromptTemplate(BaseModel):
    '''
    Tap Actor Input Prompt Template is an abstract representation of prompt template to generate ActorInput from given task data
    '''
    pass


class TapActor(BaseModel, ABC):
    """
    A TapActor is representation of an Actor suitable for webtap library.
    Basically it includes the original ApifyActor data with additional data about the actor (for example specific instructions for LLM).
    """
    descriptionForLLM: Optional[str] = None
    testRunDetails: Optional[str] = None
    constraints: Optional[str] = None

    # Here you include the instances of the other classes as attributes of TapActor
    apifyActor: Optional[ApifyActor] = None
    apifyActorExampleRun: Optional[ApifyActorExampleRun] = None
    apifyActorOutputSchema: Optional[ApifyActorOutputSchema] = None
    apifyActorInputSchema: Optional[ApifyActorInputSchema] = None
    template: TapActorInputPromptTemplate
    input: ActorInput

    @abstractmethod
    def getInput(self, aData_task : str) -> ActorInput:
        pass

    @abstractmethod
    def getTestRunInput(self, aData_task : str) -> ActorInput:
        pass

    @abstractmethod
    def validateData(self, aData_task : str, aData_sample : str) -> str:
        pass


class Tap(BaseModel, ABC):
    """
    A Tap is a class that is able to manage/scrape/validate data from a specific source.
    Currently the only source is an apify actor, but in the future it could be an API, a web page or a file.
    So currently Tap is basically a TapActor manager
    """
    tap_actor: TapActor
    actor_input: ActorInput

    @abstractmethod
    def getActorInput(self, aData_task : str) -> ActorInput:
        pass

    @abstractmethod
    def validateData(self, aData_task : str, aData_sample : str) -> str:
        pass
