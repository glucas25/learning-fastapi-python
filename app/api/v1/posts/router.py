from math import ceil

from fastapi import APIRouter, HTTPException, Path, Query, Depends, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List, Literal, Optional, Union

from app.core.db import get_db
from .schemas import (PostCreate, PostPublic, PostSummary, PostUpdate, PaginatedPosts)
from .repository import PostRepository
from app.core.security import oauth2_scheme

router=APIRouter(prefix="/posts", tags=["posts"])

@router.get("",response_model=PaginatedPosts)
def list_posts(
    text: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Query string para filtrar por titulos de los posts"
    ),
    query: Optional[str] =Query(
        default=None,
        description="Query string para filtrar por titulos de los posts",
        alias="search",
        min_length=3,
        max_length=50
    ),
    per_page: int=Query(
        10, ge=1, le=50, description="Cantidad de resultados por pagina, entre 1 y 50"),
    page: int=Query(
        1, ge=1, description="Numero de pagina, debe ser un entero mayor o igual a 1"),
    order_by: Literal["id", "title"]=Query(
        "id", description="Campo por el cual ordenar los resultados, puede ser 'id' o 'title'"),
    direction: Literal["asc", "desc"]=Query(
        "asc", description="Direccion del ordenamiento, puede ser 'asc' o 'desc'"),
    db:Session = Depends(get_db)
    ):

    repository = PostRepository(db)

    query = query or text

    total, items = repository.search(query, order_by, direction, page, per_page)

    total_pages = ceil(total / per_page) if total > 0 else 0  # Calcular el número total de páginas

    current_page = 1 if total_pages == 0 else min(page, total_pages) # Asegurarse de que la página actual no exceda el número total de páginas
    
    has_prev = current_page > 1
    has_next = current_page < total_pages if total_pages > 0 else False

    return PaginatedPosts(
        page=current_page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        order_by=order_by,
        direction=direction,
        search=query,
        items=items
    )

@router.get("/by-tags", response_model=List[PostPublic])
def filter_by_tags(tags: List[str] = Query(
    ...,
    min_length=1,
    description="Una o mas etiquetas. Ejemplo: ?tags=python&tags=fastapi")
    ,db:Session = Depends(get_db)
    ):
    if not tags:
        raise HTTPException(status_code=404, detail="Tags no agregado")

    repository =PostRepository(db)

    return repository.by_tags(tags)

@router.get("/{post_id}", response_model= Union[PostPublic, PostSummary], response_description="Post encontrado")
def get_post(post_id: int = Path(
        ..., ge=1, title="ID del post",
        description="ID del post a buscar",
        examples=[1]),
        include_content: bool = Query(
        default=True, description="Permite mostrar el contenido del post"),
        db: Session = Depends(get_db)
        ):

    repository = PostRepository(db)

    post = repository.get(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)

    return PostSummary.model_validate(post, from_attributes=True)

@router.post("", response_model=PostPublic, response_description="Post creado exitosamente", status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):

    repository = PostRepository(db)

    try:
        post = repository.create_post(title=post.title,content= post.content,
            author=(post.author.model_dump() if post.author else None),
            tags=[tag.model_dump() for tag in post.tags])
        db.commit()
        db.refresh(post)
        return post

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El post ya existe")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error de SQLAlchemy")


@router.put("/{post_id}", response_model=PostPublic, response_description="Post actualizado exitosamente", response_model_exclude_none=True)
def update_post(post_id: int,
                data: PostUpdate,
                db: Session = Depends(get_db)
                ):

    repository = PostRepository(db)

    post = repository.get(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    try:
        updates = data.model_dump(exclude_unset=True) #Convertir el basemodel PostUpdate a diccionario
        updated_post = repository.update_post(post, updates)
        db.commit()
        db.refresh(updated_post)
        return updated_post
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int,
                db:Session = Depends(get_db)
                ):
    repository = PostRepository(db)
    post = repository.get(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    try:
        repository.delete_post(post)
        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/secure")
def secure_endpoint(token:str=Depends(oauth2_scheme)):
    return {"message":"Acceso con token","token_recibido":token}