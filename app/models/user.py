from beanie import Document
from pydantic import EmailStr
from typing import Optional
from datetime import datetime


class User(Document):
    email: EmailStr
    password: str
    role: str
    created_at: Optional[datetime] = None

    class Settings:
        collection = "users"
