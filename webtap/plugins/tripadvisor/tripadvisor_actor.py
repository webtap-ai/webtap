from core.actor import ApifyActor, ApifyActorExampleRun, ApifyActorInputSchema, ApifyActorOutputSchema

class ApifyActorTripadvisor(ApifyActor):
    '''
    ApifyActorTripadvisor extends the ApifyActor class.
    It provides some default values for the inherited properties.
    '''
    owner_username: str = "tripadvisor_owner"
    name: str = "tripadvisor_actor"
    title: str = "Tripadvisor Actor"
    description: str = "This is a Tripadvisor actor."
    full_readme: str = "This is the full readme for the Tripadvisor actor."
    attribute: str = "tripadvisor_attribute"

    example_run: ApifyActorExampleRun = ApifyActorExampleRun(
        actorInput=ApifyActorInputSchema(), 
        returnedData="Sample returned data"
    )

    output_schema: ApifyActorOutputSchema = ApifyActorOutputSchema()
    input_schema: ApifyActorInputSchema = ApifyActorInputSchema()