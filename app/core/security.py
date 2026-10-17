import os
from fastapi import Depends, HTTPException, status
import jwt
from typing import Optional
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

def raise_expired_token():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="No autenticado",
        headers={"WWW-Authenticate":"Beader"}
        )

def raise_forbiden():
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail="No tienes permisos suficientes",
        headers={"WWW-Authenticate":"Beader"}
        )

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



def decode_token(token:str) -> dict:
    playload = jwt.decode(jwt=token,key=settings.JWT_SECRET,algorithms=[settings.JWT_ALG])
    return playload

def get_current_user(db: Session= Depends(get_db()), token:  str = Depends(oauth2_scheme)):
    try:
        playload=decode_token(token)
        sub: Optional[str] = playload.get("sub")
        username: Optional[str]= playload.get("username")
        if not sub or not username:
            raise_expired_token()

        user_id=int(sub)
        #return {"email":sub, "username":username}
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expirado",
                            headers={"WWW-Authenticate":"Beader"}
                            )
    except InvalidTokenError:
        raise raise_expired_token()
    except jwt.PyJWTError:
        raise raise_expired_token()

    user = db.get(User, user_id)
    if not user:
        raise raise_forbiden()
    return user
    
def has_password(plain:str)-> str:
    return password_hash.hash(plain)

def verify_password(plain:str, hashed:str) -> bool:
    return password_hash.verify(plain, hashed)