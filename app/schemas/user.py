from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class BaseUserSchema(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr

    class Config:
        orm_mode = True


class CreateUser(BaseUserSchema):
    password: str = Field(min_length=8)


class UpdateUser(BaseUserSchema):
    ...


class ShowUser(BaseUserSchema):
    id: UUID
    is_active: bool


class ShowAdmin(ShowUser):
    created_at: datetime
    updated_at: datetime
    roles: list


class ShowUserFullInfo(ShowAdmin):
    hashed_password: str


class LoginUser(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True
