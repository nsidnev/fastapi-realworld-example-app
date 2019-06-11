

def test_update_current_user(test_client, test_user):
    response = test_client.post("/api/users", json=test_user)
    assert response.status_code == 201
    assert response.json()["user"]["username"] == test_user["user"]["username"]
