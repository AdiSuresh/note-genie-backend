from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.chat_message import ChatMessageModel
from app.types.py_object_id import PyObjectId


class ChatModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias='_id', default=None)
    user_id: Optional[str] = None
    title: str = 'Untitled'
    messages: List[ChatMessageModel] = []
