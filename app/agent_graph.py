from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

system_message = SystemMessage('You are a helpful assistant.')

prompt = ChatPromptTemplate.from_messages(
    [
        system_message,
        MessagesPlaceholder(variable_name='messages'),
    ]
)

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class AgentGraph(StateGraph):
    def chatbot(self, state: AgentState):
        chain = prompt | self.llm
        message = chain.invoke({'messages': state['messages']})
        return {'messages': [message]}
    
    def __init__(self, llm, tools):
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
        
        memory = MemorySaver()
        self.graph = self.compile(
            checkpointer=memory,
        )
