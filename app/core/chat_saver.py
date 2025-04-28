from langgraph.checkpoint.mongodb import AsyncMongoDBSaver
from app.core.settings import settings


class ChatSaver():
    @classmethod
    def create(cls) -> AsyncMongoDBSaver:
        return AsyncMongoDBSaver.from_conn_string(
            settings.DATABASE_URI,
            settings.DATABASE_NAME,
            'chats_cp',
        )
