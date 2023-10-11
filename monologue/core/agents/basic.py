# TODO: add the entity description in pydantic and feed context since otherwise we rely on the name
# parse all retrieval and chain from langhain trains and structure -> generate dolaogue and ratings
# create more pydantic types for responses
# Add top N columnar stoes results for quesioning answering
# ER tools and graph tools
# Pydantic responses for graphs and other structures

from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from . import Dialogue
import os
from langchain.output_parsers import PydanticOutputParser
from monologue.core.agents.prompts import ZeroShotPrompt
from monologue import logger
from monologue.core.agents import TheLangchainCallbackHandler
import openai
import json


DEFAULT_LLM_MODEL = os.environ.get("MONO_LLM_MODEL", "gpt-4")


def strategy(context, key=None):
    if key == "ABCDE":
        return ""
    if key == "QuestionGenerator":
        return f""" Your job is to generate diverse and interesting question sets using data from the tools provided. 
      As you use the tools, You will observe entity names and statistics to give you ideas about further questions to ask. 
      You should have questions that are a mixture of statistical and entity related. 
      Entity related questions will look for further details on specific entities.
      Use this specific instructions below in your strategy:
      Instructions:
     {context }
     - Do not generate all your questions at the time same time.
     - You should generate one question at a time, then observe your answer and then generate the next question to build a complete set of questions and answers.
     - For each question and answer pair, return a summary of the question, a summary of the answer and your confidence in your answer.
     - If there are no data returned from a tool you should state that you have low confidence in your answer to that specific question.
     Lets takes this step by step.
     You have access to the following tools:"""

    # DEFAULT
    return f""" Answer the question in the context of any entities you observe in the question or in the context using all the available tools. 
    {context}
    Follow this strategy to answer the question and use all the context provided:
    - You should get context by running the stats and data tool first if you can.
    - Then expand any entity codes into their component terms, and pass all terms to the entity resolution tool.
    - The Further details tool should be used if and only if there there is no information available in the other tools. Do not pass identifiers and codes to this tool. Only pass proper nouns and questions.
    Lets takes this step by step.
    You have access to the following tools:"""


class BasicAgent:
    pass


class BasicToolUsingAgent(BasicAgent):
    """ """

    def __init__(self, tools, context=None, **kwargs):
        assert tools, "For now you need to specify a tool - in future ill wing it"
        self._tools = tools
        self._model = kwargs.get("model", DEFAULT_LLM_MODEL)
        self._temperature = kwargs.get("temperature", 0.01)
        prefix = strategy(context)
        self._prefix = prefix
        self._suffix = None
        self.build_prompt()
        self.build_agent()

    def build_prompt(self):
        self._prompt = ZeroShotAgent.create_prompt(self._tools, prefix=self._prefix)

    def build_agent(self):
        llm = ChatOpenAI(
            model_name=self._model,
            temperature=self._temperature,
        )
        self._llm_chain = LLMChain(llm=llm, prompt=self._prompt)
        tool_names = [tool.name for tool in self._tools]
        self._agent = ZeroShotAgent(llm_chain=self._llm_chain, allowed_tools=tool_names)
        self._agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self._agent,
            tools=self._tools,
            verbose=True,
            callbacks=[TheLangchainCallbackHandler(self)],
            handle_parsing_errors="check parsing",
            # output_parser=output_parser,
        )

    def __call__(self, question):
        return self._agent_executor.run(question)

    def get_dialogue(self) -> Dialogue:
        return None


class BasicTypedResponseToolUsingAgent(BasicToolUsingAgent):
    """

    from pydantic import BaseModel, Field
    import typing

    class PObject(BaseModel):
        picked_up: str = Field(description="pickup location]")
        picked_up: str = Field(description="pickup location]")
        name: str = Field(description="name")
        distance: float = Field(description="distance traveled")
        confidence: typing.Optional[float]

    class PObjects(BaseModel):
        objects: typing.List[PObject]= Field(description="collection of objects")

    agent = BasicTypedResponseToolUsingAgent(tools=tools, ptype=PObjects)
    agent("Give three example trips with the passenger, source, target and distance traveled")

    """

    def __init__(self, ptype, tools, context=None, on_parse_error=None, **kwargs):
        self._ptype = ptype
        self._on_parse_error = on_parse_error
        super().__init__(tools=tools, context=context, **kwargs)

    def build_prompt(self):
        # make a parer
        self._parser = PydanticOutputParser(pydantic_object=self._ptype)
        # uae the custom prompt for this with output
        self._prompt = ZeroShotPrompt.create_prompt(
            tools=self._tools, parser=self._parser
        )

    def __call__(self, question):
        response = self._agent_executor.run(question)
        try:
            return self._parser.parse(response)
        except Exception as ex:
            if self._on_parse_error == "raise":
                raise
            logger.warning(f"Parsed failed {ex}")
            return response


