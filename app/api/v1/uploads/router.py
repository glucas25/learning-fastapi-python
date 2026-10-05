
from fastapi import APIRouter, File, UploadFile
from app.services.file_storage import save_upload_file

router = APIRouter(prefix="/upload", tags=["uploads"])
MEDIA_DIR = "app/media"

# @router.post("/bytes")
# async def upload_bytes(file: bytes = File(...)):
#     return {"filename": "archivo_subido",
#             "size_bytes": len(file)}
#
#
# @router.post("/file")
# async def upload_file(file: UploadFile = File(...)):
#     return {"filename": file.filename,
#             "content_type": file.content_type}

@router.post("/save")
async def save_file(file: UploadFile = File(...)):
    saved_file = save_upload_file(file)
    return {
        "filename": saved_file["filename"],
        "content_type": saved_file["content_type"],
        "url": saved_file["url"],
        "size": saved_file["size"],
        "chunk_size_used": saved_file["chunk_size_used"] ,
        "chunk_calls": saved_file["chunk_calls"],
        "chunk_size_sample": saved_file["chunk_size_sample"],
    }