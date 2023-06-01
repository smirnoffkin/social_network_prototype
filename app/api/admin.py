from logging import getLogger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.connection import get_db
from app.db.postgres.models import User
from app.schemas.user import ShowAdmin
from app.services.oauth2 import get_current_user_from_token
from app.services.user import _get_user_by_id, _update_user

logger = getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.patch(
    "/admin_privilege",
    description="Grant admin rights to the user",
    response_model=ShowAdmin,
    status_code=status.HTTP_200_OK
)
async def grant_admin_privilege(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> ShowAdmin:
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden."
        )
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot manage privileges of itself."
        )
    user_for_promotion = await _get_user_by_id(user_id, db)
    if user_for_promotion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found."
        )
    if user_for_promotion.is_admin or user_for_promotion.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {user_id} already promoted to admin / superadmin."
        )
    updated_user_params = {
        "roles": user_for_promotion.enrich_admin_roles_by_admin_role()
    }
    try:
        updated_user = await _update_user(
            updated_user_params=updated_user_params,
            user_id=user_id,
            db=db
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request."
        )
    return updated_user


@router.delete(
    "/admin_privilege",
    description="Revoke admin rights from a user",
    response_model=ShowAdmin,
    status_code=status.HTTP_200_OK
)
async def revoke_admin_privilege(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
) -> ShowAdmin:
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden."
        )
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot manage privileges of itself."
        )
    user_for_revoke_admin_privileges = await _get_user_by_id(user_id, db)
    if user_for_revoke_admin_privileges is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found."
        )
    if not user_for_revoke_admin_privileges.is_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with id {user_id} has no admin privileges."
        )
    updated_user_params = {
        "roles": user_for_revoke_admin_privileges.remove_admin_privileges()
    }
    try:
        updated_user = await _update_user(
            updated_user_params=updated_user_params,
            user_id=user_id,
            db=db
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request."
        )
    return updated_user
