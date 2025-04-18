from os import getenv
from dotenv import load_dotenv

load_dotenv()

BASE_URL = getenv("BASE_URL", "http://localhost:8000")

DATABASE_USER = getenv("POSTGRES_USER", "postgres")
DATABASE_PASSWORD = getenv("POSTGRES_PASSWORD", "postgres")
DATABASE_NAME = getenv("POSTGRES_DB", "postgres")
DATABASE_HOST = getenv("POSTGRES_HOST", "localhost")
DATABASE_PORT = getenv("POSTGRES_PORT", "5432")
DATABASE_URL = f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
SYNC_DATABASE_URL = f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"


REDIS_HOST = getenv("REDIS_HOST", "localhost")
REDIS_PORT = getenv("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CACHE_DEFAULT_TIMEOUT = 60 * 60 * 24  # 1 day

PROMETHEUS_HOST = getenv("PROMETHEUS_HOST", "http://localhost")
PROMETHEUS_PORT = getenv("PROMETHEUS_PORT", "9090")
PROMETHEUS_URL = f"{PROMETHEUS_HOST}:{PROMETHEUS_PORT}"
