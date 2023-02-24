from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from typing import Dict
import datetime as dt

from app.config import JWTAuthenticationConfig
from app.models import User, UserInDB, Token, TokenData
from app.services import JWTAuthenticationService

from app.temp_db import temp_users_db


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    jwt_auth_config = JWTAuthenticationConfig.from_json()
    jwt_auth_service = JWTAuthenticationService()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, jwt_auth_config.secret_key, algorithms=[jwt_auth_config.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = jwt_auth_service.get_user(temp_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    jwt_auth_config = JWTAuthenticationConfig.from_json()
    jwt_auth_service = JWTAuthenticationService()

    user = jwt_auth_service.authenticate_user(temp_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = dt.timedelta(minutes=jwt_auth_config.access_token_expire_minutes)
    access_token = jwt_auth_service.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    token_dict = {"access_token": access_token, "token_type": "bearer"}

    return Token(**token_dict)


@router.get("/jwt_auth_test", tags=["JWT Authentication Test"])
def jwt_auth_test(token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    return dict(message="JWT Authentication works!", token=token)


@router.get("/current_user", response_model=User, tags=["JWT Authentication Test"])
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
