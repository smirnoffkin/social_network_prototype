import pytest
from fastapi import status
from httpx import AsyncClient

from app.db.postgres.models import Base
from app.schemas.post import PostReaction
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


@pytest.mark.parametrize("email, post", [
    ("user@example.com", {
        "title": "First Post",
        "content": "This is my first post!"
    }),
    ("pepe@example.com", {
        "title": "Middle Post",
        "content": "Second Post. Middle of the history."
    }),
    ("google@example.com", {
        "title": "Last Post",
        "content": "This is my last post! End of the history.",
    })
])
async def test_create_post(client: AsyncClient, email: str, post: dict):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.post("/post/create", json=post, headers=headers)
    data = res.json()
    assert res.status_code == status.HTTP_201_CREATED
    assert data["title"] == post["title"]
    assert data["content"] == post["content"]
    assert data["is_published"] is True


@pytest.mark.parametrize("post", [
    ({
        "title": "First Post",
        "content": "This is my first post!"
    }),
    ({
        "title": "Middle Post",
        "content": "Second Post. Middle of the history."
    }),
    ({
        "title": "Last Post",
        "content": "This is my last post! End of the history.",
    })
])
async def test_create_post_not_authenticated(client: AsyncClient, post: dict):
    res = await client.post("/post/create", json=post)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("post", [
    ({
        "id": 1,
        "title": "First Post",
        "content": "This is my first post!"
    }),
    ({
        "id": 2,
        "title": "Middle Post",
        "content": "Second Post. Middle of the history.",
    }),
    ({
        "id": 3,
        "title": "Last Post",
        "content": "This is my last post! End of the history.",
    })
])
async def test_get_post(client: AsyncClient, post: dict):
    res = await client.get(f"/post/{id}?post_id={post['id']}")
    data = res.json()
    assert res.status_code == status.HTTP_200_OK
    assert data["id"] == post["id"]
    assert data["title"] == post["title"]
    assert data["content"] == post["content"]
    assert data["is_published"] is True


@pytest.mark.parametrize("post_id", [(4), (1000), (999999)])
async def test_get_post_not_exists(client: AsyncClient, post_id: int):
    res = await client.get(f"/post/{id}?post_id={post_id}")
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"Post with id {post_id} not found."}


@pytest.mark.parametrize("title", [
    ("First Post"),
    ("Middle Post"),
    ("Last Post")
])
async def test_get_all_posts_by_title(client: AsyncClient, title: str):
    res = await client.get(f"/post/posts/{title}")
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("email, post", [
    ("user@example.com", {
        "id": 1,
        "title": "Updated First Post",
        "content": "This is my updated first post!",
    }),
    ("pepe@example.com", {
        "id": 2,
        "title": "Updated Middle Post",
        "content": "Updated Second Post. Middle of the history.",
    }),
    ("google@example.com", {
        "id": 3,
        "title": "Update Last Post",
        "content": "This is my updated last post! End of the history.",
    })
])
async def test_update_post(client: AsyncClient, email: str, post: dict):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.put("/post/", json=post, headers=headers)
    data = res.json()
    assert res.status_code == status.HTTP_200_OK
    assert data["id"] == post["id"]
    assert data["title"] == post["title"]
    assert data["content"] == post["content"]
    assert data["is_published"] is True


