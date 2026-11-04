import os
from fastapi import Depends, HTTPException, status
import jwt
from typing import Optional, Literal
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.db import get_db
from app.models import User

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def raise_forbiden():
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail="No tienes permisos suficientes",
        headers={"WWW-Authenticate":"Beader"}
        )

def raise_user_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Usuario no encontrado",
                         headers={"WWW-Authenticate":"Beader"}
                         )

def raise_expired_token():
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expirado",
                            headers={"WWW-Authenticate":"Beader"}
                            )

def decode_token(token:str) -> dict:
    playload = jwt.decode(jwt=token,key=settings.JWT_SECRET,algorithms=[settings.JWT_ALG])
    return playload

# def create_access_token(data:dict,expires_delta:Optional[timedelta]=None):
#     to_encode =data.copy()
#     expire = datetime.now(tz=timezone.utc) + (
#         expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp":expire})
#     token = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
#     return token

def create_access_token(sub: str, minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": sub, "exp": expire}, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def get_current_user(db: Session = Depends(get_db), tokenData:  str = Depends(oauth2_scheme)) -> User:
    try:
        playload=decode_token(tokenData)
        sub: Optional[str] = playload.get("sub")
        username: Optional[str]= playload.get("username")
        if not sub or not username:
            raise_expired_token()

        user_id=int(sub)
        #return {"email":sub, "username":username}
    except ExpiredSignatureError:
        raise raise_expired_token()
    except InvalidTokenError:
        raise raise_user_not_found()
    except jwt.PyJWTError:
        raise raise_expired_token()

    user = db.get(User, user_id)
    if not user:
        raise raise_user_not_found()
    return user
    
def hash_password(plain:str)-> str:
    return password_hash.hash(plain)

def verify_password(plain:str, hashed:str) -> bool:
    return password_hash.verify(plain, hashed)

def require_role(min_role: Literal["user","editor","admin"]):
    order ={"user":0,"editor":1,"admin":2}

    def evaluation(user:User = Depends(get_current_user)) -> User:
        if order[user.role]<order[min_role]:
            raise raise_expired_token()
        return user
    return evaluation

require_user = require_role("user")
require_editor = require_role("editor")
require_admin = require_role("admin")
