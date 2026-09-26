from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String

from app.core.db import Base

if TYPE_CHECKING:
    from .post import PostORM

class TagsORM(Base):
    __tablename__ = "tags"

    id:Mapped[int]=mapped_column(Integer,primary_key=True, index=True)
    name:Mapped[str]=mapped_column(String(100), nullable=False, index=True)

    posts: Mapped[List["PostORM"]] = relationship(
        secondary="post_tags",
        back_populates="tags")
