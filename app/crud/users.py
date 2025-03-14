from ..dependencies.db import users_collection
from ..schemas.user import User

async def get_user(username: str) -> User | None:
    """Fetches the user from the database. Currently only used for authentication"""
    user = await users_collection.find_one({"username": username})
    if user is not None:
        return User(**user)
    return None