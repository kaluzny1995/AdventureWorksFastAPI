from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Union

from app import errors
from app.models import AWFAPIUser, Token, get_response_models, EAuthenticationStatus
from app.services import JWTAuthenticationService
from app.oauth2_handlers import oauth2_scheme, get_current_user, get_current_nonreadonly_user
from app.error_handlers import raise_401, raise_500


router = APIRouter()

jwt_auth_service = JWTAuthenticationService()


@router.post("/token", response_model=Token, include_in_schema=False)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    try:
        user = jwt_auth_service.authenticate_user(form_data.username, form_data.password)
        access_token = jwt_auth_service.create_access_token(data={"sub": user.username})
        token_dict = {"access_token": access_token, "token_type": "bearer"}

        return Token(**token_dict)

    except errors.InvalidCredentialsError as e:
        raise_401(e)


@router.get("/verify/{password}", include_in_schema=False,
            responses=get_response_models(Dict[str, Union[str, bool]], [200, 401, 500]))
async def verify(password: str, token: str = Depends(oauth2_scheme)) -> Dict[str, Union[str, bool]]:
    try:
        user = jwt_auth_service.get_user_from_token(token)
        jwt_auth_service.authenticate_user(user.username, password)
        return dict(verified=True)
    except errors.InvalidCredentialsError as e:
        if "password" in str(e):
            return dict(verified=False)
        else:
            raise_401(e)
    except Exception as e:
        raise_500(e)


@router.get("/test", include_in_schema=False,
            responses=get_response_models(Dict[str, str], [200, 500]))
async def test(token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
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
            responses=get_response_models(Dict[str, str], [200, 401, 500]))
async def jwt_auth_test(token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    try:
        jwt_auth_service.get_access_token_payload(token)
        return dict(message="JWT Authentication works!", token=token)
    except (errors.JWTTokenSignatureExpiredError, errors.InvalidCredentialsError) as e:
        raise_401(e)
    except Exception as e:
        raise_500(e)


@router.get("/current_user", tags=["JWT Authentication Test"],
            responses=get_response_models(AWFAPIUser, [200, 401, 500]))
async def current_user_test(current_user: AWFAPIUser = Depends(get_current_user)) -> AWFAPIUser:
    return current_user


@router.get("/current_nonreadonly_user", tags=["JWT Authentication Test"],
            responses=get_response_models(AWFAPIUser, [200, 400, 401, 500]))
async def current_nonreadonly_user_test(
        current_nonreadonly_user: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> AWFAPIUser:
    return current_nonreadonly_user
