"""
    ***
    Spaces are the main idea behind monologue. the following are important
    - schema /views
    - subscriptions
    - performance of agents
    - exchanges of memory fragments
    ***
    
    Spaces must be dynamic but some are based on known entities and processes. 
    We can manage and evolve schema and also views on data
    
    Agents are tools that provide access to spaces. The tool config is similar to the space config
    There is a language of restriction that and focus that is surface in the tool
"""


""" Responses have a format

class Response(BaseModel):
    confidence: str = Field(description="question to set up a joke")
    data: str = Field(description="answer to resolve the joke")
    #records_used for exchange
    #reasoning graph
    
    @validator("setup")
    def check(cls, field):
        # if field[-1] != "?":
        #     raise ValueError("Badly formed question!")
        # return field

"""

from .Schema import SpaceSubscription
from .LogProcessor import LogProcessor
from .IndexManager import IndexManager
