from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.post import CreatePost, ShowPost, PostReaction
from app.services.crud import PostCRUD, PostReactionCRUD
from app.services.post_reaction import (
    enrich_post_with_reactions,
    is_user_liked_post,
    is_user_disliked_post
)


async def _create_new_post(
    body: CreatePost,
    owner_id: UUID,
    db: AsyncSession
) -> ShowPost:
    async with db.begin():
        post_crud = PostCRUD(db)
        return await post_crud.create_post(
            title=body.title,
            content=body.content,
            owner_id=owner_id
        )


async def _get_post_by_id(post_id: int, db: AsyncSession) -> ShowPost | None:
    async with db.begin():
        post_crud = PostCRUD(db)
        post = await post_crud.get_post_by_id(post_id)
        if post is None:
            return
        return await enrich_post_with_reactions(post)


async def _get_all_posts_by_title(title: str, db: AsyncSession) -> list:
    async with db.begin():
        post_crud = PostCRUD(db)
        posts = await post_crud.get_all_posts_by_title(title)

        if len(posts) != 0:
            for i in range(len(posts)):
                posts[i] = await enrich_post_with_reactions(posts[i])

        return posts


async def _update_post(
    post_id: int,
    owner_id: UUID,
    updated_post_params: dict,
    db: AsyncSession
) -> ShowPost | None:
    async with db.begin():
        post_crud = PostCRUD(db)
        updated_post_params.update({"updated_at": datetime.now()})
        updated_post = await post_crud.update_post(
            post_id=post_id,
            owner_id=owner_id,
            **updated_post_params
        )
        return await enrich_post_with_reactions(updated_post)


async def _delete_post(
    post_id: int,
    owner_id: UUID,
    db: AsyncSession
) -> ShowPost | None:
    async with db.begin():
        post_crud = PostCRUD(db)
        deleted_post = await post_crud.delete_post(post_id, owner_id)
        return await enrich_post_with_reactions(deleted_post)


async def _restore_post(
    post_id: int,
    owner_id: UUID,
    db: AsyncSession
) -> ShowPost | None:
    async with db.begin():
        post_crud = PostCRUD(db)
        restored_post = await post_crud.restore_post(post_id, owner_id)
        if restored_post is None:
            return
        return await enrich_post_with_reactions(restored_post)


async def _add_reaction_to_post(
    post_id: int,
    user_id: UUID,
    reaction: PostReaction
) -> None:
    if reaction.value == PostReaction.LIKE and await is_user_disliked_post(
        post_id=post_id,
        user_id=user_id
    ):
        await PostReactionCRUD().remove_reaction(
            post_id=post_id,
            user_id=user_id,
            reaction=PostReaction.DISLIKE
        )
    elif reaction.value == PostReaction.DISLIKE and await is_user_liked_post(
        post_id=post_id,
        user_id=user_id
    ):
        await PostReactionCRUD().remove_reaction(
            post_id=post_id,
            user_id=user_id,
            reaction=PostReaction.LIKE
        )
    await PostReactionCRUD().add_reaction(post_id, user_id, reaction)


async def _remove_reaction_from_post(
    post_id: int,
    user_id: UUID,
    reaction: PostReaction
) -> None:
    await PostReactionCRUD().remove_reaction(post_id, user_id, reaction)
