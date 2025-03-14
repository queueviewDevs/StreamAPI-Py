from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import datetime, timezone
from bson import ObjectId

from ..auth.auth import authenticate_user, create_access_token
from ..models.general import Token
from ..dependencies.db import users_collection

#Possible solution to passlib bcrypt dependency issue: https://github.com/pyca/bcrypt/issues/684#issuecomment-1902590553

router = APIRouter(
    prefix="/auth",
    tags=["Authorization"]
)

@router.post(
    path="/login",
    response_model=Token
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username}
    )
    
    #Update last login
    await users_collection.find_one_and_update(
        {"_id": ObjectId(user.id)},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    return Token(access_token=access_token, token_type="bearer")