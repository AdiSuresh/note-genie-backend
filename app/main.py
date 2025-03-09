from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from app.models.query_request import QueryRequest


app = FastAPI()

template = '''
You are a helpful assistant.

Here is the conversation history: {context}

Question: {question}

Answer:
'''
# 'deepseek-r1:1.5b'
model = OllamaLLM(model='llama3.2:1b')

prompt = ChatPromptTemplate.from_template(template=template)

chain = prompt | model

@app.get('/')
def get_root():
    return {'message': 'Hello, FastAPI!'}

async def generate_response(request: QueryRequest):
    result = chain.astream({
        'context': request.context,
        'question': request.question
    })

    async for chunk in result:
        yield chunk

@app.post('/query')
def post_query(request: QueryRequest):
    return StreamingResponse(generate_response(request), media_type='text/plain')
