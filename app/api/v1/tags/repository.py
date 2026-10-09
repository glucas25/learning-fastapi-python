
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.tags.schemas import TagPublic
from app.models import PostORM, post_tags
from app.models import TagsORM
from app.services.pagination import paginate_query


class TagRepository:
    def __init__(self, db:Session):
        self.db=db

    def get(self,id:int) -> Optional[TagsORM]:
        tag_find = select(TagsORM).where(TagsORM.id == id)
        return self.db.execute(tag_find).scalar_one_or_none()

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

    def update_tag(self,id:int,name:str) -> Optional[TagsORM]:
        tag = self.get(id=id)
        if not tag:
            return None
        if tag is not None:
            tag.name=name.strip().lower()

        self.db.add(tag)
        self.db.flush()
        self.db.refresh(tag)
        return tag

    def delete_tag(self,id:int) -> bool:
        tag = self.get(id=id)
        if not tag:
            return False
        self.db.delete(tag)
        return True

    def most_popular_tags(self) -> dict|None:
        row=(
            self.db.execute(
                select(
                    TagsORM.id.label("id"),
                    TagsORM.name.label("name"),
                    func.count(PostORM.id).label("uses")
                )
                .join(post_tags, post_tags.c.tag_id == TagsORM.id)
                .join(PostORM, PostORM.id == post_tags.c.post_id)
                .group_by(TagsORM.id, TagsORM.name)
                .order_by(func.count(PostORM.id).desc(), func.lower(TagsORM.name).asc())
                .limit(1)
            ).mappings() #convierte a diccionario
            .first()
        )

        return dict(row) if row else None


