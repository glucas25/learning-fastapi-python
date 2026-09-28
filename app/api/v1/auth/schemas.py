from pydantic import BaseModel, ConfigDict

class Token(BaseModel):
    access_token: str
    type_token:str="bearer"

class TokenData(BaseModel):
    sub: str
    username: str

class UserPublic(BaseModel):
    email:str
    username:str

    model_config=ConfigDict(from_attributes=True)