from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'Note Genie Backend'
    database_name: str
    database_uri: str
    llm_api_key: str

    jwt_secret: str
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60 * 24 * 10

    class Config:
        env_file = '.env'
        case_sensitive = False

settings = Settings()
