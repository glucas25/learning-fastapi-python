
from fastapi import APIRouter, Depends, HTTPException, status,Path
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User
from .repository import UserRepository
from .schemas import TokenResponse, UserPublic, UserCreate, UserLogin, RoleUpdate
from app.core.security import auth2_token, create_access_token, get_current_user, hash_password, verify_password, require_admin

router = APIRouter(prefix="/auth",tags=["auth"])

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate,
             db: Session =Depends(get_db)
             ):
    repository=UserRepository(db)
    if repository.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    user = repository.create(
        email = payload.email,
        hashed_password = hash_password(payload.password),
        full_name = payload.full_name
    )
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user)

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login (payload:UserLogin, db: Session = Depends(get_db)):
    repository=UserRepository(db)
    user = repository.get_by_email(payload.email)
    if not user or not verify_password(payload.password,user.hashed_password):
        raise HTTPException(status_code =status.HTTP_401_UNAUTHORIZED,
                            detail="Credenciales invalidas")
    token=create_access_token(sub=str(user.id))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))
    
@router.get("/me", response_model=UserPublic)
def read_me(current:User =Depends(get_current_user)):
    return UserPublic.model_validate(current)

@router.put("/role/{user_id}", response_model=UserPublic)
def set_role(user_id: int = Path(..., ge=1),
             payload:RoleUpdate =None,
             db: Session = Depends(get_db),
             _admin:User = Depends(require_admin)
             ):
    repository=UserRepository(db)
    user = repository.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    updated = repository.set_role(user, payload.role)
    return UserPublic.model_validate(updated)

@router.post("/token")
async def token_endpoint(response = Depends(auth2_token)):
    return response