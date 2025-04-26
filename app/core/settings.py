from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'Note Genie Backend'
    MONGO_URI = str
    DB_NAME = str

    class Config:
        env_file = '.env'

settings = Settings()
