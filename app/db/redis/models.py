from uuid import UUID

from pydantic import BaseModel

from app.schemas.post import PostReaction


class PostReactionRedisSet(BaseModel):
    post_id: int | None = None
    user_id: UUID | None = None
    reaction: PostReaction | None = None

    @property
    def key(self):
        if self.post_id is None or self.reaction is None:
            raise ValueError("Can't create key: check post_id or reaction")
        return f"Post:{self.post_id} Reaction:{self.reaction.value}"

    @property
    def value(self):
        if self.user_id is None:
            raise ValueError("Can't create value: user_id is null")
        return str(self.user_id)