class QuestionGeneratingAgent:
    """
    WIP: does not work very well at the moment

    agent = QuestionGeneratingAgent(tools=tools, temperature=.9)

    #design of questions - do not specify specific entities in question
    #question should be graph related to uncover who what why and their relationships
    agent("Generate 5 questions with answers using the data about trips, passengers and places to understand
    [who] traveled in and [why] someone with their background might have traveled there")

    Relationships can maybe be inferred with
        agent = QuestionGeneratingAgent(tools=tools)
        agent("By looking at the descriptions from tools provided, infer a graph of relationships from the metadata that the tools provide - represent the graph as triplets")

    Notes:
    The ER tool could be handy with pointer to other tools
    The more info tools could also provide some general information rather than empty results

    agent("By looking at the descriptions from tools provided, infer a graph of relationships from the metadata that the tools provide - represent the graph as triplets. Provide one example from the data for each triplet")

    Based on the information provided by the tools, the following triplets can be inferred:\n\n1. (AvengingPassengersInstruct, travels_in, Places) - This relationship indicates that the AvengingPassengersInstruct entities travel in the Places entities. An example of this would be a passenger named "Phillip Javert" traveling in "Manhattan".\n\n2. (Places, has, NycTripEvent) - This relationship indicates that the Places entities have NycTripEvent entities. An example of this would be "Manhattan" having a trip event where "Phillip Javert" was picked up at "Midtown Center" and dropped off at "Lenox Hill West".\n\n3. (NycTripEvent, involves, AvengingPassengersInstruct) - This relationship indicates that the NycTripEvent entities involve AvengingPassengersInstruct entities. An example of this would be a trip event where "Phillip Javert" was the passenger.
    """

    def __init__(self, tools, context=None, **kwargs):
        self._tools = tools
        self._model = kwargs.get("model", DEFAULT_LLM_MODEL)
        self._temperature = kwargs.get("temperature", 0.01)
        prefix = strategy(key="QuestionGenerator", context=context)
        self._prefix = prefix
        self._suffix = None
        self.build()

    def build(self):
        prompt = ZeroShotAgent.create_prompt(
            self._tools,
            prefix=self._prefix,
            suffix=self._suffix,
            input_variables=["input", "agent_scratchpad"],
        )
        llm = ChatOpenAI(model_name=self._model, temperature=self._temperature)
        self._llm_chain = LLMChain(llm=llm, prompt=prompt)
        tool_names = [tool.name for tool in self._tools]
        self._agent = ZeroShotAgent(llm_chain=self._llm_chain, allowed_tools=tool_names)
        self._agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self._agent,
            tools=self._tools,
            verbose=True,
            handle_parsing_errors="check parsing",
        )

    def __call__(self, question):
        return self._agent_executor.run(question)

    def get_dialogue(self) -> Dialogue:
        return None


def open_ai_functions(functions, question, limit=10):
    """
    WIP
    will probably deprecate the use of the langchain agents and build out one agent interface from this
    """
    plan = f""" You are an assistant that answers questions using provided data and functions.   """

    messages = [
        {"role": "system", "content": plan},
        {"role": "user", "content": question},
    ]

    for i in range(limit):
        response = openai.ChatCompletion.create(
            model=DEFAULT_LLM_MODEL,
            messages=messages,
            functions=functions,
            function_call="auto",
        )

        response_message = response["choices"][0]["message"]
        # print('thinking....', response_message.get('content'))

        if response_message.get("function_call"):
            function_name = response_message["function_call"]["name"]
            function_to_call = eval(function_name)
            function_args = json.loads(response_message["function_call"]["arguments"])
            # print(f"""{function_name}('{function_args.get("text")}')""")
            function_response = function_to_call(
                text=function_args.get("text"),
            )

            messages.append(response_message)
            messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }
            )

        if response["choices"][0]["finish_reason"] == "stop":
            break
    return response_message["content"]


"""
CALIBRATE

Approach 1 - derive an agent that is good asking questions from soe permutation of tools

agent = BasicToolUsingAgent(tools=tools, context="Answer questions about people taking trips in new york", temperature=.9)

agent(""generate 3 questions that might be interesting about any entities referenced in the data using focusing for example on people and places.
You should get some sample data from the tools to get ideas. 
Answer each question using these tools and give the full set of questions and answers with your confidence on a scale of 1 to 10 in the answer
If there are no data returned you should state that you have low confidence
"")

We need to trace the decision paths between tools and the confidence on each path and store that [human] -> [agent] -> [agent] -> [tool]
store edges
{
    source_node_id
    target_node_id
    session_id
    event_time
    confidence
    data_size
    qualified_data_keys: [table_or_entity_name.key]
}

"""
