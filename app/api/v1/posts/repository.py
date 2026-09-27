
from math import ceil
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.post import PostORM
from app.models.tag import TagsORM
from app.models.author import AuthorORM


class PostRepository:

    def __init__(self, db: Session):
        self.db = db

    def get(self, post_id: int) -> Optional[PostORM]:
        post_find = select(PostORM).where(PostORM.id == post_id)
        return self.db.execute(post_find).scalar_one_or_none()

    def search(self, query: Optional[str], order_by:str, direction:str, page: int, per_page: int) -> Tuple[int, List[PostORM]]:
        
        results= select(PostORM) # Construye un objeto de consulta SQL interna de select * from post
        
        if query:
            results = results.where(PostORM.title.ilike(f"%{query}%"))
            
        total = self.db.scalar(select(func.count()).select_from(results.subquery())) or 0

        if total == 0:
             return 0, []
        total_pages = ceil(total / per_page)# Calcular el número total de páginas
        
        current_page = min(page, max(1, total_pages)) # Asegurarse de que la página actual no exceda el número total de páginas

        order_col = PostORM.id if order_by == "id" else func.lower(PostORM.title)
        
        results = results.order_by(order_col.asc() if direction == "asc" else order_col.desc())
        
        start=(current_page-1)*per_page
        
        items = self.db.execute(results.limit(per_page).offset(start)).scalars().all()

        return total, items

    def by_tags(self, tag_names: List[str]) -> List[PostORM]:

        normalize_tag_name = [tag.strip().lower() for tag in tag_names if tag.strip()]
        if not normalize_tag_name:
            return []
        
        post_list = (
                select(PostORM).options(
                selectinload(PostORM.tags),
                joinedload(PostORM.author),
                ).where(PostORM.tags.any(func.lower(TagsORM.name).in_(normalize_tag_name)))
                .order_by(PostORM.id.asc())
            )
        
        return self.db.execute(post_list).scalars().all()

    def ensure_author(self,name: str,email: str) -> AuthorORM:
        
        if name and email:
            author_obj = self.db.execute(select(AuthorORM).where(AuthorORM.email == email)).scalar_one_or_none()

            if author_obj:
                return author_obj
            
            author_obj = AuthorORM(name=name, email=email)
            self.db.add(author_obj)
            self.db.flush()
            return author_obj

    def ensure_tag(self, name: str) -> TagsORM:
        tags_obj = self.db.execute(
                    select(TagsORM).where(TagsORM.name.ilike(name))).scalar_one_or_none()
        if tags_obj:
            return tags_obj

        tags_obj = TagsORM(name=name)
        self.db.add(tags_obj)
        self.db.flush()
        return tags_obj

    def create_post(self, title:str, content:str,author:Optional[dict],tags:List[dict]) -> PostORM:
        author_obj=None
        if author:
            author_obj = self.ensure_author(author['name'],author['email'])

        if tags:
            tags_list=[]
            for tag in tags:
                tag_obj=self.ensure_tag(tag['name'])
                tags_list.append(tag_obj)

        post = PostORM(title=title, content=content, author=author_obj,tags=tags_list)

        self.db.add(post)
        self.db.flush()
        self.db.refresh(post)
        return post

    def update_post(self,post:PostORM,updates:dict) -> PostORM:
        for key, value in updates.items():
            setattr(post, key, value)
    
        self.db.add(post)
        self.db.refresh(post)
        return post

    def delete_post(self,post:PostORM) -> None:
        self.db.delete(post)
