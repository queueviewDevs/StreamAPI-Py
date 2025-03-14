from fastapi import Depends, HTTPException, status, WebSocket, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import hashlib

from ..schemas.user import User
from ..schemas.device import Device
from ..crud.users import get_user
from ..crud.devices import verify_api_key


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)



#Possible solution to passlib bcrypt dependency issue: https://github.com/pyca/bcrypt/issues/684#issuecomment-1902590553

SECRET_KEY = "056509aebe10c9cd862799f66bd169adef0a05f5f7d55e655ee641dc42a60494"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUES = 120
    
    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
api_key_scheme = APIKeyHeader(name="x-key", auto_error=False)


def hash_password(password: str) -> str:
    """Returns the hashed password"""
    return pwd_context.hash(password)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Returns true if the plain password hashes to the hashed password"""
    return pwd_context.verify(plain_password, hashed_password)



def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Returns a JWT string"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def decode_access_token(token: str) -> dict:
    """Returns the data from the token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except InvalidTokenError:
        raise credentials_exception


    
async def authenticate_user(username: str, password: str) -> User | None:
    user = await get_user(username)
    if user is None:
        return None
    if not verify_password(password, user.hashed_pw):
        return None
    return user



async def get_current_user(token: Optional[str] = Security(oauth2_scheme)):
    """The optional authentication dependency for users. This is used for endpoints with shared access"""
    if token:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            print("Cred ex in get_current_user")
            raise credentials_exception

        user = await get_user(username=username)
        if user is None:
            raise credentials_exception
        if user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user
    return None



async def get_current_device(api_key: Optional[str] = Security(api_key_scheme)) -> Device:
    """The optional authentication dependency for devices. This is used for endpoints with shared access"""
    if api_key:
        hashed_api_key = hashlib.sha256(api_key.encode()).hexdigest()
        device = await verify_api_key(hashed_api_key)
        
        if device is not None:
            return device
        
        else:
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    return None



async def get_current_client(
    jwt_user: Optional[User] = Depends(get_current_user),
    api_key_user: Optional[Device] = Depends(get_current_device)
):
    """The combined authentication dependency that handles JWT and API Key authentication for both user and device clients"""
    if jwt_user:
        return jwt_user
    if api_key_user:
        return api_key_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials via JWT or API key"
    )
    
    

#In order to have endpoints that should only be accessed by 1 type of client, we will create wrapper dependencies that override the Optional
async def authorize_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Wrapper dependency for endpoints strictly enforcing user auth only"""
    if current_user is None:
        raise credentials_exception
    return current_user


async def authorize_device(current_device: Optional[Device] = Depends(get_current_device)) -> Device:
    """Wrapper dependency for endpoints strictly enforcing device auth only"""
    if current_device is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return current_device
    


async def authenticate_websocket_user(websocket: WebSocket):
    """Extract and authenticate user from WebSocket headers."""
    
    api_key = websocket.headers.get("x-key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    # Explicitly call get_current_user first
    current_device = await get_current_device(api_key)
    
    # Now pass the user object instead of a token
    return current_device