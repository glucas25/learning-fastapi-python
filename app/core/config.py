import os


class settings():
    JWT_SECRET: str = os.getenv("SECRET_KEY", "change_me_in_prod")
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))