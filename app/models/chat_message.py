import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MessengerType(str, Enum):
    user = 'user'
    bot = 'bot'

class ChatMessageModel(BaseModel):
    data: str
    role: MessengerType
    timestamp: datetime.datetime = Field(
        default_factory=lambda _: datetime.datetime.now(
            datetime.timezone.utc
        )
    )
