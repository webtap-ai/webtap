from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional
from abc import abstractmethod


class Retriever(BaseModel):
    """
    DataRetrieverModel is the rappresentation of a how the data task can be can_fulfilled.
    For apify model type will be apify, model id will be the Apify actor id, as exposed on Apify API documentation.
    """

    type: str
    id: str
    input: Any = None


class RetrieverResult(BaseModel):
    """
    BaseTapReturn is the schema rappresentation of the return value of a tap.
    """

    can_fulfill: bool
    explanation: str
    retriever: Retriever = None
    alternative_fulfillable_data_task: str = None


class BaseTap(BaseModel):
    """
    A Tap is an interface definition of a class that is able to manage/scrape/validate data from a specific source.
    Currently the only source is an apify actor, but in the future it could be an API, a web page or a file.
    """

    name: str
    description: str
    chat_salutation: str

    @abstractmethod
    def get_retriever(self, aData_task: str) -> Retriever:
        pass

    @abstractmethod
    def validate_data(self, aData_task: str, aData_sample: str) -> str:
        pass

    @abstractmethod
    def get_retriever_and_run(self, aData_task: str) -> dict:
        pass
