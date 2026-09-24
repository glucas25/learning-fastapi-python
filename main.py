import os
from datetime import datetime
from math import ceil
from tkinter.constants import CASCADE
from typing import Optional, List, Union, Literal


from fastapi import FastAPI, Query, Path, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from sqlalchemy import create_engine, Integer, String, Text, DateTime, select, func, UniqueConstraint, ForeignKey, \
    Table, Column
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column, relationship

DATABASE_URL = os.getenv("DATABASE_URL","sqlite:///./blog.db")
print("Conectado a: ", DATABASE_URL)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=True, future=True,**engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,autoflush=False,autocommit=False, class_=Session)

class Base(DeclarativeBase):
    pass

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey(
        "post.id", ondelete=CASCADE), primary_key=True),
    Column("tag_id", ForeignKey(
        "tags.id", ondelete=CASCADE), primary_key=True)
)


class AuthorORM(Base):
    __tablename__ = "authors"

    id:Mapped[int]=mapped_column(Integer,primary_key=True, index=True)
    name:Mapped[str]=mapped_column(String(100), nullable=False)
    email:Mapped[str]=mapped_column(String(100), unique=True, index=True)

    posts:Mapped[List["PostORM"]] = relationship(back_populates="author")

class TagsORM(Base):
    __tablename__ = "tags"

    id:Mapped[int]=mapped_column(Integer,primary_key=True, index=True)
    name:Mapped[str]=mapped_column(String(100), nullable=False, index=True)

    posts: Mapped[List["PostORM"]] = relationship(back_populates="tags")


class PostORM(Base):
    __tablename__ = "post"
    __table_args__ = (UniqueConstraint("title", name="unique_post_title"),)

    id:Mapped[int]=mapped_column(Integer,primary_key=True, index=True)
    title:Mapped[str]=mapped_column(String(100), nullable=False, index=True)
    content:Mapped[str]=mapped_column(Text, nullable=False)
    create_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.now)

    author_id:Mapped[Optional[int]]=mapped_column(ForeignKey("authors.id"))
    author: Mapped[Optional["AuthorORM"]]=relationship(back_populates="posts")

    tags:Mapped[List["TagsORM"]]=relationship(
        secondary=post_tags,
        back_populates="posts",
        lazy="selectin",
        passive_deletes=True,
    )



Base.metadata.create_all(bind=engine) #dev

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app=FastAPI(title="MiniBlog")

class Tag(BaseModel):
    name: str = Field(...,
        min_length=2,
        max_length=30,
        description="Nombre de la etiqueta",
        examples=["Python"]
    )

    model_config = ConfigDict(from_attributes=True) #Tambien acepta objetos, ORM, si no esta solo acepta diccionarios

class Autor(BaseModel):
    nombre: str = Field(
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
    autor: Optional[Autor] = None
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

    autor: Optional[Autor] = None
    tags: List[Tag] = Field(default_factory=list, description="Lista de etiquetas del post") # Crea una lista vacia por defecto

    @field_validator("title")
    @classmethod
    def title_not_allowed(cls, value:str)-> str:
        if "spam" in value.lower():
            raise ValueError("El titulo no puede contener la palabra 'spam'")
        return value

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

BLOG_POSTS = [
    {"id": 1, "title": "Primer Post", "content": "Este es el contenido del primer post"},
    {"id": 2, "title": "Segundo Post", "content": "Este es el contenido del segundo post"},
    {"id": 3, "title": "Tercer Post", "content": "Este es el contenido del tercer post"}
]

@app.get("/")
def home():
    return {'message': 'Bienvenido a mi MiniBlog'}


# #Query Params
# @app.get("/posts")
# def get_posts(query: str | None =Query(default=None, description="Query string para filtrar por titulos de los posts")):
#     if query:
#        result = [post for post in BLOG_POSTS if query.lower() in post["title"].lower()]
#        return {"posts": result, "query": query}
#     else:
#         return {"posts": BLOG_POSTS}

@app.get("/posts", response_model=PaginatedPosts)
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
        10, ge=1, le=50,
        description="Cantidad de resultados por pagina, entre 1 y 50"), 

    page: int=Query(
        1, ge=1,
        description="Numero de pagina, debe ser un entero mayor o igual a 1"),


    order_by: Literal["id", "title"]=Query(
        "id", 
        description="Campo por el cual ordenar los resultados, puede ser 'id' o 'title'"),

    direction: Literal["asc", "desc"]=Query(
        "asc", 
        description="Direccion del ordenamiento, puede ser 'asc' o 'desc'"),

    db:Session = Depends(get_db)

    ):

    #results = BLOG_POSTS
    results= select(PostORM) # Construye un objeto de consulta SQL interna de select * from post

    search_text = query or text

    if search_text:
       #results = [post for post in results if search_text.lower() in post["title"].lower()]
        results = results.where(PostORM.title.ilike(f"%{search_text}%"))

    #total = len(results)
    total = db.scalar(select(func.count()).select_from(results.subquery())) or 0
    total_pages = ceil(total / per_page) if total > 0 else 0  # Calcular el número total de páginas

    current_page = 1 if total_pages == 0 else min(page, total_pages) # Asegurarse de que la página actual no exceda el número total de páginas

    #results = sorted(results, key=lambda post: post[order_by], reverse=(direction=="desc"))
    if order_by == "id":
        order_col= PostORM.id
    else:
        order_col = func.lower(PostORM.title)

    results = results.order_by(order_col.asc() if direction == "asc" else order_col.desc())


    if total_pages==0:
        #items=[]
        items = List[PostORM]=[]
    else:
        start=(current_page-1)*per_page
        #items = [
        #    PostPublic.model_validate(post) for post in results[start:start+per_page]]
        items = db.execute(results.limit(per_page).offset(start)).scalars().all()

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
        search=search_text,
        items=items
    )


