from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'Note Genie Backend'
    DATABASE_NAME: str
    DATABASE_URI: str
    LLM_API_KEY: str

    class Config:
        env_file = '.env'

settings = Settings()
