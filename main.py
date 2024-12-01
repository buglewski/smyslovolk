"""
Запросы синхронны

"""
import asyncio
import json
import shutil

from fastapi import Body, Depends, FastAPI, Request, Path, status, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import Generator, User
from os import listdir, mkdir, remove
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from sqlmodel import Field, Session, SQLModel, create_engine, select

D_CONTAINER = "meowmeow2"
N_GENERATOR_ON_PAGE = 10
MAX_SIZE = 1024*1024*5
MAX_NUMBER_OF_FILES = 3

sqlite_file_name = "instance/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

#total_amount_of_generators = len(Session(engine).exec(select(Generator)).all())

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

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


@app.post("/new_file/{login}/{generator_name}/{filename}")
async def new_file(login : str, generator_name : str, filename : str):
    try:
        path = f"./data/{login}/{generator_name}"
        fls = listdir(path)
        if (filename in fls or len(fls) + 1 > MAX_NUMBER_OF_FILES or len(filename) > 20):
            raise
        f = open(f"data/{login}/{generator_name}/{filename}", "w")
        f.close()
    except:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, 
                content={ "message": "Ошибка создания файла" }
        )
    
@app.delete("/delete_file/{login}/{generator_name}/{filename}")
async def delete_file(login : str, generator_name : str, filename : str):
    try:
        path = f"./data/{login}/{generator_name}/{filename}"
        remove(path)
    except:
        return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={ "message": "Не обнаружен файл" }
        )


@app.get("/get_file/{login}/{generator_name}/{filename}")
async def get_file(login : str, generator_name : str, filename : str):
    try:
        f = open(f"data/{login}/{generator_name}/{filename}")
        data = f.read()
        return data
    except:
        return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={ "message": "Файл не найден" }
        )

class svF(BaseModel):
    text : str = Field(max_length=MAX_SIZE)

@app.put("/save_file/{login}/{generator_name}/{filename}")
async def save_file(login : str, generator_name : str, filename : str, body : svF):
    try:
        f = open(f"data/{login}/{generator_name}/{filename}", "w")
        f.write(body.text)
        f.close()
    except:
        return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                content={ "message": "Файл не найден" }
        )



@app.get("/get_generator/{login}/{generator_name}")
async def get_generator(session : SessionDep, login : str, generator_name : str, args : list[str] = Query(default=[])):
    try:
        generator = session.exec(select(Generator).filter(Generator.user_login == login, Generator.name == generator_name)).one()
        path = f"./data/{login}/{generator_name}"
        return { "generator": generator, "files" : listdir(path) }
    
    except:
        return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={ "message": "Генератор не найден" }
        )


@app.get("/gen/{login}/{generator_name}")
async def generate(session : SessionDep, login : str, generator_name : str, args : list[str] = Query(default=[])):
    try:
        generator = session.exec(select(Generator).filter(Generator.user_login == login, Generator.name == generator_name)).one()
    except:
        return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={ "message": "Генератор не найден" }
        )
    if generator.mod == 'naive_generic':
        json_path = f"data/{generator.user_login}/{generator.name}/{generator.name}.json"
        py_path = f"data/naive_generator.py"
        zhopa = await asyncio.create_subprocess_shell(f'python3 {py_path} {json_path}', stdout=asyncio.subprocess.PIPE, limit=MAX_SIZE)
        line = await zhopa.communicate()
        return line
    elif generator.mod == 'py_generic':
        path = f"data/{generator.user_login}/{generator.name}"
        argv = ' '.join(args)
        zhopa = await asyncio.create_subprocess_shell(f'docker run -i -d {D_CONTAINER}', stdout=asyncio.subprocess.PIPE)
        container_id = (await zhopa.communicate())[0].decode()[:12]
        zhopa = await asyncio.create_subprocess_shell(f'docker cp {path} {container_id}:a', stdout=asyncio.subprocess.PIPE)
        zhopa = await asyncio.create_subprocess_shell(f'docker exec {container_id} bin/bash -c "cd a; timeout 30s python3 {generator_name}.py {argv}"', stdout=asyncio.subprocess.PIPE, limit=MAX_SIZE)
        line = await zhopa.communicate()
        zhopa = await asyncio.create_subprocess_shell(f'docker kill {container_id}', stdout=asyncio.subprocess.PIPE)
        return line

    print(generator)
    return login

@app.get("/generators/")
def get_generators(session : SessionDep, page : int = Query(1, ge=1)):
    generators = session.exec(select(Generator).offset(N_GENERATOR_ON_PAGE * (page-1)).limit(N_GENERATOR_ON_PAGE)).all()
    return generators

class CreateGenerator(BaseModel):
    generator: Generator

@app.post("/create_generator/")
def create_generator(session : SessionDep, item: Generator):
    print(item)
    try:
        session.add(item)
    except:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "Ошибка добавления генератора"})
    try:
        mkdir(f"data/{item.user_login}/{item.name}")
    except:
        pass
    if item.mod == 'naive_generic':
        json_path = f"data/{item.user_login}/{item.name}/{item.name}.json"
        f = open(json_path, 'w', encoding='UTF-8')
        f.write(json.dumps({"morphems": [["mor1 ", "mor 2 "], ["mor 3", "mor 4"]]}))
        f.close()
    try:
        session.commit()
    except:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "Ошибка добавления генератора (SQL commit)"})
    return f"{item.user_login}/{item.name}"

@app.delete("/delete_generator/{login}/{generator_name}")
def delete_generator(session : SessionDep, login : str, generator_name : str):
    try:
        generator = session.exec(select(Generator).filter(Generator.user_login == login, Generator.name == generator_name)).one()
        session.delete(generator)
        session.commit()
    except:
        return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={ "message": "Генератор не найден" }
        )
    try:
        shutil.rmtree(f"data/{login}/{generator_name}", ignore_errors=True)
    except:
        pass
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "successfully deleted"}
    )

@app.post("/edit_generator/{user_login}/{generator_name}")
def edit_generator(session : SessionDep, user_login : str, generator_name : str, item: Generator):
        print(item)
        if (item.user_login != user_login or item.name != generator_name): 
            raise
        generator = session.exec(select(Generator).filter(Generator.user_login == user_login, Generator.name == generator_name)).one()
        generator.title = item.title
        generator.description = item.description
        session.add(generator)
        session.commit()

@app.get("/meow")
async def meow(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

@app.get("/", response_class=HTMLResponse)
def root(session : SessionDep, request : Request, page : int = Query(default=1, ge=1)):
    total_amount_of_generators = len(Session(engine).exec(select(Generator)).all())
    number_of_pages = total_amount_of_generators // N_GENERATOR_ON_PAGE + (total_amount_of_generators % N_GENERATOR_ON_PAGE > 0)
    return templates.TemplateResponse(request=request, name="index.html", context={"page": page, "number_of_pages": number_of_pages}) 

@app.get("/{login}/{generator_name}", response_class=HTMLResponse)
async def generator_page(session : SessionDep, request : Request, login : str, generator_name : str, args : list[str] = Query(default=[])):
    #number_of_pages = total_amount_of_generators // N_GENERATOR_ON_PAGE + (total_amount_of_generators % N_GENERATOR_ON_PAGE > 0)
    return templates.TemplateResponse(request=request, name="generator.html", context={"user_login": login, "name": generator_name} ) 

@app.get("/{login}/{generator_name}/edit", response_class=HTMLResponse)
async def edit_generator(session : SessionDep, request : Request, login : str, generator_name : str, args : list[str] = Query(default=[])):
    return templates.TemplateResponse(request=request, name="generator_edit.html", context={"user_login": login, "name": generator_name} ) 
