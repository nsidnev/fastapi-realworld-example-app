import os

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, DatabaseURL, Secret

API_V1_STR = "/api"

JWT_TOKEN_PREFIX = "Token"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # one week

config = Config(".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")  # deploying without docker-compose
if not DATABASE_URL:
    POSTGRES_HOST = config("POSTGRES_HOST")
    POSTGRES_PORT = config("POSTGRES_PORT")
    POSTGRES_USER = config("POSTGRES_USER")
    POSTGRES_PASS = config("POSTGRES_PASSWORD")
    POSTGRES_NAME = config("POSTGRES_DB")
    MAX_CONNECTIONS_COUNT = config("MAX_CONNECTIONS_COUNT", default=10, cast=int)
    MIN_CONNECTIONS_COUNT = config("MIN_CONNECTIONS_COUNT", default=10, cast=int)

    DATABASE_URL = DatabaseURL(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_NAME}"
    )
    SECRET_KEY = config("SECRET_KEY", cast=Secret)
else:
    DATABASE_URL = DatabaseURL(DATABASE_URL)
    SECRET_KEY = os.getenv("SECRET_KEY")
    MAX_CONNECTIONS_COUNT = int(os.getenv("MAX_CONNECTIONS_COUNT", 10))
    MIN_CONNECTIONS_COUNT = int(os.getenv("MIN_CONNECTIONS_COUNT", 10))

PROJECT_NAME = config("PROJECT_NAME", default="FastAPI example application")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=CommaSeparatedStrings, default=None)
