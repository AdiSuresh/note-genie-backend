from motor.motor_asyncio import AsyncIOMotorClient
from app.core.settings import settings

db_client = AsyncIOMotorClient(settings.DATABASE_URI)
db = db_client[settings.DATABASE_NAME]

chats_collection = db['chats']
chats_cp_collection = db['chats_cp']

notes_collection = db['notes']
