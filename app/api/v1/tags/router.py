from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.tags.repository import TagRepository
from app.api.v1.tags.schemas import TagCreate, TagPublic, TagUpdate
from app.core.db import get_db
from app.core.security import get_current_user


router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/{tag_id]", response_model=TagPublic, status_code=status.HTTP_200_OK)
def get_tags(tag_id: int, db: Session = Depends(get_db)):
    repository = TagRepository(db)
    tag_find = repository.get(tag_id)
    if not tag_find:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag_find

@router.get("", response_model=Dict)
def list_tags(
        query: str | None = Query(None),
        per_page: int=Query(10, ge=1, le=100),
        page: int=Query(1, ge=1 ),
        order_by: str=Query("id", pattern="^(id|name)$"),
        direction: str=Query("asc", pattern="^(asc|desc)$"),
        db:Session = Depends(get_db)
        ):
    repository = TagRepository(db)
    return repository.list_tags(search=query,order_by=order_by,direction=direction,page=page,per_page=per_page)



@router.post("", response_model=TagPublic, response_description="Tag creado OK",status_code=status.HTTP_201_CREATED)
def create_tag(tag:TagCreate, db: Session=Depends(get_db),user=Depends(get_current_user)):
    repository = TagRepository(db)
    try:
        tag_created=repository.create_tag(tag.name)
        db.commit()
        db.refresh(tag_created)
        return tag_created
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el tag")

@router.put("/{tag_id}", response_model=TagPublic, status_code=status.HTTP_200_OK)
def update_tag(tag_id: int, data:TagUpdate, db: Session=Depends(get_db)):
    repository = TagRepository(db)
    tag = repository.update_tag(tag_id, data.name)
    db.commit()
    db.refresh(tag)
    return TagPublic.model_validate(tag)

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    repository = TagRepository(db)
    deleted_tag = repository.delete_tag(tag_id)
    if not deleted_tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.commit()
    return None

@router.get("/popular-tag")
def popular_tag(db: Session = Depends(get_db)):
    repository = TagRepository(db)
    row = repository.most_popular_tags()
    if not row:
        raise HTTPException(status_code=404, detail="No hay tag en la base de datos")
    return row