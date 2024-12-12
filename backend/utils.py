import os
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def create_jwt(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

