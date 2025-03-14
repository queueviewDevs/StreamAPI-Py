"""Models for admin accounts that give access to the API"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Annotated, List
from enum import Enum
from datetime import datetime, timezone
from bson import ObjectId

from pydantic.functional_validators import BeforeValidator
PyObjectId = Annotated[str, BeforeValidator(str)]

#-----alternate method of dealing w/ object ids:
# https://github.com/mongodb-developer/mongodb-with-fastapi/blob/master/app.py

# from pydantic.functional_validators import BeforeValidator
# PyObjectId = Annotated[str, BeforeValidator(str)]
# id: Optional[PyObjectId] = Field(alias="_id", default=None)
# class StudentModel(BaseModel):
#     id: Optional[PyObjectId] = Field(alias="_id", default=None)
        
        

class RoleEnum(str, Enum):
    admin = 'admin'
    manager = 'manager'
    standard = 'standard'



class UserBase(BaseModel):
    username: str = Field(...)
    name: str = Field(...)
    email: EmailStr = Field(...)
    role: RoleEnum = Field(default_value = RoleEnum.standard)
    disabled: bool = Field(default=False)
    
    
    
class User(UserBase):
    """Used for DB purposes. Model for return User data"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    hashed_pw: str = Field(..., description="The hashed password using SHA256")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = Field(None, description="Timestamp of last login")
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
    


class UserCreate(UserBase):
    """Used for creating a user object"""
    password: str = Field(..., description="The plaintext password")
    
    
    
class UserUpdate(BaseModel):
    """Used for updating a user object"""
    username: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    email: Optional[EmailStr] = Field(None)
    role: Optional[RoleEnum] = Field(None)
    
    
    
class UserCollection(BaseModel):
    """A container holding a list of `User` instances"""
    users: List[User]
    
    
class UserQuery(BaseModel):
    """A model used for querying the users collection"""
    username: Optional[str] = Field(None, description="Filter by username")
    name: Optional[str] = Field(None, description="Filter by name")
    email: Optional[bool] = Field(None, description="Filter by email")
    role: Optional[RoleEnum] = Field(None, description="Filter by role")
    disabled: Optional[bool] = Field(None, description="Filter by disabled users")