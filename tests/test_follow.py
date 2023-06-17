import pytest
from fastapi import status
from httpx import AsyncClient

from app.db.postgres.models import Base
from tests.conftest import create_test_auth_headers_for_user, sync_engine

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


@pytest.mark.parametrize("follower_email, username_to_follow", [
    ("user@example.com", "pepe"),
    ("pepe@example.com", "auto"),
    ("google@example.com", "pepe"),
])
async def test_follow_user(client: AsyncClient, follower_email: str, username_to_follow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.post(f"/follow/{username_to_follow}", headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json() == f"You are following to the user {username_to_follow}"


@pytest.mark.parametrize("follower_email, username_to_follow", [
    ("user@example.com", "pepe"),
    ("pepe@example.com", "auto"),
    ("google@example.com", "pepe"),
])
async def test_follow_user_when_follow_already_exists(client: AsyncClient, follower_email: str, username_to_follow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.post(f"/follow/{username_to_follow}", headers=headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.json() == {"detail": f"You are already following user {username_to_follow}"}


@pytest.mark.parametrize("follower_email, username_to_follow", [
    ("user@example.com", "einstein"),
    ("pepe@example.com", "leonardo"),
    ("google@example.com", "jonny"),
])
async def test_follow_user_who_not_exists(client: AsyncClient, follower_email: str, username_to_follow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.post(f"/follow/{username_to_follow}", headers=headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"User with username {username_to_follow} not found"}


@pytest.mark.parametrize("follower_email, username_to_follow", [
    ("user@example.com", "new_user"),
    ("pepe@example.com", "pepe"),
    ("google@example.com", "auto"),
])
async def test_follow_for_yourself(client: AsyncClient, follower_email: str, username_to_follow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.post(f"/follow/{username_to_follow}", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.json() == {"detail": "You cannot subscribe to yourself"}


@pytest.mark.parametrize("username_to_follow", [
    ("pepe"),
    ("auto"),
    ("pepe"),
])
async def test_follow_user_not_authenticated(client: AsyncClient, username_to_follow: str):
    res = await client.post(f"/follow/{username_to_follow}")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("follower_email, username_to_follow", [
    ("user@example.com", "pepe"),
    ("pepe@example.com", "auto"),
    ("google@example.com", "pepe"),
])
async def test_get_status_of_follow_when_follow_exists(client: AsyncClient, follower_email: str, username_to_follow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.get(f"/follow/{username_to_follow}", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == f"You are following to the user {username_to_follow}"


@pytest.mark.parametrize("follower_email, username_to_follow", [
    ("user@example.com", "auto"),
    ("pepe@example.com", "new_user"),
    ("google@example.com", "new_user"),
])
async def test_get_status_of_follow_when_follow_not_exists(client: AsyncClient, follower_email: str, username_to_follow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.get(f"/follow/{username_to_follow}", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == f"You are not following user {username_to_follow}"


@pytest.mark.parametrize("follower_email, username_to_follow", [
    ("user@example.com", "einstein"),
    ("pepe@example.com", "leonardo"),
    ("google@example.com", "jonny"),
])
async def test_get_status_of_follow_user_who_not_exists(client: AsyncClient, follower_email: str, username_to_follow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.get(f"/follow/{username_to_follow}", headers=headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"User with username {username_to_follow} not found"}


@pytest.mark.parametrize("username_to_follow", [
    ("pepe"),
    ("auto"),
    ("pepe"),
])
async def test_get_status_of_follow_not_authenticated(client: AsyncClient, username_to_follow: str):
    res = await client.get(f"/follow/{username_to_follow}")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("email", [
    ("user@example.com"),
    ("pepe@example.com"),
    ("google@example.com"),
])
async def test_get_list_followers(client: AsyncClient, email: str):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.get("/follow/list/followers", headers=headers)
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("email", [
    ("user@example.com"),
    ("pepe@example.com"),
    ("google@example.com"),
])
async def test_get_list_following(client: AsyncClient, email: str):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.get("/follow/list/following", headers=headers)
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("follower_email, username_to_unfollow", [
    ("user@example.com", "pepe"),
    ("pepe@example.com", "auto"),
    ("google@example.com", "pepe"),
])
async def test_unfollow_user(client: AsyncClient, follower_email: str, username_to_unfollow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.delete(f"/follow/{username_to_unfollow}", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == f"You are unfollowing user {username_to_unfollow}"


@pytest.mark.parametrize("follower_email, username_to_unfollow", [
    ("user@example.com", "pepe"),
    ("pepe@example.com", "auto"),
    ("google@example.com", "pepe"),
])
async def test_unfollow_user_when_follow_not_exists(client: AsyncClient, follower_email: str, username_to_unfollow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.delete(f"/follow/{username_to_unfollow}", headers=headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"You are not following user {username_to_unfollow}"}


@pytest.mark.parametrize("follower_email, username_to_unfollow", [
    ("user@example.com", "einstein"),
    ("pepe@example.com", "leonardo"),
    ("google@example.com", "jonny"),
])
async def test_unfollow_user_who_not_exists(client: AsyncClient, follower_email: str, username_to_unfollow: str):
    headers = await create_test_auth_headers_for_user(follower_email)
    res = await client.get(f"/follow/{username_to_unfollow}", headers=headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"User with username {username_to_unfollow} not found"}


@pytest.mark.parametrize("username_to_unfollow", [
    ("pepe"),
    ("auto"),
    ("pepe"),
])
async def test_unfollow_user_not_authenticated(client: AsyncClient, username_to_unfollow: str):
    res = await client.get(f"/follow/{username_to_unfollow}")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Not authenticated"}


async def test_delete_user_in_database():
    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
