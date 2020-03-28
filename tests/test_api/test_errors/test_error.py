import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import HTTP_404_NOT_FOUND

pytestmark = pytest.mark.asyncio


async def test_frw_validation_error_format(app: FastAPI):
    client = AsyncClient(base_url="http://testserver", app=app)
    response = await client.get("/wrong_path/asd")
    assert response.status_code == HTTP_404_NOT_FOUND

    error_data = response.json()
    assert "errors" in error_data
