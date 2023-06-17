from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_cache.decorator import cache
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.connection import get_db
from app.db.postgres.models import User
from app.schemas.post import CreatePost, UpdatePost, ShowPost, PostReaction
from app.services.oauth2 import get_current_user_from_token
from app.services.post import (
    _create_new_post,
    _delete_post,
    _get_post_by_id,
    _get_all_posts_by_title,
    _update_post,
    _restore_post,
    _add_reaction_to_post,
    _remove_reaction_from_post
)

logger = getLogger(__name__)

router = APIRouter(prefix="/post", tags=["Post (articles)"])


@router.post(
    "/create",
    description="Create post",
    response_model=ShowPost,
    status_code=status.HTTP_201_CREATED
)
async def create_post(
    body: CreatePost,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> ShowPost:
    try:
        new_post = await _create_new_post(body, current_user.id, db)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This post is already exists"
        )
    return new_post


@router.get(
    "/{id}",
    description="Get post by id",
    response_model=ShowPost,
    status_code=status.HTTP_200_OK
)
@cache(expire=10)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db)
) -> ShowPost:
    post = await _get_post_by_id(post_id, db)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found."
        )
    return post


@router.get(
    "/posts/{title}",
    description="Get a list of all posts with this name",
    response_model=list[ShowPost],
    status_code=status.HTTP_200_OK
)
@cache(expire=10)
async def get_all_posts_by_title(
    title: str,
    db: AsyncSession = Depends(get_db)
) -> list[ShowPost]:
    posts = await _get_all_posts_by_title(title, db)
    return posts


@router.put(
    "/",
    description="Update post",
    response_model=ShowPost,
    status_code=status.HTTP_200_OK
)
async def update_post(
    body: UpdatePost,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> ShowPost:
    updated_post_params = body.dict(exclude_none=True)
    if updated_post_params == {}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing fields"
        )
    post_for_update = await _get_post_by_id(body.id, db)
    if post_for_update is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {body.id} not found."
        )
    if post_for_update.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden."
        )
    try:
        updated_post = await _update_post(
            post_id=post_for_update.id,
            owner_id=current_user.id,
            updated_post_params=updated_post_params,
            db=db
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request"
        )
    return updated_post


@router.delete(
    "/{id}",
    description="Delete post",
    response_model=ShowPost,
    status_code=status.HTTP_200_OK
)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> ShowPost:
    post_to_delete = await _get_post_by_id(post_id, db)
    if post_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found."
        )
    if post_to_delete.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden."
        )
    deleted_post = await _delete_post(post_id, current_user.id, db)
    return deleted_post


@router.post(
    "/restore/{id}",
    description="Restore post",
    response_model=ShowPost,
    status_code=status.HTTP_200_OK
)
async def restore_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> ShowPost:
    post_to_restore = await _restore_post(post_id, current_user.id, db)
    if post_to_restore is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found."
        )
    return post_to_restore


@router.post(
    "/{id}/reaction/{reaction}",
    description="Add reaction",
    status_code=status.HTTP_201_CREATED
)
async def add_reaction_to_post(
    reaction: PostReaction,
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
) -> str:
    post = await _get_post_by_id(post_id, db)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found."
        )
    await _add_reaction_to_post(post_id, current_user.id, reaction)
    return f"Reaction {reaction.value} was added to post with id {post_id}"


@router.delete(
    "/{id}/reaction/{reaction}",
    description="Remove reaction",
    status_code=status.HTTP_200_OK
)
async def remove_reaction_from_post(
    reaction: PostReaction,
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> str:
    post = await _get_post_by_id(post_id, db)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found."
        )
    await _remove_reaction_from_post(post_id, current_user.id, reaction)
    return f"Reaction {reaction.value} removed from post with id {post_id}"
