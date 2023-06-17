from uuid import UUID

from pydantic import BaseModel


class Follow(BaseModel):
    user_id: UUID
    follower_id: UUID

    class Config:
        orm_mode = True
