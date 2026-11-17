import os
from pathlib import Path

# Safe dotenv loading without hard dependency
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
    except ImportError:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Supabase Free Cloud Database
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip()
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "").strip()
    
    # LLM APIs (Free Tier)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()

    # Capstone BGE Embedding API
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "https://103.42.50.41:1035/v1").strip()
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "bge-small-en-v1.5").strip()
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "").strip()
    EMBEDDING_CA_CERT_PATH: str = str(
        (Path(__file__).resolve().parent.parent / os.getenv("EMBEDDING_CA_CERT_PATH", "certs/vm02-ca.crt"))
        if not os.path.isabs(os.getenv("EMBEDDING_CA_CERT_PATH", "certs/vm02-ca.crt"))
        else Path(os.getenv("EMBEDDING_CA_CERT_PATH", "certs/vm02-ca.crt"))
    )

    # Capstone Qwen3-8B Inference API (VM07)
    QWEN_BASE_URL: str = os.getenv("QWEN_BASE_URL", "https://103.42.50.41:1031/v1").strip()
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "Qwen/Qwen3-8B").strip()
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "").strip()
    QWEN_CA_CERT_PATH: str = str(
        (Path(__file__).resolve().parent.parent / os.getenv("QWEN_CA_CERT_PATH", "certs/vm07-ca.crt"))
        if not os.path.isabs(os.getenv("QWEN_CA_CERT_PATH", "certs/vm07-ca.crt"))
        else Path(os.getenv("QWEN_CA_CERT_PATH", "certs/vm07-ca.crt"))
    )

settings = Settings()

