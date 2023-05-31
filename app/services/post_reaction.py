from uuid import UUID

from app.db.postgres.models import Post
from app.db.redis.connection import redis
from app.db.redis.models import PostReaction, PostReactionRedisSet
from app.schemas.post import ShowPost
from app.services.crud import PostReactionCRUD


async def enrich_post_with_reactions(post: Post) -> ShowPost:
    reactions = await PostReactionCRUD().get_post_reactions(post.id)

    resp = ShowPost.from_orm(post)
    resp.reactions = reactions
    return resp


async def is_user_liked_post(post_id: int, user_id: UUID) -> bool:
    rk = PostReactionRedisSet(
        post_id=post_id,
        user_id=user_id,
        reaction=PostReaction.LIKE
    )
    value = redis.get(rk.key)
    return False if value is None else True


async def is_user_disliked_post(post_id: int, user_id: UUID) -> bool:
    rk = PostReactionRedisSet(
        post_id=post_id,
        user_id=user_id,
        reaction=PostReaction.DISLIKE
    )
    value = redis.get(rk.key)
    return False if value is None else True


async def is_user_left_reaction_on_post(post_id: int, user_id: UUID) -> bool:
    user_liked_post = await is_user_liked_post(post_id, user_id)
    if user_liked_post:
        return True
    user_disliked_post = await is_user_disliked_post(post_id, user_id)
    if user_disliked_post:
        return True
    return False
