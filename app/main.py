import os

from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

from app.api.v1.posts.router import router as post_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.uploads.router import router as upload_router, MEDIA_DIR
from app.api.v1.tags.router import router as tags_router
from app.core.db import Base, engine

load_dotenv()

def create_app() -> FastAPI:
    app=FastAPI(title="MiniBlog")
    Base.metadata.create_all(bind=engine) #dev

    app.include_router(auth_router,prefix="/api/v1")
    app.include_router(post_router)
    app.include_router(upload_router)
    app.include_router(tags_router)

    os.makedirs(MEDIA_DIR,exist_ok=True)
    app.mount("/media",StaticFiles(directory=MEDIA_DIR),name="media")

    return app

app = create_app()