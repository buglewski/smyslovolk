"""
Запросы синхронны

"""
import asyncio

from fastapi import Depends, FastAPI, status, Query
from fastapi.responses import JSONResponse
from models import Generator, User
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from sqlmodel import Field, Session, SQLModel, create_engine, select

import subprocess


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class FilterParams(BaseModel):
    id: int
    limit: int = Field(100, gt=0, le=100, title="Limit of some", description="meow!")
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = Field(default="created_at", description="MEOW!")
    tags: list[str] = []

class GenerationParams(BaseModel):
    login: str
    generator: str 
    kwarg: dict = Field({})

sqlite_file_name = "instance/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.get("/gen/{login}/{generator_name}/")
async def generate(session : SessionDep, login : str, generator_name : str, args : list[str] = Query(default=[])):
    try:
        generator = session.exec(select(Generator).filter(Generator.user_login == login, Generator.name == generator_name)).one()
    except:
        return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={ "message": "Генератор не найден" }
        )
    if generator.mod == 'naive_generic':
        path = f"data/{generator.user_login}/{generator.name}/{generator.name}.json"
        zhopa = subprocess.run(['python', 'naive_generator.py', path], capture_output=True, user="guess")
        return zhopa

    print(generator)
    return login

@app.post("/items/")
async def create_item(item: Item):
    return item


@app.get("/meow/{id}")
async def meow(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

@app.get("/{id}")
async def root(id : int = 0, data : list[int] = Query(title="Cat", description="MEOW", default=[1,1,1])):
    return {"message": "Hello World",
            "id" : id,
            "data": data}
