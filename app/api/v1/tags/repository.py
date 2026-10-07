
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tag import TagsORM


class TagRepository:
    def __init__(self, db:Session):
        self.db=db

    def create_tag(self,name:str):
        normalize_tag =name.strip().lower()

        tags_obj = self.db.execute(
                            select(TagsORM).where(TagsORM.name.ilike(normalize_tag))).scalar_one_or_none()
        if tags_obj:
            return tags_obj

        tags_obj = TagsORM(name=name)
        self.db.add(tags_obj)
        self.db.flush()
        return tags_obj