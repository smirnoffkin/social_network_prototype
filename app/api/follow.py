from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.connection import get_db
from app.db.postgres.models import User
from app.schemas.follow import Follow
from app.services.oauth2 import get_current_user_from_token
from app.services.follow import (
    _create_follow,
    _delete_follow,
    _get_list_of_followers,
    _get_list_of_following,
    is_user_following
)
from app.services.user import _get_user_by_username

logger = getLogger(__name__)

router = APIRouter(prefix="/follow", tags=["Follow"])


@router.post(
    "/{username}",
    description="Follow user",
    status_code=status.HTTP_201_CREATED
)
async def follow_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> str:
    user_for_follow = await _get_user_by_username(username, db)
    if user_for_follow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )
    if user_for_follow.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot subscribe to yourself"
        )
    is_follow_exists = await is_user_following(
        user_id=user_for_follow.id,
        follower_id=current_user.id,
        db=db
    )
    if is_follow_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"You are already following user {username}"
        )
    try:
        await _create_follow(
            user_id=user_for_follow.id,
            follower_id=current_user.id,
            db=db
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request"
        )
    return f"You are following to the user {username}"


@router.get(
    "/",
    description="Check status of follow",
    status_code=status.HTTP_200_OK
)
async def get_status_of_follow(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> str:
    user_for_check = await _get_user_by_username(username, db)
    if user_for_check is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )
    is_follow_exists = await is_user_following(
        user_id=user_for_check.id,
        follower_id=current_user.id,
        db=db
    )
    if is_follow_exists:
        return f"You are following to the user {username}"
    return f"You are not following user {username}"


@router.get(
    "/followers",
    description="Get a list of my followers",
    response_model=list[Follow],
    status_code=status.HTTP_200_OK
)
async def get_list_of_followers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> list[Follow]:
    return await _get_list_of_followers(current_user.id, db)


@router.get(
    "/following",
    description="Get a list of my following",
    response_model=list[Follow],
    status_code=status.HTTP_200_OK
)
async def get_list_of_following(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> list[Follow]:
    return await _get_list_of_following(current_user.id, db)


@router.delete(
    "/{username}",
    description="Unfollow user",
    status_code=status.HTTP_200_OK
)
async def unfollow_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> str:
    user_for_unfollow = await _get_user_by_username(username, db)
    if user_for_unfollow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )
    is_follow_exists = await is_user_following(
        user_id=user_for_unfollow.id,
        follower_id=current_user.id,
        db=db
    )
    if not is_follow_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"You are not following user {username}"
        )

    await _delete_follow(
        user_id=user_for_unfollow.id,
        follower_id=current_user.id,
        db=db
    )
    return f"You are unfollowing user {username}"
