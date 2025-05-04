from langgraph.checkpoint.mongodb import AsyncMongoDBSaver
from app.core.settings import settings


class ChatSaver():
    @classmethod
    def create(cls) -> AsyncMongoDBSaver:
        return AsyncMongoDBSaver.from_conn_string(
            settings.database_uri,
            settings.database_name,
            'chats_cp',
        )
