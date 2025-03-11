from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from sqlmodel import select

from .config import get_session
from ..models.users import User

#Possible solution to passlib bcrypt dependency issue: https://github.com/pyca/bcrypt/issues/684#issuecomment-1902590553

SECRET_KEY = "056509aebe10c9cd862799f66bd169adef0a05f5f7d55e655ee641dc42a60494"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_DAYS = 1


class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    username: str | None = None


# class User(BaseModel):
#     username: str
#     email: str | None = None
#     full_name: str | None = None
#     disabled: bool | None = None
    
    
# class UserInDB(User):
#     hashed_password: str
    
    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)



def get_password_hash(password):
    return pwd_context.hash(password)



def get_user(username: str) -> User | None:
    session = get_session()
    results = session.exec(select(User).where(User.username == username))
    user = results.one_or_none()
    session.close()
    return user


    
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_pw):
        return False
    return user



def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            print("Cred ex in get_current_user")
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user



async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):

    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



async def authenticate_websocket_user(websocket: WebSocket):
    """Extract and authenticate user from WebSocket headers."""
    
    token_header = websocket.headers.get("Authorization")
    if not token_header or not token_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = token_header.split("Bearer ")[1]
    
    # Explicitly call get_current_user first
    current_user = await get_current_user(token)
    
    # Now pass the user object instead of a token
    return await get_current_active_user(current_user)