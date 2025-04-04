from pydantic import BaseModel


class ChatResponseRequest(BaseModel):
    message: str
    context: str = ''
