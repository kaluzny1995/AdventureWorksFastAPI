from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict

from app import errors
from app.models import AWFAPIUser, Token, Message, EAuthenticationStatus
from app.services import JWTAuthenticationService
from app.oauth2_handlers import oauth2_scheme, get_current_user
from app.error_handlers import raise_401, raise_500


router = APIRouter()


@router.post("/token", response_model=Token, include_in_schema=False)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    jwt_auth_service = JWTAuthenticationService()

    try:
        user = jwt_auth_service.authenticate_user(form_data.username, form_data.password)
        access_token = jwt_auth_service.create_access_token(data={"sub": user.username})
        token_dict = {"access_token": access_token, "token_type": "bearer"}

        return Token(**token_dict)

    except errors.InvalidCredentialsError as e:
        raise_401(e)


@router.get("/test", include_in_schema=False,
            responses={200: {"model": Dict[str, str]},
                       401: {"model": Dict[str, str]}, 500: {"model": Message}})
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
            responses={200: {"model": Dict[str, str]},
                       401: {"model": Message}, 500: {"model": Message}})
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
            responses={200: {"model": AWFAPIUser},
                       401: {"model": Message}, 500: {"model": Message}})
async def current_user_test(current_user: AWFAPIUser = Depends(get_current_user)) -> AWFAPIUser:
    return current_user
