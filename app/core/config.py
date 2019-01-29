from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, DatabaseURL, Secret

API_V1_STR = "/api"

JWT_TOKEN_PREFIX = "Token"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # one week

config = Config(".env")

PROJECT_NAME = config("PROJECT_NAME")
SECRET_KEY = config("SECRET_KEY", cast=Secret)
DATABASE_URL = config("DATABASE_URL", cast=DatabaseURL)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=CommaSeparatedStrings, default=None)
