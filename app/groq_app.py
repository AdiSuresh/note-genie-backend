from typing import List
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
from app.models.chat import ChatModel
from app.models.query_request import ChatResponseRequest

load_dotenv()

app = FastAPI()


# DB setup
MONGO_URI = os.getenv('MONGO_URI')
client = AsyncIOMotorClient(MONGO_URI)
db = client['note_genie_db']
chats_collection = db['chats']


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

async def generate_response(request: ChatResponseRequest, id: ObjectId):
    result = chain.astream({
        'context': request.context,
        'question': request.question
    })
    
    chunks = []

    async for chunk in result:
        chunks.append(chunk.content)
        yield chunk.content
    
    response = ''.join(chunks)
    
    await chats_collection.update_one(
        {'_id': id},
        {'$push': {'messages': {'role': 'bot', 'data': response}}}
    )
    
    print('finished')

@app.post('/chats/{id}/respond')
async def post_query(id: str, request: ChatResponseRequest):
    try:
        id = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail='Invalid chat ID')

    chat = chats_collection.find_one({'_id': id,})
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')
    
    await chats_collection.update_one(
        {'_id': id},
        {'$push': {'messages': {'role': 'user', 'data': request.question}}}
    )

    return StreamingResponse(generate_response(request, id), media_type='text/plain')

@app.post('/chats')
async def create_chat(chat: ChatModel):
    chat_dict = chat.model_dump(by_alias=True, exclude=['id'])
    result = await chats_collection.insert_one(chat_dict)
    return {'id': str(result.inserted_id)}

@app.get('/chats/{id}', response_model=ChatModel)
async def get_chat(id: str):
    try:
        id = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail='Invalid chat ID')
    
    chat = await chats_collection.find_one({'_id': id})
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    chat['_id'] = str(chat['_id'])
    return chat

@app.get('/chats', response_model=List[ChatModel])
async def get_chats():
    chats = await chats_collection.find().to_list()
    for chat in chats:
        chat['_id'] = str(chat['_id'])
        chat.pop('messages')
    return chats
