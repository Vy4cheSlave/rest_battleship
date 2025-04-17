from src.config import jwt_settings
from src.schemas import UserAuthPublic, UserPublic, TokenWithRefresh
from src.models import User
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, Body, HTTPException, status, Header, WebSocket, Query, WebSocketException
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.api.dependencies import SessionDep
from sqlmodel import select, exists
from datetime import datetime, timedelta
from jwt.exceptions import InvalidTokenError
import jwt


auth_router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

LOGIN_URL = "/players/login"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES=15
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS=7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=LOGIN_URL)

def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, jwt_settings.jwt_secret_key, algorithm=jwt_settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, jwt_settings.jwt_secret_key, algorithm=jwt_settings.jwt_algorithm)
    return encoded_jwt

@auth_router.post("/players/register", response_model=UserPublic)
async def register_user(
    input_body: Annotated[UserAuthPublic, Body()], 
    async_session: SessionDep,
    ):
    user_is_exist = await async_session.execute(
        select(exists().where(User.username == input_body.username))
    )
    user_is_exist = user_is_exist.scalars().first()
    
    if user_is_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"User with name \"{input_body.username}\" already exists.")

    user_db = User.model_validate(input_body)
    user_db.password = get_password_hash(user_db.password)
    async_session.add(user_db)
    await async_session.commit()
    await async_session.refresh(user_db)
    return user_db

@auth_router.post(LOGIN_URL, response_model=TokenWithRefresh)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    async_session: SessionDep,
    ):
    incorrect_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_db = await async_session.execute(
        select(User).where(
            User.username==form_data.username,
        )
    )
    user_db = user_db.scalars().first()
    
    if not user_db:
        raise incorrect_exception
    if not verify_password(form_data.password, user_db.password):
        raise incorrect_exception

    access_token_expires = timedelta(minutes=jwt_settings.jwt_access_token_expire_minutes)
    refresh_token_expires = timedelta(days=jwt_settings.jwt_refresh_token_expire_days)
    access_token = create_access_token(data={"sub": user_db.username}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": user_db.username}, expires_delta=refresh_token_expires)

    return TokenWithRefresh(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@auth_router.post("/players/refresh_token", response_model=TokenWithRefresh)
async def refresh_token(
    x_refresh_token: Annotated[str, Header()],
    async_session: SessionDep,
    ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            x_refresh_token, 
            jwt_settings.jwt_secret_key, 
            algorithms=[jwt_settings.jwt_algorithm],
            )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        user_db = await async_session.execute(
        select(User).where(
            User.username==username,
            )
        )
        user_db = user_db.scalars().first()
        
        if not user_db:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    access_token_expires = timedelta(minutes=jwt_settings.jwt_access_token_expire_minutes)
    new_access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)

    return TokenWithRefresh(access_token=new_access_token, refresh_token=x_refresh_token, token_type="bearer")

async def check_access_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    async_session: SessionDep,
    ) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            jwt_settings.jwt_secret_key, 
            algorithms=[jwt_settings.jwt_algorithm],
            )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        user_db = await async_session.execute(
        select(User).where(
            User.username==username,
            )
        )
        user_db = user_db.scalars().first()
        
        if not user_db:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    return user_db

async def check_access_token_websocket(
    websocket: WebSocket,
    token: Annotated[str , Query()],
    async_session: SessionDep,
    ) -> User:
    credentials_exception = WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Error: Could not validate credentials"
        )
    try:
        payload = jwt.decode(
            token, 
            jwt_settings.jwt_secret_key, 
            algorithms=[jwt_settings.jwt_algorithm],
            )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        user_db = await async_session.execute(
        select(User).where(
            User.username==username,
            )
        )
        user_db = user_db.scalars().first()
        
        if not user_db:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    return user_db

    