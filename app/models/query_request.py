from pydantic import BaseModel


class ChatResponseRequest(BaseModel):
    id: str
    question: str
    context: str = ''