@pytest.mark.parametrize("email, post", [
    ("user@example.com", {
        "id": 10,
        "title": "Updated First Post",
        "content": "This is my updated first post!",
    }),
    ("pepe@example.com", {
        "id": 777,
        "title": "Updated Middle Post",
        "content": "Updated Second Post. Middle of the history.",
    }),
    ("google@example.com", {
        "id": 999999,
        "title": "Update Last Post",
        "content": "This is my updated last post! End of the history.",
    }),
])
async def test_update_post_not_exists(
    client: AsyncClient,
    email: str,
    post: dict
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.put("/post/", json=post, headers=headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f'Post with id {post["id"]} not found.'}


@pytest.mark.parametrize("email, post", [
    ("pepe@example.com", {
        "id": 1,
        "title": "Updated First Post",
        "content": "This is my updated first post!",
    }),
    ("google@example.com", {
        "id": 2,
        "title": "Updated Middle Post",
        "content": "Updated Second Post. Middle of the history.",
    }),
    ("user@example.com", {
        "id": 3,
        "title": "Update Last Post",
        "content": "This is my updated last post! End of the history.",
    })
])
async def test_update_post_with_invalid_credentials(
    client: AsyncClient,
    email: str,
    post: dict
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.put("/post/", json=post, headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.json() == {"detail": "Forbidden."}


@pytest.mark.parametrize("post", [
    ({
        "id": 1,
        "title": "Updated First Post",
        "content": "This is my updated first post!",
    }),
    ({
        "id": 2,
        "title": "Updated Middle Post",
        "content": "Updated Second Post. Middle of the history.",
    }),
    ({
        "id": 3,
        "title": "Update Last Post",
        "content": "This is my updated last post! End of the history.",
    }),
])
async def test_update_post_not_authenticated(client: AsyncClient, post: dict):
    res = await client.put("/post/", json=post)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("email, post_id", [
    ("user@example.com", 10),
    ("pepe@example.com", 777),
    ("google@example.com", 9999999),
])
async def test_delete_post_not_exists(
    client: AsyncClient,
    email: str,
    post_id: int
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.delete(f"/post/{id}?post_id={post_id}", headers=headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"Post with id {post_id} not found."}


@pytest.mark.parametrize("email, post_id", [
    ("pepe@example.com", 1),
    ("google@example.com", 2),
    ("user@example.com", 3)
])
async def test_delete_post_with_invalid_credentials(
    client: AsyncClient,
    email: str,
    post_id: int
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.delete(f"/post/{id}?post_id={post_id}", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.json() == {"detail": "Forbidden."}


@pytest.mark.parametrize("post_id", [
    (1),
    (2),
    (3)
])
async def test_delete_post_not_authenticated(
    client: AsyncClient,
    post_id: int
):
    res = await client.delete(f"/post/{id}post_id={post_id}")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("email, post", [
    ("user@example.com", {
        "id": 1,
        "title": "Updated First Post",
        "content": "This is my updated first post!",
    }),
    ("pepe@example.com", {
        "id": 2,
        "title": "Updated Middle Post",
        "content": "Updated Second Post. Middle of the history.",
    }),
    ("google@example.com", {
        "id": 3,
        "title": "Update Last Post",
        "content": "This is my updated last post! End of the history.",
    })
])
async def test_delete_post(client: AsyncClient, email: str, post: dict):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.delete(
        url=f"/post/{id}?post_id={post['id']}",
        headers=headers
    )
    data = res.json()
    assert res.status_code == status.HTTP_200_OK
    assert data["id"] == post["id"]
    assert data["title"] == post["title"]
    assert data["content"] == post["content"]
    assert data["is_published"] is False


@pytest.mark.parametrize("email, post_id", [
    ("user@example.com", 1),
    ("pepe@example.com", 2),
    ("google@example.com", 3)
])
async def test_restore_post(client: AsyncClient, email: str, post_id: int):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.post(
        url=f"/post/restore/{id}?post_id={post_id}",
        headers=headers
    )
    data = res.json()
    assert res.status_code == status.HTTP_200_OK
    assert data["id"] == post_id
    assert data["is_published"] is True


@pytest.mark.parametrize("email, post_id", [
    ("user@example.com", 10),
    ("pepe@example.com", 777),
    ("google@example.com", 999999)
])
async def test_restore_post_not_exists(
    client: AsyncClient,
    email: str,
    post_id: int
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.post(
        url=f"/post/restore/{id}?post_id={post_id}",
        headers=headers
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"Post with id {post_id} not found."}


@pytest.mark.parametrize("email, post_id", [
    ("pepe@example.com", 1),
    ("google@example.com", 2),
    ("user@example.com", 3)
])
async def test_restore_post_with_invalid_credentials(
    client: AsyncClient,
    email: str,
    post_id: int
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.post(
        url=f"/post/restore/{id}?post_id={post_id}",
        headers=headers
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"Post with id {post_id} not found."}


@pytest.mark.parametrize("email, post_id, reaction", [
    ("user@example.com", 1, PostReaction.LIKE),
    ("pepe@example.com", 1, PostReaction.LIKE),
    ("pepe@example.com", 2, PostReaction.LIKE),
    ("google@example.com", 3, PostReaction.DISLIKE),
])
async def test_add_reaction_to_post(
    client: AsyncClient,
    email: str,
    post_id: int,
    reaction: PostReaction
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.post(
        url=f"/post/{id}/reaction/{reaction.value}?post_id={post_id}",
        headers=headers
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json() == (
        f"Reaction {reaction.value} was added to post with id {post_id}"
    )


@pytest.mark.parametrize("email, post_id, reaction", [
    ("user@example.com", 10, PostReaction.LIKE),
    ("pepe@example.com", 10, PostReaction.LIKE),
    ("pepe@example.com", 777, PostReaction.LIKE),
    ("google@example.com", 999999, PostReaction.DISLIKE),
])
async def test_add_reaction_to_post_not_exists(
    client: AsyncClient,
    email: str,
    post_id: int,
    reaction: PostReaction
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.post(
        url=f"/post/{id}/reaction/{reaction.value}?post_id={post_id}",
        headers=headers
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"Post with id {post_id} not found."}


@pytest.mark.parametrize("post_id, like_amount, dislike_amount", [
    (1, 2, 0),
    (2, 1, 0),
    (3, 0, 1)
])
async def test_check_reactions_on_post(
    client: AsyncClient,
    post_id: int,
    like_amount: int,
    dislike_amount: int
):
    res = await client.get(f"/post/{id}?post_id={post_id}")
    data = res.json()
    assert res.status_code == status.HTTP_200_OK
    assert data["id"] == post_id
    assert data["reactions"] == {
        "like": like_amount,
        "dislike": dislike_amount
    }


@pytest.mark.parametrize("email, post_id, reaction", [
    ("user@example.com", 1, PostReaction.DISLIKE),
    ("pepe@example.com", 1, PostReaction.DISLIKE),
    ("pepe@example.com", 2, PostReaction.DISLIKE),
    ("google@example.com", 3, PostReaction.LIKE)
])
async def test_change_reaction_on_post(
    client: AsyncClient,
    email: str,
    post_id: int,
    reaction: PostReaction
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.post(
        url=f"/post/{id}/reaction/{reaction.value}?post_id={post_id}",
        headers=headers
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json() == (
        f"Reaction {reaction.value} was added to post with id {post_id}"
    )


@pytest.mark.parametrize("post_id, like_amount, dislike_amount", [
    (1, 0, 2),
    (2, 0, 1),
    (3, 1, 0)
])
async def test_check_reactions_on_post_after_change_reaction(
    client: AsyncClient,
    post_id: int,
    like_amount: int,
    dislike_amount: int
):
    res = await client.get(f"/post/{id}?post_id={post_id}")
    data = res.json()
    assert res.status_code == status.HTTP_200_OK
    assert data["id"] == post_id
    assert data["reactions"] == {
        "like": like_amount,
        "dislike": dislike_amount
    }


@pytest.mark.parametrize("email, post_id, reaction", [
    ("user@example.com", 1, PostReaction.DISLIKE),
    ("pepe@example.com", 1, PostReaction.DISLIKE),
    ("pepe@example.com", 2, PostReaction.DISLIKE),
    ("google@example.com", 3, PostReaction.LIKE),
])
async def test_remove_reaction_from_post(
    client: AsyncClient,
    email: str,
    post_id: int,
    reaction: PostReaction
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.delete(
        url=f"/post/{id}/reaction/{reaction.value}?post_id={post_id}",
        headers=headers
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == (
        f"Reaction {reaction.value} removed from post with id {post_id}"
    )


@pytest.mark.parametrize("email, post_id, reaction", [
    ("user@example.com", 10, PostReaction.LIKE),
    ("pepe@example.com", 10, PostReaction.LIKE),
    ("pepe@example.com", 777, PostReaction.LIKE),
    ("google@example.com", 999999, PostReaction.DISLIKE),
])
async def test_remove_reaction_from_post_not_exists(
    client: AsyncClient,
    email: str,
    post_id: int,
    reaction: PostReaction
):
    headers = await create_test_auth_headers_for_user(email)
    res = await client.delete(
        url=f"/post/{id}/reaction/{reaction.value}?post_id={post_id}",
        headers=headers
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json() == {"detail": f"Post with id {post_id} not found."}


async def test_delete_user_in_database():
    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
