import json
from langchain.tools import BaseTool
from langchain.vectorstores import VectorStore
from typing import Type
from pydantic import BaseModel, Field, PrivateAttr

class NotesToolSearchInput(BaseModel):
    query: str = Field(..., description='The query to search for notes')

class NotesTool(BaseTool):
    name: str = 'notes_tool'
    description: str = 'Searches for potentially relevant notes based on a query'
    args_schema: Type[BaseModel] = NotesToolSearchInput

    _vectorstore: VectorStore = PrivateAttr()
    _k: int = PrivateAttr(default=5)
    
    def __init__(self, vectorstore: VectorStore, k: int = 5):
        super().__init__()
        self._vectorstore = vectorstore
        self._k = k

    def _run(self, query: str) -> str:
        raise NotImplementedError()

    async def _arun(self, query: str) -> str:
        """Run a similarity search and return the top-k potentially relevant notes."""
        
        search_results = await self._vectorstore.asimilarity_search(query, k=self._k)
        print('_arun was called')
        print(f'query: {query}')
        result = {
            'tool_status': 'active',
        }
        print(f'found {len(search_results)} results')
        if not search_results:
            result['search_results'] = f'No search results for "{query}"'
        else:
            result['search_results'] = '\n\n'.join([doc.page_content for doc in search_results])
        return json.dumps(result)
