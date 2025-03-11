"""Models for admin accounts that give access to the API"""

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

class UserBase(SQLModel):
    name: str = Field(index=True)
    username: str = Field(index=True, unique=True)
    disabled: bool = Field(default=False)
    
class User(UserBase, table=True):
    """Used for DB purposes"""
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    hashed_pw: str = Field(...)
    
class UserModel(UserBase):
    id: int