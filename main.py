"""
Запросы синхронны

"""
import asyncio
import json
import jwt
import shutil

from datetime import datetime, timedelta, timezone
from fastapi import Body, Depends, FastAPI, HTTPException, Request, Response, Path, status, Query
from fastapi_login import LoginManager 
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jwt.exceptions import InvalidTokenError
from models import Generator, User
from os import listdir, mkdir, remove
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from sqlmodel import Field, Session, SQLModel, create_engine, select

D_CONTAINER = "pyimage"
N_GENERATOR_ON_PAGE = 10
MAX_SIZE = 1024*1024*5
MAX_NUMBER_OF_FILES = 3

SECRET_KEY = "77755b481b50ed7967821b1a4bb98991559ae50ff07ac92786bc654fbb666c98"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

manager = LoginManager(SECRET_KEY, token_url="/token", use_cookie=True)
manager.cookie_name = "some-name"

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@manager.user_loader()
def get_user(username: str, session = Session(engine)) -> User:
    try:
        print(username)
        current_user = session.exec(select(User).filter(User.login==username)).one()
        print(current_user)
        return current_user
    except:
        return None    
    
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
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
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )
    resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp, access_token)
    return resp
    #response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    #return Token(access_token=access_token, token_type="bearer")

class UsrR(BaseModel):
    username : str
    name : str
    email : str
    password : str

@app.post("/register/")
async def new_user(session : SessionDep, user : UsrR):
    try:
        new_user = User(login=user.username, name = user.name, email = user.email, hashed_password=get_password_hash(user.password))        
        session.add(new_user)
        session.commit()
        mkdir(f"data/{user.username}")
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    except:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, 
                content={ "message": "Ошибка регистрации" }
        )

@app.post("/new_file/{login}/{generator_name}/{filename}")
async def new_file(login : str, generator_name : str, filename : str, user=Depends(manager)):
    if (user.login != login): 
        return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, 
                content={ "message": "HTTP_403_FORBIDDEN" }
        )
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
async def delete_file(login : str, generator_name : str, filename : str, user=Depends(manager)):
    if (user.login != login): 
        return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, 
                content={ "message": "HTTP_403_FORBIDDEN" }
        )
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
async def save_file(login : str, generator_name : str, filename : str, body : svF, user=Depends(manager)):
    if (user.login != login): 
        return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, 
                content={ "message": "HTTP_403_FORBIDDEN" }
        )
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

@app.get("/generators/{login}")
def get_generators(session : SessionDep, login : str, page : int = Query(1, ge=1)):
    generators = session.exec(select(Generator).filter(Generator.user_login == login).offset(N_GENERATOR_ON_PAGE * (page-1)).limit(N_GENERATOR_ON_PAGE)).all()
    print(generators)
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
def delete_generator(session : SessionDep, login : str, generator_name : str, user=Depends(manager)):
    if (user.login != login): 
        return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, 
                content={ "message": "HTTP_403_FORBIDDEN" }
        )
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
def edit_generator(session : SessionDep, user_login : str, generator_name : str, item: Generator, user=Depends(manager)):
    if (user.login != user_login): 
        return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, 
                content={ "message": "HTTP_403_FORBIDDEN" }
        )
    try:
        print(item)
        if (item.user_login != user_login or item.name != generator_name): 
            raise
        generator = session.exec(select(Generator).filter(Generator.user_login == user_login, Generator.name == generator_name)).one()
        generator.title = item.title
        generator.description = item.description
        session.add(generator)
        session.commit()
    except:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, 
                content={ "message": "HTTP_400_BAD_REQUEST" }
        )

@app.get("/", response_class=HTMLResponse)
def root(session : SessionDep, 
         request : Request, 
         page : int = Query(default=1, ge=1),
         user = Depends(manager.optional)
    ):
    total_amount_of_generators = len(session.exec(select(Generator)).all())
    number_of_pages = total_amount_of_generators // N_GENERATOR_ON_PAGE + (total_amount_of_generators % N_GENERATOR_ON_PAGE > 0)
    return templates.TemplateResponse(request=request, name="index.html", context={"current_user": user.login if user else '0', 
                                                                                   "page": page, 
                                                                                   "number_of_pages": number_of_pages}) 

@app.get("/{login}", response_class=HTMLResponse)
def user_page(session : SessionDep, 
         request : Request, 
         login : str,
         page : int = Query(default=1, ge=1),
         user = Depends(manager.optional)
    ):
    total_amount_of_generators = len(session.exec(select(Generator).filter(Generator.user_login==login)).all())
    number_of_pages = total_amount_of_generators // N_GENERATOR_ON_PAGE + (total_amount_of_generators % N_GENERATOR_ON_PAGE > 0)
    return templates.TemplateResponse(request=request, name="user.html", context={"current_user": user.login if user else '0', 
                                                                                   "user" : login,
                                                                                   "page": page, 
                                                                                   "number_of_pages": number_of_pages}) 

@app.get("/{login}/{generator_name}", response_class=HTMLResponse)
async def generator_page(session : SessionDep, request : Request, login : str, generator_name : str, args : list[str] = Query(default=[])):
    #number_of_pages = total_amount_of_generators // N_GENERATOR_ON_PAGE + (total_amount_of_generators % N_GENERATOR_ON_PAGE > 0)
    return templates.TemplateResponse(request=request, name="generator.html", context={"user_login": login, "name": generator_name} ) 

@app.get("/{login}/{generator_name}/edit", response_class=HTMLResponse)
async def edit_generator(session : SessionDep, 
                         request : Request, 
                         login : str, 
                         generator_name : str, 
                         args : list[str] = Query(default=[]),
                         user = Depends(manager.optional)):
    return templates.TemplateResponse(request=request, name="generator_edit.html", context={"current_user": user.login if user else '0', 
                                                                                            "user_login": login, 
                                                                                            "name": generator_name} ) 

@app.get("/register/", response_class=HTMLResponse)
async def get_register_page(request : Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.get("/login", response_class=HTMLResponse)
async def get_login_page(request : Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get('/logout', response_class=HTMLResponse)
def protected_route(user=Depends(manager)):
    resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp, "")
    return resp