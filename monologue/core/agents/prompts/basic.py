from . import typing, PromptTemplate


class ZeroShotPrompt:
    # flake8: noqa
    PREFIX = """Answer the following questions as best you can. If you obseve that you have checked parsing and the answer is completed, return the Final answer formatted.
    You have access to the following tools:"""
    FORMAT_INSTRUCTIONS = """Use the following format until you are ready to check final output parsing:
    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}] except for formatting in which case you should do it yourself.
    Action Input: the input to the action
    Observation: the result of the action
    Confidence: State the confidence you have in the result from 0 to 1
    ... (this Thought/Action/Action Input/Observation/Confidence can repeat N times until the Final Answer and not after!) 
 
    Thought: I now know the final answer!
    """
    SUFFIX = """
    Format instructions:  {output_format_instructions}.
    Final Answer: The final formatted answer to the original input question
    Begin!
    Question: {input}
    Thought:{agent_scratchpad}"""

    @staticmethod
    def create_prompt(
        tools,
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: typing.Optional[typing.List[str]] = None,
        parser=None,
    ) -> PromptTemplate:
        """Create prompt in the style of the zero shot agent.

        Args:
            tools: List of tools the agent will have access to, used to format the
                prompt.
            prefix: String to put before the list of tools.
            suffix: String to put after the list of tools.
            input_variables: List of input variables the final prompt will expect.

        Returns:
            A PromptTemplate with the template assembled from the pieces here.
        """
        tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
        tool_names = ", ".join([tool.name for tool in tools])
        format_instructions = format_instructions.format(tool_names=tool_names)
        template = "\n\n".join([prefix, tool_strings, format_instructions, suffix])
        if input_variables is None:
            input_variables = ["input", "agent_scratchpad"]

        return PromptTemplate(
            template=template,
            input_variables=input_variables,
            partial_variables={
                "output_format_instructions": parser.get_format_instructions()
            },
        )
