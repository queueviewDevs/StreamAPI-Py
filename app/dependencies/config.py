from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

sqlite_url = 'sqlite:///./queueview.db'

connect_args = {"check_same_thread": False}

engine = create_engine(sqlite_url, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)
    
# def get_session():
#     with Session(engine) as session:
#         yield session

def get_session():
    return Session(engine)
        
DatabaseDep = Annotated[Session, Depends(get_session)]

# This was a demo section to test adding data to db
# from .auth import get_password_hash
# from sqlmodel import select
# from ..models.users import User 
# def populate():
#     u1 = User(
#         name="Eric Muzzo",
#         username="ericmuzzo",
#         email="ericm02@me.com",
#         hashed_pw=get_password_hash("dirtbIke1*")
#     )
    
#     session = Session(engine)
#     session.add(u1)
#     session.commit()
#     session.close()
    
# def test():
#     with Session(engine) as session:
#         statement = select(User)
#         results = session.exec(statement)
#         for user in results:
#             print(user)