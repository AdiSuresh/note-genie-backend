from typing import List
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
from app.models.chat import ChatModel
from app.models.query_request import QueryRequest

load_dotenv()

app = FastAPI()


# DB setup
MONGO_URI = os.getenv('MONGO_URI')
client = AsyncIOMotorClient(MONGO_URI)
db = client['note_genie_db']
chat_collection = db['chats']


# LLM setup
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
