from pydantic import BaseModel

class StreamCommand(BaseModel):
    stream: bool = False  # True for start, False for stop
    

class Token(BaseModel):
    access_token: str
    token_type: str
    

class TokenData(BaseModel):
    username: str | None = None