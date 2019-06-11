from pytest import fixture
from starlette.config import environ
from starlette.testclient import TestClient
from app.db.mongodb import get_database
from app.core.config import database_name, users_collection_name


@fixture(scope="session")
def test_user():
    return {
        "user": {
            "email": "user1@example.com",
            "password": "string1",
            "username": "string1"
        }
    }


@fixture(scope="session")
def test_client(test_user):
    from app.main import app
    with TestClient(app) as test_client:
        yield test_client

    import asyncio
    db = asyncio.run(get_database())
    db[database_name][users_collection_name].delete_one({"username": test_user["user"]["username"]})


# This line would raise an error if we use it after 'settings' has been imported.
environ['TESTING'] = 'TRUE'
