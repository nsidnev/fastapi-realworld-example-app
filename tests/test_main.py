from starlette.testclient import TestClient


def test_read_connect_to_mongo():
    with TestClient(app) as client:
        assert client
