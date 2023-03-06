from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict

from app import errors
from app.models import UserInput, User, Token, Message, EAuthenticationStatus
from app.services import JWTAuthenticationService
from app.error_handlers import raise_400, raise_401, raise_500

from app.temp_db import temp_users_db


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    jwt_auth_service = JWTAuthenticationService()

    try:
        user = jwt_auth_service.get_user_from_token(token)
        return user

    except errors.JWTTokenSignatureExpiredError as e:
        raise_401(e)
    except errors.InvalidCredentialsError as e:
        raise_401(e)
    except Exception as e:
        raise_500(e)


async def get_current_active_user(current_user: UserInput = Depends(get_current_user)) -> UserInput:
    if current_user.is_disabled:
        raise_400(Exception(f"{current_user.username}, Current user is inactive."))
    return current_user


@router.post("/token", response_model=Token, include_in_schema=False)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    jwt_auth_service = JWTAuthenticationService()
    credentials_exception = errors.InvalidCredentialsError("Incorrect username or password.")

    user = jwt_auth_service.authenticate_user(temp_users_db, form_data.username, form_data.password)
    if user is None:
        raise_401(credentials_exception)

    access_token = jwt_auth_service.create_access_token(data={"sub": user.username})
    token_dict = {"access_token": access_token, "token_type": "bearer"}

    return Token(**token_dict)


@router.get("/test", include_in_schema=False,
            responses={200: {"model": Dict[str, str]}, 401: {"model": Dict[str, str]}, 500: {"model": Message}})
async def test(token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    jwt_auth_service = JWTAuthenticationService()

    try:
        jwt_auth_service.get_access_token_payload(token)
        return dict(message=EAuthenticationStatus.AUTHENTICATED)
    except errors.JWTTokenSignatureExpiredError:
        return dict(message=EAuthenticationStatus.EXPIRED)
    except errors.InvalidCredentialsError:
        return dict(message=EAuthenticationStatus.UNAUTHENTICATED)
    except Exception as e:
        raise_500(e)


@router.get("/jwt_auth_test", tags=["JWT Authentication Test"],
            responses={200: {"model": Dict[str, str]}, 401: {"model": Message}, 500: {"model": Message}})
async def jwt_auth_test(token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    jwt_auth_service = JWTAuthenticationService()

    try:
        jwt_auth_service.get_access_token_payload(token)
        return dict(message="JWT Authentication works!", token=token)

    except errors.JWTTokenSignatureExpiredError as e:
        raise_401(e)
    except errors.InvalidCredentialsError as e:
        raise_401(e)
    except Exception as e:
        raise_500(e)


@router.get("/current_user", tags=["JWT Authentication Test"],
            responses={200: {"model": UserInput}, 400: {"model": Message},
                       401: {"model": Message}, 500: {"model": Message}})
async def read_users_me(current_user: UserInput = Depends(get_current_active_user)) -> UserInput:
    return current_user
