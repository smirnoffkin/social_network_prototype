import pytest
from fastapi import status
from httpx import AsyncClient

from app.db.postgres.models import Base
from tests.conftest import sync_engine

# first artificially populate the database with users


@pytest.mark.parametrize("user", [
    ({
        "username": "new_user",
        "first_name": "Lex",
        "last_name": "Fridman",
        "email": "user@example.com",
        "password": "123456789",
    }),
    ({
        "username": "pepe",
        "first_name": "Pepe",
        "last_name": "King",
        "email": "pepe@example.com",
        "password": "pepe`s hashed password",
    }),
    ({
        "username": "auto",
        "first_name": "FastAPI",
        "last_name": "Fun",
        "email": "google@example.com",
        "password": "very_difficult_password",
    })
])
async def test_create_user_in_database(client: AsyncClient, user: dict):
    await client.post("/user/registration", json=user)


@pytest.mark.parametrize("login_data", [
    ({"email": "user@example.com", "password": "123456789"}),
    ({"email": "pepe@example.com", "password": "pepe`s hashed password"}),
    ({"email": "google@example.com", "password": "very_difficult_password"})
])
async def test_login_for_access_token(client: AsyncClient, login_data: dict):
    res = await client.post("/auth/login", data={
            "username": login_data["email"],
            "password": login_data["password"]
        }
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["token_type"] == "bearer"


@pytest.mark.parametrize("data", [
    ({"email": "not_a_user@example.com", "password": "123456789"}),
    ({"email": "pepe@example.com", "password": "Not a pepe`s password"}),
    ({"email": "apple@example.com", "password": "incorrect password"})
])
async def test_login_with_invalid_credentials(client: AsyncClient, data: dict):
    res = await client.post("/auth/login", data={
            "username": data["email"],
            "password": data["password"]
        }
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Incorrect email or password"}


async def test_delete_user_in_database():
    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