@app.get("/posts/by-tags", response_model=List[PostPublic])
def filter_by_tags(tags: List[str] = Query(
    ...,
    min_length=2,
    description="Una o mas etiquetas. Ejemplo: ?tags=python&tags=fastapi"
    )
):
    tags_lower=[tag.lower() for tag in tags]

    return [
        PostPublic.model_validate(post)
        for post in BLOG_POSTS
        if any(
            tag["name"].lower() in tags_lower
            for tag in post.get("tags", [])
        )
    ]



@app.get("/posts/{post_id}", response_model= Union[PostPublic, PostSummary], response_description="Post encontrado")
def get_post(post_id: int = Path(
        ..., ge=1,
        title="ID del post",
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


    # result=[post for post in BLOG_POSTS if post["id"]==post_id]
    # if result:
    #     post=result[0]
    #     if not include_content:
    #         return {"id": post["id"], "title": post["title"]}
    #     return post
    # else:




# # POST con QUERY PARAMS
# @app.post("/posts")
# def create_post(title: str = Query(..., description="Titulo del post"), content: str = Query(..., description="Contenido del post")):
#     new_id = max(post["id"] for post in BLOG_POSTS) + 1
#     new_post = {"id": new_id, "title": title, "content": content}
#     BLOG_POSTS.append(new_post)
#     return {"message": "Post creado exitosamente", "post": new_post}


# POST con BODY y Pydantic
@app.post("/posts", response_model=PostPublic, response_description="Post creado exitosamente", status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    new_post = PostORM(title=post.title, content=post.content)
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
        raise HTTPException(status_code=500, detail=str(e))
    # new_id=max(post["id"] for post in BLOG_POSTS)+1 if BLOG_POSTS else 1
    # new_post={"id": new_id,
    #         "title": post.title,
    #         "content": post.content,
    #         "tags": [tag.model_dump() for tag in post.tags],
    #         "autor": post.autor.model_dump() if post.autor else None}
    # BLOG_POSTS.append(new_post)
    # return new_post

# POST CON BODY
# @app.post("/posts")
# def create_post(post:dict=Body(...)):
#     if "title" not in post or "content" not in post:
#         raise HTTPException(status_code=400, detail="El post debe contener 'title' y 'content'")
#     if not str(post["title"]).strip() or not str(post["content"]).strip():
#         raise HTTPException(status_code=400, detail="El 'title' y 'content' no pueden estar vacíos")
#     new_id=max(post["id"] for post in BLOG_POSTS)+1 if BLOG_POSTS else 1
#     new_post={"id": new_id, "title": post["title"], "content": post["content"]}
#     BLOG_POSTS.append(new_post)
#     return {"message": "Post creado exitosamente", "post": new_post}

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


    # for index, post in enumerate(BLOG_POSTS):
    #     if post["id"]==post_id:
    #         BLOG_POSTS.pop(index)
    #         return
    # raise HTTPException(status_code=404, detail="Post no encontrado")