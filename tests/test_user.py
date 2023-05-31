import pytest
from fastapi import status
from httpx import AsyncClient

from tests.conftest import create_test_auth_headers_for_user


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
async def test_create_user(client: AsyncClient, user: dict):
    res = await client.post("/user/registration", json=user)
    data = res.json()
    assert res.status_code == status.HTTP_201_CREATED
    assert data["username"] == user["username"]
    assert data["first_name"] == user["first_name"]
    assert data["last_name"] == user["last_name"]
    assert data["email"] == user["email"]
    assert data["is_active"] is True


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
async def test_create_user_bad_request(client: AsyncClient, user: dict):
    res = await client.post("/user/registration", json=user)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.json() == {"detail": "This username or email is already in use"}


@pytest.mark.parametrize("user", [
    ({
        "username": "new_user",
        "first_name": "Lex",
        "last_name": "Fridman",
        "email": "user@example.com",
        "password": "1234",
    }),
    ({
        "username": "pepe",
        "first_name": "Pepe",
        "last_name": "King",
        "email": "pepe@example.com",
        "password": "pepe",
    }),
    ({
        "username": "auto",
        "first_name": "FastAPI",
        "last_name": "Fun",
        "email": "google@example.com",
        "password": "google",
    })
])
async def test_create_user_with_short_password(
    client: AsyncClient,
    user: dict
):
    res = await client.post("/user/registration", json=user)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert res.json() == {
        "detail": [
            {
                "ctx": {"limit_value": 8},
                "loc": ["body", "password"],
                "msg": "ensure this value has at least 8 characters",
                "type": "value_error.any_str.min_length",
            }
        ]
    }


@pytest.mark.parametrize("user", [
    ({"password": "123456789"}),
    ({"username": "pepe", "last_name": "King", "email": "pepe@example.com"}),
    ({"email": "google@example.com", "password": "very_difficult_password"}),
])
async def test_create_user_with_missing_fields(
    client: AsyncClient,
    user: dict
):
    res = await client.post("/user/registration", json=user)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("expected_user", [
    ({
        "username": "new_user",
        "first_name": "Lex",
        "last_name": "Fridman",
        "email": "user@example.com",
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
    }),
])
async def test_get_user(client: AsyncClient, expected_user: dict):
    res = await client.get(f"/user/{expected_user['username']}")
    data = res.json()
    assert res.status_code == status.HTTP_200_OK
    assert data["username"] == expected_user["username"]
    assert data["first_name"] == expected_user["first_name"]
    assert data["last_name"] == expected_user["last_name"]
    assert data["email"] == expected_user["email"]
    assert data["is_active"] is True


@pytest.mark.parametrize("username", [
    ("Leo Tolstoy"),
    ("bad_pepe"),
    ("abracadabra")
])
async def test_get_user_not_exists(client: AsyncClient, username: str):
    res = await client.get(f"/user/{username}")
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == (
        {"detail": f"User with username {username} not found."}
    )


@pytest.mark.parametrize("user", [
    ({
        "username": "mark",
        "first_name": "Mark",
        "last_name": "Twain",
        "email": "user@example.com",
    }),
    ({
        "username": "new_pepe",
        "first_name": "Pepe",
        "last_name": "Lord of the Rings",
        "email": "pepe@example.com",
    }),
    ({
        "username": "google",
        "first_name": "Google",
        "last_name": "Dev",
        "email": "google@example.com",
    }),
])
async def test_update_user(client: AsyncClient, user: dict):
    headers = await create_test_auth_headers_for_user(user["email"])
    res = await client.put("/user/update_profile", json=user, headers=headers)
    data = res.json()
    assert res.status_code == status.HTTP_200_OK
    assert data["username"] == user["username"]
    assert data["first_name"] == user["first_name"]
    assert data["last_name"] == user["last_name"]
    assert data["email"] == user["email"]
    assert data["is_active"] is True


@pytest.mark.parametrize("user", [
    ({
        "username": "hugo",
        "first_name": "Victor",
        "last_name": "Hugo",
        "email": "victorhugo@example.com",
    }),
    ({
        "username": "imposter",
        "first_name": "Unknown",
        "last_name": "User",
        "email": "imposter@example.com",
    }),
    ({
        "username": "apple",
        "first_name": "Apple",
        "last_name": "Dev",
        "email": "apple@example.com",
    }),
])
async def test_update_user_with_invalid_credentials(
    client: AsyncClient,
    user: dict
):
    headers = await create_test_auth_headers_for_user(user["email"])
    res = await client.put("/user/update_profile", json=user, headers=headers)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Could not validate credentials"}


@pytest.mark.parametrize("user", [
    ({
        "username": "updated_user",
        "first_name": "Mark",
        "last_name": "Twain",
        "email": "user@example.com",
    }),
    ({
        "username": "new_pepe",
        "first_name": "Pepe",
        "last_name": "Lord of the Rings",
        "email": "pepe@example.com",
    }),
    ({
        "username": "google",
        "first_name": "Google",
        "last_name": "Dev",
        "email": "google@example.com",
    }),
])
async def test_update_user_not_authenticated(client: AsyncClient, user: dict):
    res = await client.put("/user/update_profile", json=user)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("email", [
    ("user@example.com"),
    ("pepe@example.com"),
    ("google@example.com"),
])
async def test_delete_user(client: AsyncClient, email: str):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.delete(f"/user/delete_account/{email}", headers=headers)
    data = res.json()
    assert res.status_code == status.HTTP_200_OK
    assert data["email"] == email
    assert data["is_active"] is False


@pytest.mark.parametrize("email", [
    ("mark@example.com"),
    ("unknown@example.com"),
    ("apple@example.com"),
])
async def test_delete_user_with_invalid_credentials(
    client: AsyncClient,
    email: str
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.delete(f"/user/delete_account/{email}", headers=headers)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Could not validate credentials"}
