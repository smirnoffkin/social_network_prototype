import pytest
from httpx import AsyncClient


@pytest.mark.parametrize("expected", [
    ({"Social Network Project": "This is the root of the project!"})
])
async def test_root(client: AsyncClient, expected: dict):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == expected
