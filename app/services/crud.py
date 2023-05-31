from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.models import PortalRole, Post, User
from app.db.redis.connection import redis
from app.db.redis.models import PostReaction, PostReactionRedisSet


class UserCRUD:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(
        self,
        username: str,
        first_name: str,
        last_name: str,
        email: str,
        hashed_password: str,
        roles: list[PortalRole],
    ) -> User:
        new_user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            is_active=True,
            roles=roles,
        )
        self.db_session.add(new_user)
        await self.db_session.commit()
        return new_user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        query = (
            select(User)
            .where(and_(User.id == user_id, User.is_active == True))
        )
        res = await self.db_session.execute(query)
        user_row = res.fetchone()
        if user_row is not None:
            return user_row[0]

    async def get_user_by_email(self, email: str) -> User | None:
        query = (
            select(User)
            .where(and_(User.email == email, User.is_active == True))
        )
        res = await self.db_session.execute(query)
        user_row = res.fetchone()
        if user_row is not None:
            return user_row[0]

    async def get_user_by_username(self, username: str) -> User | None:
        query = (
            select(User)
            .where(and_(User.username == username, User.is_active == True))
        )
        res = await self.db_session.execute(query)
        user_row = res.fetchone()
        if user_row is not None:
            return user_row[0]

    async def update_user_by_id(self, user_id: UUID, **kwargs) -> User | None:
        query = (
            update(User)
            .where(and_(User.id == user_id, User.is_active == True))
            .values(kwargs)
            .returning(User)
        )
        res = await self.db_session.execute(query)
        update_user_row = res.fetchone()
        if update_user_row is not None:
            return update_user_row[0]

    async def update_user_by_email(self, email: str, **kwargs) -> UUID | None:
        query = (
            update(User)
            .where(and_(User.email == email, User.is_active == True))
            .values(kwargs)
            .returning(User.id)
        )
        res = await self.db_session.execute(query)
        update_user_row = res.fetchone()
        if update_user_row is not None:
            return update_user_row[0]

    async def delete_user_by_id(self, user_id: UUID) -> User | None:
        query = (
            update(User)
            .where(and_(User.id == user_id, User.is_active == True))
            .values(is_active=False)
            .returning(User)
        )
        res = await self.db_session.execute(query)
        deleted_user_row = res.fetchone()
        if deleted_user_row is not None:
            return deleted_user_row[0]

    async def delete_user_by_email(self, email: str) -> User | None:
        query = (
            update(User)
            .where(and_(User.email == email, User.is_active == True))
            .values(is_active=False)
            .returning(User)
        )
        res = await self.db_session.execute(query)
        deleted_user_row = res.fetchone()
        if deleted_user_row is not None:
            return deleted_user_row[0]

    async def restore_user_by_email(self, email: str) -> User | None:
        query = (
            update(User)
            .where(and_(User.email == email, User.is_active == False))
            .values(is_active=True)
            .returning(User)
        )
        res = await self.db_session.execute(query)
        restored_user_row = res.fetchone()
        if restored_user_row is not None:
            return restored_user_row[0]


class PostCRUD:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_post(
        self,
        title: str,
        content: str,
        owner_id: UUID
    ) -> Post:
        new_post = Post(
            title=title,
            content=content,
            is_published=True,
            owner_id=owner_id
        )
        self.db_session.add(new_post)
        await self.db_session.commit()
        return new_post

    async def get_post_by_id(self, post_id: int) -> Post | None:
        query = (
            select(Post)
            .where(and_(Post.id == post_id, Post.is_published == True))
        )
        res = await self.db_session.execute(query)
        post_row = res.fetchone()
        if post_row is not None:
            return post_row[0]

    async def get_all_posts_by_title(self, title: str) -> list[Post]:
        query = (
            select(Post)
            .where(and_(Post.title == title, Post.is_published == True))
        )
        res = await self.db_session.execute(query)
        posts = list(res.scalars().all())
        return posts

    async def update_post(
        self,
        post_id: int,
        owner_id: UUID,
        **kwargs
    ) -> Post | None:
        query = (
            update(Post)
            .where(
                and_(
                    Post.id == post_id,
                    Post.owner_id == owner_id,
                    Post.is_published == True,
                )
            )
            .values(kwargs)
            .returning(Post)
        )
        res = await self.db_session.execute(query)
        update_post_row = res.fetchone()
        if update_post_row is not None:
            return update_post_row[0]

    async def delete_post(self, post_id: int, owner_id: UUID) -> Post | None:
        query = (
            update(Post)
            .where(
                and_(
                    Post.id == post_id,
                    Post.owner_id == owner_id,
                    Post.is_published == True,
                )
            )
            .values(is_published=False)
            .returning(Post)
        )
        res = await self.db_session.execute(query)
        deleted_post_row = res.fetchone()
        if deleted_post_row is not None:
            return deleted_post_row[0]

    async def restore_post(self, post_id: int, owner_id: UUID) -> Post | None:
        query = (
            update(Post)
            .where(
                and_(
                    Post.id == post_id,
                    Post.owner_id == owner_id,
                    Post.is_published == False,
                )
            )
            .values(is_published=True)
            .returning(Post)
        )
        res = await self.db_session.execute(query)
        restored_post_row = res.fetchone()
        if restored_post_row is not None:
            return restored_post_row[0]


class PostReactionCRUD:
    @staticmethod
    async def add_reaction(
        post_id: int,
        user_id: UUID,
        reaction: PostReaction
    ):
        rk = PostReactionRedisSet(
            post_id=post_id,
            user_id=user_id,
            reaction=reaction
        )
        async with redis.pipeline(transaction=True) as pipe:
            await pipe.sadd(rk.key, rk.value)
            await pipe.execute()

    @staticmethod
    async def get_post_reactions(post_id: int) -> dict:
        rk = PostReactionRedisSet(post_id=post_id)
        reactions = {}
        for reaction in PostReaction:
            rk.reaction = reaction
            reactions |= {reaction: await redis.scard(rk.key)}

        return reactions

    @staticmethod
    async def remove_reaction(
        post_id: int,
        user_id: UUID,
        reaction: PostReaction
    ):
        rk = PostReactionRedisSet(
            post_id=post_id,
            user_id=user_id,
            reaction=reaction
        )
        await redis.srem(rk.key, rk.value)

    @staticmethod
    async def remove_all_reactions(post_id: int, user_id: UUID):
        rk = PostReactionRedisSet(post_id=post_id, user_id=user_id)
        async with redis.pipeline(transaction=True) as pipe:
            for to_delete in PostReaction:
                rk.reaction = to_delete
                await pipe.srem(rk.key, rk.value)
            await pipe.execute()
