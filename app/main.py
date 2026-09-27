import os
from datetime import datetime
from math import ceil
from typing import Optional, List, Union, Literal
from fastapi import FastAPI, Query, Path, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from sqlalchemy import create_engine, Integer, String, Text, DateTime, select, func, UniqueConstraint, ForeignKey, \
    Table, Column, Select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column, relationship, selectinload, \
    joinedload
from dotenv import load_dotenv

load_dotenv()











Base.metadata.create_all(bind=engine) #dev



app=FastAPI(title="MiniBlog")



@app.get("/")
def home():
    return {'message': 'Bienvenido a mi MiniBlog'}



@app.get("/posts/by-tags", response_model=List[PostPublic])
def filter_by_tags(tags: List[str] = Query(
    ...,
    min_length=1,
    description="Una o mas etiquetas. Ejemplo: ?tags=python&tags=fastapi")
    ,db:Session = Depends(get_db)
    ):
    if not tags:
        raise HTTPException(status_code=404, detail="Tags no agregado")

    normalize_tag_name = [tag.strip().lower() for tag in tags if tag.strip()]
    if not normalize_tag_name:
        return []

    post_list = (
        select(PostORM).options(
        selectinload(PostORM.tags),
        joinedload(PostORM.author),
        ).where(PostORM.tags.any(func.lower(TagsORM.name).in_(normalize_tag_name)))
        .order_by(PostORM.id.asc())
    )
    post = db.execute(post_list).scalars().all()

    return post #PostPublic.model_validate(post, from_attributes=True)




@app.get("/posts/{post_id}", response_model= Union[PostPublic, PostSummary], response_description="Post encontrado")
def get_post(post_id: int = Path(
        ..., ge=1, title="ID del post",
        description="ID del post a buscar",
        examples=[1]),
        include_content: bool = Query(
        default=True, description="Permite mostrar el contenido del post"),
        db: Session = Depends(get_db)
        ):
    #Alternativa directa por primary key
    #post = db.get(PostORM,post_id)

    #Alternativa flexible para cualquier busqueda
    post_find = select(PostORM).where(PostORM.id == post_id)
    post = db.execute(post_find).scalars().first()

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)

    return PostSummary.model_validate(post, from_attributes=True)



# POST con BODY y Pydantic
@app.post("/posts", response_model=PostPublic, response_description="Post creado exitosamente", status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    author_obj=None
    if post.author:
        author_obj = db.execute(
            select(AuthorORM).where(AuthorORM.email == post.author.email)).scalar_one_or_none()
        if not author_obj:
            author_obj = AuthorORM(name=post.author.name, email=post.author.email)
            db.add(author_obj)
            db.flush()

    new_post = PostORM(title=post.title, content=post.content, author=author_obj)


    for tag in post.tags:
        tags_obj = db.execute(
                select(TagsORM).where(TagsORM.name.ilike(tag.name))).scalar_one_or_none()
        if not tags_obj:
            tags_obj = TagsORM(name=tag.name)
            db.add(tags_obj)
            db.flush()
        new_post.tags.append(tags_obj)
    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El post ya existe")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error de SQLAlchemy")
    # new_id=max(post["id"] for post in BLOG_POSTS)+1 if BLOG_POSTS else 1
    # new_post={"id": new_id,
    #         "title": post.title,
    #         "content": post.content,
    #         "tags": [tag.model_dump() for tag in post.tags],
    #         "autor": post.autor.model_dump() if post.autor else None}
    # BLOG_POSTS.append(new_post)
    # return new_post


@app.put("/posts/{post_id}", response_model=PostPublic, response_description="Post actualizado exitosamente", response_model_exclude_none=True)
def update_post(post_id: int,
                data: PostUpdate,
                db: Session = Depends(get_db)
                ):

    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    updated_post = data.model_dump(exclude_unset=True)
    for key, value in updated_post.items():
        setattr(post, key, value)

    try:
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # for post in BLOG_POSTS:
    #     if post["id"] == post_id:
    #         if data.title is not None: post["title"] = data.title
    #         if data.content is not None: post["content"] = data.content
    #         return post
    # raise HTTPException(status_code=404, detail="Post no encontrado")

@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int,
                db:Session = Depends(get_db)
                ):
    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    try:
        db.delete(post)
        db.commit()
        #return {}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

