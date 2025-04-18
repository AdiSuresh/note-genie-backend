from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class AgentGraph(StateGraph):
    def chatbot(self, state: AgentState):
        message = self.llm.invoke(state['messages'])
        # Because we will be interrupting during tool execution,
        # we disable parallel tool calling to avoid repeating any
        # tool invocations when we resume.
        assert len(message.tool_calls) <= 1
        return {'messages': [message]}
    
    def __init__(self, llm, tools):
        super().__init__(state_schema=AgentState)

        memory = MemorySaver()

        self.llm = llm
        
        self.add_node('chatbot', self.chatbot)

        tool_node = ToolNode(tools=tools)
        self.add_node('tools', tool_node)

        self.add_conditional_edges(
            'chatbot',
            tools_condition,
        )
        self.add_edge('tools', 'chatbot')
        self.add_edge(START, 'chatbot')
        
        self.graph = self.compile(
            checkpointer=memory,
        )
