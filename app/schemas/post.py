from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class PostReaction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class BasePostSchema(BaseModel):
    title: str
    content: str

    class Config:
        orm_mode = True


class CreatePost(BasePostSchema):
    ...


class UpdatePost(BasePostSchema):
    id: int


class ShowPost(BasePostSchema):
    id: int
    owner_id: UUID
    is_published: bool
    created_at: datetime
    updated_at: datetime
    reactions: dict = {reaction: 0 for reaction in PostReaction}

    class Config:
        use_enum_values = True


class PageRequest(BaseModel):
    skip: int = Field(ge=0, default=0)
    limit: int = Field(ge=0, le=500, default=50)
