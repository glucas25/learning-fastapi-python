
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.categories.repository import CategoryRepository
from app.api.v1.posts import repository
from app.core.db import get_db
from app.api.v1.categories.schemas import CategoryCreate, CategoryUpdate, CategoryPublic

router = APIRouter(prefix="/categories", tags=["categories"])


# @router.get("/paginated", response_model=dict)
# def list_categories_paginated(page:int, per_page:int, db: Session=Depends(get_db)):
#     repository =CategoryRepository(db)
#     total, categories = repository.list_with_total(page=page, per_page=per_page)
#     return {"total": total, "items": [CategoryPublic(name=category.name, slug=category.slug) for category in categories]}



@router.get("", response_model=list[CategoryPublic])
def list_categories(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)
    return repository.list_many(skip=skip, limit=limit)  
  
    


@router.post("", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    repository=CategoryRepository(db)
    exist=repository.get_by_slug(slug=data.slug)
    if exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug ya existe")
    category = repository.create(name=data.name, slug=data.slug)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryPublic)
def get_category(category_id: int, db: Session = Depends(get_db)):
    repository=CategoryRepository(db)
    category = repository.get(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    return category


@router.put("/{category_id}", response_model=CategoryPublic)
def update_category(category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)):
    repository=CategoryRepository(db)
    category = repository.get(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    update = repository.update(category, updates=data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(update)
    return update

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    repository=CategoryRepository(db)
    category = repository.get(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    repository.delete(category)
    db.commit()