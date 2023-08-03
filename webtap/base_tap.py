from pydantic import BaseModel, Field
from typing import Any
from abc import abstractmethod

class DataModel(BaseModel):
    '''
    DataModel is the rappresentation of a how the data task can be delivered.
    For apify model type will be apify, model id will be the Apify actor id, as exposed on Apify API documentation.
    '''
    
    type: str
    id: str
    input: Any = None

class BaseTapReturn(BaseModel):
    '''
    BaseTapReturn is the schema rappresentation of the return value of a tap.
    '''
    can_deliver: bool
    explanation: str
    data_model: DataModel = None
    alternative_fulfillable_data_request: str = None

class BaseTap(BaseModel):
    """
    A Tap is an interface definition of a class that is able to manage/scrape/validate data from a specific source.
    Currently the only source is an apify actor, but in the future it could be an API, a web page or a file.
    """
    name: str
    description: str

    @abstractmethod
    def getDataModel(self, aData_task : str) -> BaseTapReturn:
        pass

    @abstractmethod
    def validateData(self, aData_task : str, aData_sample : str) -> str:
        pass
