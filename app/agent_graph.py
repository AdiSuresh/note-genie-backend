from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

system_message = SystemMessage('You are a helpful assistant that can produce human-like responses.')

prompt = ChatPromptTemplate.from_messages(
    [
        system_message,
        MessagesPlaceholder(variable_name='messages'),
    ]
)

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


class AgentGraph(StateGraph):
    @staticmethod
    def create_graph(llm, tools, memory) -> CompiledStateGraph:
        return AgentGraph(llm, tools, memory).graph
    
    def chatbot(self, state: AgentState):
        chain = prompt | self.llm
        message = chain.invoke({'messages': state['messages']})
        assert len(message.tool_calls) <= 1
        return {'messages': [message]}
    
    def __init__(self, llm, tools, memory):
        super().__init__(state_schema=AgentState)

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
