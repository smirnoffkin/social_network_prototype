from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crud import FollowCRUD
from app.schemas.follow import Follow


async def _create_follow(
    user_id: UUID,
    follower_id: UUID,
    db: AsyncSession
) -> None:
    async with db.begin():
        follow_crud = FollowCRUD(db)
        await follow_crud.create_follow(user_id, follower_id)


async def _get_list_of_following(
    follower_id: UUID,
    db: AsyncSession
) -> list:
    async with db.begin():
        follow_crud = FollowCRUD(db)
        return await follow_crud.get_all_following(follower_id)


async def _get_list_of_followers(
    user_id: UUID,
    db: AsyncSession
) -> list:
    async with db.begin():
        follow_crud = FollowCRUD(db)
        return await follow_crud.get_all_followers(user_id)


async def is_user_following(
    user_id: UUID,
    follower_id: UUID,
    db: AsyncSession
) -> bool:
    async with db.begin():
        follow_crud = FollowCRUD(db)
        follow = await follow_crud.get_follow(user_id, follower_id)
        return False if follow is None else True


async def _delete_follow(
    user_id: UUID,
    follower_id: UUID,
    db: AsyncSession
) -> None:
    async with db.begin():
        follow_crud = FollowCRUD(db)
        await follow_crud.delete_follow(user_id, follower_id)
