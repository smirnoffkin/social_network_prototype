from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_cache.decorator import cache
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.connection import get_db
from app.db.postgres.models import User
from app.schemas.user import CreateUser, UpdateUser, ShowUser
from app.services.oauth2 import get_current_user_from_token
from app.services.user import (
    _create_new_user,
    _delete_user_by_email,
    _get_user_by_email,
    _get_user_by_username,
    _update_user,
    check_user_permissions
)
from app.utils.celery.worker import verify_email_for_registration

logger = getLogger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.post(
    "/registration",
    description="Registration",
    response_model=ShowUser,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    body: CreateUser,
    db: AsyncSession = Depends(get_db)
) -> ShowUser:
    try:
        is_verified_email = verify_email_for_registration.delay(body.email)
        if is_verified_email:
            new_user = await _create_new_user(body, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have not verified your email"
            )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username or email is already in use"
        )
    return new_user


@router.get(
    "/{username}",
    description="Get information about a user by username",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK
)
@cache(expire=120)
async def get_user(
    username: str,
    db: AsyncSession = Depends(get_db)
) -> ShowUser:
    user = await _get_user_by_username(username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found."
        )
    return user


@router.put(
    "/update_profile",
    description="Update profile",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK
)
async def update_user(
    body: UpdateUser,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> ShowUser:
    updated_user_params = body.dict(exclude_none=True)
    if updated_user_params == {}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing fields"
        )
    user_for_update = await _get_user_by_email(body.email, db)
    if user_for_update is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {body.email} not found."
        )
    if body.email != current_user.email:
        if check_user_permissions(
            target_user=user_for_update,
            current_user=current_user
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden."
            )
    try:
        updated_user = await _update_user(
            updated_user_params=updated_user_params,
            user_id=current_user.id,
            db=db
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request"
        )
    return updated_user


@router.delete(
    "/delete_account/{email}",
    description="Delete account",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK
)
async def delete_user(
    email: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> ShowUser:
    user_to_delete = await _get_user_by_email(email, db)
    if user_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found."
        )
    if not check_user_permissions(
        target_user=user_to_delete,
        current_user=current_user
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden."
        )

    deleted_user = await _delete_user_by_email(email, db)
    if deleted_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found."
        )
    return deleted_user
