import os
from fastapi import Depends, HTTPException, status
import jwt
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

SECRET_KEY = os.getenv("SECRET_KEY","change_me_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES","30"))


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

def create_access_token(data:dict,expires_delta:Optional[timedelta]=None):
    to_encode =data.copy()
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp":expire})
    token = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_token(token:str) -> dict:
    playload = jwt.decode(jwt=token,key=SECRET_KEY,algorithms=[ALGORITHM])
    return playload

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        playload=decode_token(token)
        sub: Optional[str] = playload.get("sub")
        username: Optional[str]= playload.get("username")
        if not sub or not username:
            raise_expired_token()
        return {"email":sub, "username":username}
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expirado",
                            headers={"WWW-Authenticate":"Beader"}
                            )
    except InvalidTokenError:
        raise raise_expired_token()
    
