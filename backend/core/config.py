import os
from pydantic_settings import BaseSettings

# Manual parsing of .env to bypass parent process env variable override
groq_key_val = ""
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                val = line.split("=", 1)[1].strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                groq_key_val = val

if groq_key_val:
    os.environ["GROQ_API_KEY"] = groq_key_val
elif os.environ.get("GROQ_API_KEY") == "your_groq_key_here":
    del os.environ["GROQ_API_KEY"]


class Settings(BaseSettings):
    groq_api_key: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    collection_name: str = "placementbrain"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    redis_url: str = "redis://redis:6379"
    upload_dir: str = "/data/uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
