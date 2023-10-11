from langchain.callbacks.base import BaseCallbackHandler
from typing import Dict, Any, Union
from langchain.schema.agent import AgentAction, AgentFinish


class TheLangchainCallbackHandler(BaseCallbackHandler):
    """
    https://python.langchain.com/docs/modules/callbacks/
    """

    def __init__(self, collector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collector = collector

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(f"My custom handler, token: {token}")

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        print(f"Chain start")

    # def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
    #     """Run when chain ends running."""

    # def on_chain_error(
    #     self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    # ) -> Any:
    #     """Run when chain errors."""

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""
        print(f"<< TOOL startng {input_str=} >>>")

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        print(f"<< TOOL DONE {output=} >>>")

    # def on_tool_error(
    #     self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    # ) -> Any:
    #     """Run when tool errors."""

    # def on_text(self, text: str, **kwargs: Any) -> Any:
    #     """Run on arbitrary text."""
    #      print("<< TEXTING >>>")

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action."""
        print(f"<< AGENT ACTING {action=} >>>")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end."""
        print(f"<< AGENT DONE {finish=} >>>")
