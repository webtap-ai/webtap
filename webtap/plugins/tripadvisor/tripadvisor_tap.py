from pydantic import BaseModel
from typing import Optional
from core.actor import ApifyActor, ApifyActorExampleRun, ApifyActorInputSchema, ApifyActorOutputSchema
from core.tap import Tap, TapActor, TapActorInputPromptTemplate, ActorInput
from plugins.tripadvisor.tripadvisor_actor import ApifyActorTripadvisor

class TapActorInputPromptTemplateTripadvisor(TapActorInputPromptTemplate):
    """
    TapActorInputPromptTemplateTripadvisor extends the TapActorInputPromptTemplate class.
    It provides some default values for the inherited properties.
    """
    # Here you can define the specific properties for this class
    template: str = "This is a template prompt for TripAdvisor actor."


class TapActorTripadvisor(TapActor):
    """
    TapActorTripadvisor extends the TapActor class.
    It provides some default values for the inherited properties.
    """
    descriptionForLLM: str = "Description for LLM for Tripadvisor Actor"
    testRunDetails: str = "Test Run Details for Tripadvisor Actor"
    constraints: str = "Constraints for Tripadvisor Actor"
    
    # Using ApifyActorTripadvisor for the apifyActor attribute
    apifyActor: ApifyActorTripadvisor = ApifyActorTripadvisor()
    apifyActorExampleRun: ApifyActorExampleRun = ApifyActorExampleRun(
        actorInput=ApifyActorInputSchema(), 
        returnedData="Sample returned data"
    )
    apifyActorOutputSchema: ApifyActorOutputSchema = ApifyActorOutputSchema()
    apifyActorInputSchema: ApifyActorInputSchema = ApifyActorInputSchema()
    template: TapActorInputPromptTemplateTripadvisor = TapActorInputPromptTemplateTripadvisor()
    input: ActorInput = ActorInput()

    def getInput(self, aData_task : str) -> ActorInput:
        # Implementation here
        pass

    def getTestRunInput(self, aData_task : str) -> ActorInput:
        # Implementation here
        pass

    def validateData(self, aData_task : str, aData_sample : str) -> str:
        # Implementation here
        pass


class TapTripadvisor(Tap):
    """
    TapTripadvisor extends the Tap class.
    It provides some default values for the inherited properties.
    """
    tap_actor: TapActorTripadvisor = TapActorTripadvisor()
    actor_input: ActorInput = ActorInput()

    def getActorInput(self, aData_task : str) -> ActorInput:
        # Implementation here
        pass

    def validateData(self, aData_task : str, aData_sample : str) -> str:
        # Implementation here
        pass
