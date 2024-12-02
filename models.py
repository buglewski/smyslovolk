from enum import Enum
from sqlmodel import Field, SQLModel

"""
POSSIBLE MODS: naive_generic, py_generic

"""

class Generator(SQLModel, table=True):
    user_login : str = Field(default="admin", index=True, nullable=False, primary_key=True, foreign_key="user.login", min_length=3, max_length=20)
    name : str = Field(index=True, nullable=False, primary_key=True, min_length=3, max_length=20)
    title : str = Field(index=True, nullable=False, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=240)
    mod: str = Field(default="naive_generic")
    private: bool = Field(default=False)
    hidden: bool = Field(default=False)
    safe: bool = Field(default=False)
    

class User(SQLModel, table=True):
    login : str = Field(index=True, nullable=False, primary_key=True, min_length=3, max_length=20)
    name : str = Field(index=True, nullable=False, min_length=3, max_length=50)
    email : str | None = Field(default=None, max_length=50)
    hashed_password : str | None = Field(default=None)
    admin : bool = Field(default=False)


    


