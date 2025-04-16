from langchain.tools import BaseTool
from langchain.vectorstores import VectorStore
from typing import Type
from pydantic import BaseModel, Field, PrivateAttr

class NotesToolSearchInput(BaseModel):
    query: str = Field(..., description='The query to search for notes')

class NotesTool(BaseTool):
    name: str = 'notes_tool'
    description: str = 'Searches for relevant chunks of notes created by the user based on a query'
    args_schema: Type[BaseModel] = NotesToolSearchInput

    _vectorstore: VectorStore = PrivateAttr()
    _k: int = PrivateAttr(default=5)
    
    def __init__(self, vectorstore: VectorStore, k: int = 5):
        super().__init__()
        self._vectorstore = vectorstore
        self._k = k

    def _run(self, query: str) -> str:
        '''Run a similarity search and return the top-k relevant chunks.'''
        results = self._vectorstore.similarity_search(query, k=self._k)
        if not results:
            return 'No relevant data found.'
        return '\n\n'.join([doc.page_content for doc in results])

    async def _arun(self, query: str) -> str:
        '''Run a similarity search and return the top-k relevant chunks.'''
        results = await self._vectorstore.asimilarity_search(query, k=self._k)
        if not results:
            return 'No relevant data found.'
        return '\n\n'.join([doc.page_content for doc in results])
