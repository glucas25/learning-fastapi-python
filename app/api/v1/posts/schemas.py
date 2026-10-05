from fastapi import Form
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import List, Optional, Literal, Annotated


class Tag(BaseModel):
    name: str = Field(...,
        min_length=2,
        max_length=30,
        description="Nombre de la etiqueta",
        examples=["Python"]
    )

    model_config = ConfigDict(from_attributes=True) #Tambien acepta objetos, ORM, si no esta solo acepta diccionarios

class Author(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nombre de la persona",
        examples=["Juan Perez"])
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class PostBase(BaseModel):
    title: str
    content: str
    author: Optional[Author] = None
    image_url: Optional[str] = None
    tags: Optional[List[Tag]] = Field(default_factory=list, description="Lista de etiquetas del post") # Crea una lista vacia por defecto

class PostCreate(BaseModel):
    title: str= Field(
        ...,
        min_length=3,
        max_length=100,
        description="Titulo del post - minimo 3 caracteres y maximo 100",
        examples=["Mi primer post con FastAPI"])
    content: str = Field(
        default="Contenido por defecto", 
        min_length=10,
        description="Contenido del post - minimo 10 caracteres",
        examples=["Este es el contenido de mi primer post con FastAPI"])

    #author: Optional[Author] = None
    tags: List[Tag] = Field(default_factory=list, description="Lista de etiquetas del post") # Crea una lista vacia por defecto

    @field_validator("title")
    @classmethod
    def title_not_allowed(cls, value:str)-> str:
        if "spam" in value.lower():
            raise ValueError("El titulo no puede contener la palabra 'spam'")
        return value

    @classmethod
    def as_form(
            cls,
            title: Annotated[str, Form(min_length=3)],
            content: Annotated[str, Form(min_length=10)],
            tags: Annotated[Optional[List[str]],Form()] = None,
            ):
        tag_objs = [Tag(name=t) for t in (tags or [])]
        return cls(title=title, content=content, tags=tag_objs)

class PostUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=100, description="Titulo del post - minimo 3 caracteres y maximo 100")
    content: str
    
class PostPublic(PostBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
    
class PostSummary(BaseModel):
    id: int
    title: str

class PaginatedPosts(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: Literal["id", "title"]
    direction: Literal["asc", "desc"]
    search: Optional[str] = None
    items: List[PostPublic]
