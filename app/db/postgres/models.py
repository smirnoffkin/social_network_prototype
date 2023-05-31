import uuid
from enum import Enum

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    text,
    TIMESTAMP
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TEXT, UUID

from app.db.postgres.connection import Base


class PortalRole(str, Enum):
    ROLE_PORTAL_USER = "ROLE_PORTAL_USER"
    ROLE_PORTAL_ADMIN = "ROLE_PORTAL_ADMIN"
    ROLE_PORTAL_SUPERADMIN = "ROLE_PORTAL_SUPERADMIN"


class BaseAlchemyModel(Base):
    __abstract__ = True

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()")
    )


class User(BaseAlchemyModel):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    roles = Column(ARRAY(String), nullable=False)
    posts = relationship("Post", back_populates="owner")

    @property
    def is_superadmin(self) -> bool:
        return PortalRole.ROLE_PORTAL_SUPERADMIN in self.roles

    @property
    def is_admin(self) -> bool:
        return PortalRole.ROLE_PORTAL_ADMIN in self.roles

    def enrich_admin_roles_by_admin_role(self):
        if not self.is_admin:
            return {*self.roles, PortalRole.ROLE_PORTAL_ADMIN}

    def remove_admin_privileges(self):
        if self.is_admin:
            return {PortalRole.ROLE_PORTAL_USER}


class Post(BaseAlchemyModel):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(TEXT, nullable=False)
    content = Column(TEXT, nullable=False)
    is_published = Column(Boolean, server_default="TRUE", nullable=False)
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    owner = relationship("User", back_populates="posts")
