from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.models import PortalRole, User
from app.schemas.user import CreateUser
from app.services.crud import UserCRUD
from app.services.security import Hasher


async def _create_new_user(body: CreateUser, db: AsyncSession) -> User:
    async with db.begin():
        user_crud = UserCRUD(db)
        return await user_crud.create_user(
            username=body.username,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            hashed_password=Hasher.get_hashed_password(body.password),
            roles=[PortalRole.ROLE_PORTAL_USER],
        )


async def _delete_user_by_id(user_id: UUID, db: AsyncSession) -> User | None:
    async with db.begin():
        user_crud = UserCRUD(db)
        return await user_crud.delete_user_by_id(user_id)


async def _delete_user_by_email(email: str, db: AsyncSession) -> User | None:
    async with db.begin():
        user_crud = UserCRUD(db)
        return await user_crud.delete_user_by_email(email)


async def _update_user(
    updated_user_params: dict,
    user_id: UUID,
    db: AsyncSession
) -> User | None:
    async with db.begin():
        user_crud = UserCRUD(db)
        updated_user_params.update({"updated_at": datetime.now()})
        return await user_crud.update_user_by_id(
            user_id=user_id,
            **updated_user_params
        )


async def _get_user_by_id(user_id: UUID, db: AsyncSession) -> User | None:
    async with db.begin():
        user_crud = UserCRUD(db)
        return await user_crud.get_user_by_id(user_id)


async def _get_user_by_email(email: str, db: AsyncSession) -> User | None:
    async with db.begin():
        user_crud = UserCRUD(db)
        return await user_crud.get_user_by_email(email)


async def _get_user_by_username(
    username: str,
    db: AsyncSession
) -> User | None:
    async with db.begin():
        user_crud = UserCRUD(db)
        return await user_crud.get_user_by_username(username)


def check_user_permissions(target_user: User, current_user: User) -> bool:
    if PortalRole.ROLE_PORTAL_SUPERADMIN in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Superadmin cannot be deleted via API.",
        )
    if target_user.id != current_user.id:
        # check admin role
        if not {
            PortalRole.ROLE_PORTAL_ADMIN,
            PortalRole.ROLE_PORTAL_SUPERADMIN,
        }.intersection(current_user.roles):
            return False
        # check admin deactivate superadmin attempt
        if (
            PortalRole.ROLE_PORTAL_SUPERADMIN in target_user.roles
            and PortalRole.ROLE_PORTAL_ADMIN in current_user.roles
        ):
            return False
        # check admin deactivate admin attempt
        if (
            PortalRole.ROLE_PORTAL_ADMIN in target_user.roles
            and PortalRole.ROLE_PORTAL_ADMIN in current_user.roles
        ):
            return False
    return True
