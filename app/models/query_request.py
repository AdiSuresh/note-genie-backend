from pydantic import BaseModel


class ChatResponseRequest(BaseModel):
    question: str
    context: str = ''
