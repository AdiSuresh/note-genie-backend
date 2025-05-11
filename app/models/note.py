from typing import Optional
from pydantic import BaseModel, Field
from app.types.py_object_id import PyObjectId


class NoteModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias='_id', default=None)
    user_id: Optional[str] = None
    title: str = 'Untitled'
    content: str = ''
