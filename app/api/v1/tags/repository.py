
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.tags.schemas import TagPublic
from app.models.tag import TagsORM
from app.services.pagination import paginate_query


class TagRepository:
    def __init__(self, db:Session):
        self.db=db

    def list_tags(self,
               search: Optional[str],
               order_by:str="id",
               direction:str="asc",
               page: int=1,
               per_page: int=10):
        query = select(TagsORM)
        if search:
            query = query.where(func.lower(
                TagsORM.name).ilike(f"%{search.lower()}%"))

        allowed_order ={
            "id":TagsORM.id,
            "name":func.lower(TagsORM.name),
        }

        result = paginate_query(
            db=self.db,
            model=TagsORM,
            base_query=query,
            page=page,
            per_page=per_page,
            order_by=order_by,
            direction=direction,
            allowed_order=allowed_order
        )

        result["items"]=[TagPublic.model_validate(item) for item in result["items"]]

        return result

    

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