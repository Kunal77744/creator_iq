import os
from pathlib import Path

from dotenv import load_dotenv

# Load project-root .env.local (written by `neon init` / `neon deploy`) and backend .env
_ROOT_ENV_LOCAL = Path(__file__).resolve().parent.parent.parent / ".env.local"
if _ROOT_ENV_LOCAL.exists():
    load_dotenv(_ROOT_ENV_LOCAL)
load_dotenv()


def _normalize_pg_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


DATABASE_URL = _normalize_pg_url(
    os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/creatoriq")
)
DATABASE_URL_UNPOOLED = _normalize_pg_url(os.getenv("DATABASE_URL_UNPOOLED", DATABASE_URL))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
_IS_PROD = (
    os.getenv("ENV", "").lower() == "production"
    or os.getenv("VERCEL_ENV", "").lower() == "production"
    or os.getenv("VERCEL", "") == "1"
)
if _IS_PROD and (
    SECRET_KEY in {"dev-only-secret-change-me", "change-this-to-a-long-random-string"}
    or len(SECRET_KEY) < 16
):
    raise RuntimeError("SECRET_KEY must be set to a strong secret (16+ chars) in production.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
SEED_DEMO_USERS = os.getenv("SEED_DEMO_USERS", "false").lower() == "true"
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))  # tests lower this for speed
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "360"))  # auto re-sync of connected YouTube channels (0 = off)

LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID', '')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET', '')
LINKEDIN_REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8000/api/auth/linkedin/callback')
