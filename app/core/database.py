from motor.motor_asyncio import AsyncIOMotorClient
from app.core.settings import settings

db_client = AsyncIOMotorClient(settings.database_uri)
db = db_client[settings.database_name]

chats_collection = db['chats']
chats_cp_collection = db['chats_cp']

notes_collection = db['notes']

users_collection = db['users']
