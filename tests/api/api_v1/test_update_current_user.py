from starlette.testclient import TestClient
from app.main import app

user = {
    "user": {
        "email": "user@example.com",
        "password": "string",
        "username": "string"
    }
}

client = TestClient(app)


def test_update_current_user():
    response = client.post("/api/users", user)
    assert response.status_code == 200
    assert response.json() == {"name": "Fighters"}
