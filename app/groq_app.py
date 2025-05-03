from typing import List
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_text_splitters import RecursiveCharacterTextSplitter
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    AIMessageChunk,
)
from langchain_groq import ChatGroq
from langgraph.checkpoint.base import BaseCheckpointSaver
from app.agent_graph import AgentGraph
from app.core.settings import settings
from app.core.chat_saver import ChatSaver
from app.models.chat import ChatModel
from app.models.note import NoteModel
from app.models.query_request import ChatResponseRequest
from app.models.update_title_request import UpdateChatRequest
from app.tools.notes import NotesTool
from app.core.database import chats_collection, notes_collection
from app.utils.base_checkpoint_saver import aget_messages

embedding_model = HuggingFaceEmbeddings(
    model_name='nomic-ai/nomic-embed-text-v2-moe',
    model_kwargs={
        'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'trust_remote_code': True,
    },
    encode_kwargs={'normalize_embeddings': True},
)

vectorstore = Chroma(
    collection_name='notes',
    embedding_function=embedding_model,
    persist_directory='./chroma_db'
)

llm = ChatGroq(
    model='llama-3.1-8b-instant',
    api_key=settings.LLM_API_KEY,
    temperature=0.25,
    streaming=True,
)

app = FastAPI()

@app.get('/')
def get_root():
    return {'message': 'Hello, FastAPI!'}

@app.get('/test')
async def test():
    try:
        pass
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)
    return {'message': 'success'}

async def generate_response(message: str, id: ObjectId):
    chat_id = str(id)

    tools = [NotesTool(vectorstore=vectorstore)]
    llm_with_tools = llm.bind_tools(
        tools=tools,
    )
    async with ChatSaver.create() as memory:
        memory: BaseCheckpointSaver
        graph = AgentGraph.create_graph(llm_with_tools, tools, memory)
        config = {'configurable': {'thread_id': chat_id}}
        result = graph.astream(
            input={
                'messages': [HumanMessage(message)]
            },
            config=config,
            stream_mode='messages',
        )

        chunks = []

        async for chunk in result:
            # print(f'chunk: {chunk}')
            chunk = chunk[0]
            content = chunk.content
            if isinstance(chunk, AIMessageChunk):
                chunks.append(content)
                yield content
            else:
                print(f'other chunk: {type(chunk)}')

    response = ''.join(chunks)

    print(f'final response: {response}')
    
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

    return StreamingResponse(generate_response(request.message, id), media_type='text/plain')

@app.post('/chats')
async def create_chat(chat: ChatModel):
    chat_dict = chat.model_dump(by_alias=True, exclude=['id'])
    result = await chats_collection.insert_one(chat_dict)
    return {'id': str(result.inserted_id)}

@app.get('/chats/{id}', response_model=ChatModel)
async def get_chat(id: str):
    try:
        id = ObjectId(id)
    except Exception as e:
        raise HTTPException(status_code=400, detail='Invalid chat ID') from e

    chat = await chats_collection.find_one({'_id': id})
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    chat['_id'] = str(chat['_id'])

    async with ChatSaver.create() as memory:
        memory: BaseCheckpointSaver
        config = {'configurable': {'thread_id': str(id)}}
        chat_history = await aget_messages(memory, config)
        messages = []
        for message in chat_history:
            message_object = None
            if isinstance(message, HumanMessage):
                message_object = {
                    'data': message.content,
                    'role': 'user'
                }
            elif isinstance(message, AIMessage):
                message_object = {
                    'data': message.content,
                    'role': 'bot'
                }

            if message_object:
                messages.append(message_object)

        chat['messages'] = messages
        print('messages assigned to chat')
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
    except Exception as e:
        raise HTTPException(status_code=400, detail='Invalid chat ID') from e

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
    except Exception as e:
        raise HTTPException(status_code=400, detail='Invalid chat ID') from e

    result = await chats_collection.delete_one({'_id': id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Chat not found')

    return {'message': 'Chat deleted successfully'}

@app.post('/notes')
async def create_note(note: NoteModel):
    note_dict = note.model_dump(by_alias=True, exclude=['id'])

    try:
        result = await notes_collection.insert_one(note_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail='Something went wrong') from e

    return JSONResponse(
        content={'id': str(result.inserted_id)},
        status_code=201,
    )

@app.put('/notes/{id}')
async def update_note(id: str, note: NoteModel):
    try:
        obj_id = ObjectId(id)
    except Exception as e:
        raise HTTPException(status_code=400, detail='Invalid note ID') from e

    result = await notes_collection.update_one(
        {'_id': obj_id},
        {'$set': {'title': note.title, 'content': note.content}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Note not found')

    return {'message': 'Note updated successfully'}

@app.post('/notes/{id}/embed')
async def update_note_embeddings(id: str, note: NoteModel):
    try:
        obj_id = ObjectId(id)
    except Exception as e:
        raise HTTPException(status_code=400, detail='Invalid note ID') from e
    
    search_result = await notes_collection.find_one({'_id': obj_id})
    
    if not search_result:
        raise HTTPException(status_code=404, detail='Note not found')
    
    text = note.model_dump_json(exclude=['id'])

    await vectorstore.adelete(
        where={'note_id': id}
    )

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=0, keep_separator='end')
    chunks = text_splitter.split_text(text)

    try:
        await vectorstore.aadd_texts(
            texts=chunks,
            metadatas=[{'note_id': id, 'index': i} for i in range(len(chunks))],
        )
        return {'message': 'Note embeddings updated successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail='Something went wrong')
