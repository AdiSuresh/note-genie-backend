import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from app.models.query_request import QueryRequest

load_dotenv()

app = FastAPI()

template = '''
You are a helpful assistant.

Here is the conversation history: {context}

Question: {question}

Answer:
'''

model = ChatGroq(model='llama-3.1-8b-instant')

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
        yield chunk.content

@app.post('/query')
async def post_query(request: QueryRequest):
    return StreamingResponse(generate_response(request), media_type='text/plain')
