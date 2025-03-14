from fastapi import APIRouter, HTTPException, Depends, status, Response, Query
from fastapi.responses import JSONResponse
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from typing import Optional
import re

from ..dependencies.db import users_collection
from ..schemas.user import User, UserCreate, UserUpdate, UserCollection, UserQuery
from ..auth.auth import hash_password

router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)


@router.get(
    path="/",
    response_description="Get all users",
    response_model=UserCollection,
    response_model_by_alias=False
)
async def get_users(query: UserQuery = Depends(), q: Optional[str] = Query(None, description="Search query string to match any values")) -> UserCollection:
    """
    List all of the users in the database. Search querying is supported on fields username, name, email, and _id
    
    The response is unpaginated and limited to 1000 results
    """
    filters = query.model_dump(exclude_none=True)
    mongo_query = filters.copy() if filters else {}
    
    if q:
        search_clause = {
            "$or": [
                {"username": {"$regex": re.escape(q), "$options": "i"}},
                {"name": {"$regex": re.escape(q), "$options": "i"}},
                {"email": {"$regex": re.escape(q), "$options": "i"}},
                {"_id": {"$regex": re.escape(q), "$options": "i"}}
            ]
        }
        
        if mongo_query:
            mongo_query = {"$and": [mongo_query, search_clause]}
        else:
            mongo_query = search_clause
    
    users = await users_collection.find(mongo_query).to_list(1000)
    return UserCollection(users=users)



@router.get(
    path="/{id}",
    response_description="Get single user",
    response_model=User,
    response_model_by_alias=False
)
async def get_user(id: str) -> User:
    """Get a single user by their _id"""
    user = await users_collection.find_one({"_id": ObjectId(id)})
    if user:
        return user
    
    raise HTTPException(status_code=404, detail=f"User with {id} not found")



@router.post(
    path="/",
    description="Create a user",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False
)
async def create_user(user: UserCreate) -> User:
    """Create a user"""
    
    #Construct a User Object
    user = User(
        username=user.username,
        name=user.name,
        email=user.email,
        role=user.role,
        hashed_pw=hash_password(user.password)
    )
    
    try:
        new_user = await users_collection.insert_one(user.model_dump(by_alias=True, exclude=["id"]))
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail=f"A user with the provided username or email already exist")
    
    created_user = await users_collection.find_one({"_id": new_user.inserted_id})
    return created_user



@router.put(
    path="/{id}",
    description="Update a user",
    response_model=User,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False
)
async def update_user(id: str, user: UserUpdate) -> User:
    """Update a user by its _id"""
    update_payload = user.model_dump(by_alias=True, exclude_none=True)
    
    if len(update_payload) >= 1:
        
        try:
            update_result = await users_collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": update_payload},
                return_document=ReturnDocument.AFTER
            )
        except DuplicateKeyError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Duplicate key error",
                    "message": "Record with given unique username or email already exists"
                }
            )
        
        if update_result:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"User with {id} not found")
    
    #Update is empty, but still return the matching document
    existing_user = await users_collection.find_one({"_id": ObjectId(id)})
    if existing_user:
        return existing_user
    
    raise HTTPException(status_code=404, detail=f"User with {id} not found")



@router.delete(
    path="/{id}",
    description="Delete a user"
)
async def delete_user(id: str):
    """Delete a user by it's _id"""
    delete_result = await users_collection.delete_one({"_id": ObjectId(id)})
    
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    raise HTTPException(status_code=404, detail=f"User with {id} not found")