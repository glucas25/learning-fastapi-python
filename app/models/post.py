from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, Table, Text, DateTime, ForeignKey, UniqueConstraint, Column

from app.core.db import Base

if TYPE_CHECKING:
    from .author import AuthorORM
    from .tag import TagsORM

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey(
        "post.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey(
        "tags.id", ondelete="CASCADE"), primary_key=True)
)



class PostORM(Base):
    __tablename__ = "post"
    __table_args__ = (UniqueConstraint("title", name="unique_post_title"),)

    id:Mapped[int]=mapped_column(Integer,primary_key=True, index=True)
    title:Mapped[str]=mapped_column(String(100), nullable=False, index=True)
    content:Mapped[str]=mapped_column(Text, nullable=False)
    image_url = mapped_column(String(300), nullable=True)
    create_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.now)

    author_id:Mapped[Optional[int]]=mapped_column(ForeignKey("authors.id"))
    author: Mapped[Optional["AuthorORM"]]=relationship(
        back_populates="posts")

    tags:Mapped[List["TagsORM"]]=relationship(
        secondary="post_tags",
        back_populates="posts",
        lazy="selectin",
        passive_deletes=True
    )
