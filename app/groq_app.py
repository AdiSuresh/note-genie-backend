from typing import List
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    AIMessageChunk,
)
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
from app.agent_graph import AgentGraph
from app.document_loader import DocumentLoader
from app.models.chat import ChatModel
from app.models.query_request import ChatResponseRequest
from app.models.update_title_request import UpdateChatRequest
from app.tools.notes import NotesTool

load_dotenv()

# DB setup
MONGO_URI = os.getenv('MONGO_URI')
client = AsyncIOMotorClient(MONGO_URI)
db = client['note_genie_db']
chats_collection = db['chats']

embedding_model = HuggingFaceEmbeddings(
    model_name='nomic-ai/nomic-embed-text-v2-moe',
    model_kwargs={
        'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'trust_remote_code': True,
    },
    encode_kwargs={'normalize_embeddings': True},
)

# vectorstore = Chroma(
#     collection_name='notes',
#     embedding_function=embedding_model,
#     persist_directory='chroma_db'
# )

vectorstore = Chroma.from_texts(
    texts=DocumentLoader().load('document.txt'),
    collection_name='document',
    embedding=embedding_model,
)

notes_tool = NotesTool(
    vectorstore=vectorstore
)

tools = [notes_tool]

llm = ChatGroq(
    model='llama-3.1-8b-instant',
    streaming=True,
)

llm_with_tools = llm.bind_tools(
    tools=tools,
)

agent = AgentGraph(
    llm=llm_with_tools,
    tools=tools,
)

app = FastAPI()

@app.get('/')
def get_root():
    return {'message': 'Hello, FastAPI!'}

async def create_message_list(chat_id: str):
    chat_id = ObjectId(chat_id)

    chat = await get_chat(id=chat_id)
    message_objects = chat['messages']

    is_user = True
    messages: list[BaseMessage] = [
        SystemMessage(
            'You are a helpful assistant that makes use of the notes tool for responding to user\'s queries.',
        ),
    ]

    for object in message_objects:
        content = object['data']
        role = object['role']

        match (role, is_user):
            case ('user', True):
                is_user = False
                messages.append(HumanMessage(content=content))
            case ('bot', False):
                is_user = True
                messages.append(AIMessage(content=content))
            case _:
                raise HTTPException(status_code=500, detail='Malformed message list')
    
    return messages

@app.get('/test')
async def test():
    try:
        id = '67e17812951a0032e4784126'
        await create_message_list(chat_id=id)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    return {'message': 'success'}

async def generate_response(request: ChatResponseRequest, id: ObjectId):
    chat_id = str(id)
    messages = await create_message_list(chat_id=chat_id)

    config = {'configurable': {'thread_id': '1'}}

    print(f'user input: {messages[-1]}')
    result = agent.graph.astream(
        {
            'messages': [messages[-1]]
        },
        config=config,
        stream_mode='messages',
    )
    
    chunks = []

    async for chunk in result:
        # print(f'chunk: {chunk}')
        message = chunk[0]
        content = message.content
        if isinstance(message, AIMessageChunk):
            chunks.append(content)
            yield content
    
    response = ''.join(chunks)

    print(f'final response: {response}')
    
    await chats_collection.update_one(
        {'_id': id},
        {'$push': {'messages': {'role': 'bot', 'data': response}}}
    )
    
    print('finished')

@app.post('/chats/{id}/respond')
async def create_chat_response(id: str, request: ChatResponseRequest):
    try:
        id = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail='Invalid chat ID')

    chat = chats_collection.find_one({'_id': id,})
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')
    
    result = await chats_collection.update_one(
        {'_id': id},
        {'$push': {'messages': {'role': 'user', 'data': request.message}}}
    )

    print(f'message appended: {result}')

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
    chats = await chats_collection.find(None, {'messages': 0}).to_list(None)
    for chat in chats:
        chat['_id'] = str(chat['_id'])
    return chats

@app.put('/chats/{id}')
async def update_chat_title(id: str, chat: UpdateChatRequest):
    try:
        id = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail='Invalid chat ID')

    result = await chats_collection.update_one(
        {'_id': id},
        {'$set': {'title': chat.title}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Chat not found')

    return {'message': 'Title updated successfully'}

@app.delete('/chats/{id}')
async def delete_chat(id: str):
    try:
        id = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail='Invalid chat ID')

    result = await chats_collection.delete_one({'_id': id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Chat not found')

    return {'message': 'Chat deleted successfully'}
