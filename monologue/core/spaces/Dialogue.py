from pydantic import BaseModel, Field
import typing


class Dialogue(BaseModel):
    """
    structure model of a session
    dumped as timeseries to partitions on s3
    """

    # the textual question
    question: str
    # the textual response
    response: str
    # the agents own confidence in the answer
    confidence: float = Field(default=0)
    # a collection of [tool, record_id]
    keys_used: typing.Optional[str] = Field(default_factory=list)
    # logs of the reasoning session -> dumped to s3
    log_uri: typing.Optional[str]
    # the time of the audit event
    event_time: str
    # a unique session id for grouping purposes e.g. a chain id
    session_id: str
    # a qualified node  <node_type>_<hash> for the person or thing making a request
    source_node_id: str
    # a qualified node  <node_type>_<hash> for the person or thing making a request
    target_node_id: str
