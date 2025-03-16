from pydantic import BaseModel, Field

class UpdateChatRequest(BaseModel):
    title: str = Field(..., min_length=1, description='Title cannot be empty')
