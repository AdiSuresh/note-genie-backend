from typing import Optional
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage

async def aget_messages(memory: BaseCheckpointSaver, config: RunnableConfig):
    return _extract_messages(await memory.aget(config))

def _extract_messages(checkpoint: Optional[Checkpoint]):
    if not checkpoint:
        return []

    if not (channel_values := checkpoint['channel_values']):
        return []

    if not (chat_history := channel_values['messages']):
        return []

    result = []
    for message in chat_history:
        if isinstance(message, HumanMessage):
            result.append(message)
        elif isinstance(message, AIMessage):
            if result and isinstance(last_message:= result[-1], AIMessage):
                result[-1] = AIMessage(last_message.content + message.content)
                continue
            result.append(message)

    return result
