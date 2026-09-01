from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Company RAG Chatbot"
    QDRANT_URL: str = "memory"
    OPENAI_API_KEY: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = ""
    MICROSOFT_USER_EMAIL: str = ""
    # other configurations
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
