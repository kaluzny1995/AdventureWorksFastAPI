from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app import errors
from app.models import ResponseMessage, Token, AWFAPIUser, get_response_models, \
    EAuthenticationStatus, EPasswordVerificationStatus
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
            responses=get_response_models(ResponseMessage, [200, 401, 500]))
async def verify(password: str, token: str = Depends(oauth2_scheme)) -> ResponseMessage:
    try:
        user = jwt_auth_service.get_user_from_token(token)
        jwt_auth_service.authenticate_user(user.username, password)
        return ResponseMessage(title=EPasswordVerificationStatus.VERIFIED,
                               description="Users password is verified.",
                               code=status.HTTP_200_OK)
    except errors.InvalidCredentialsError as e:
        if "password" in str(e):
            return ResponseMessage(title=EPasswordVerificationStatus.UNVERIFIED,
                                   description="Users password is not verified.",
                                   code=status.HTTP_200_OK)
        else:
            raise_401(e)
    except Exception as e:
        raise_500(e)


@router.get("/test", include_in_schema=False,
            responses=get_response_models(ResponseMessage, [200, 500]))
async def test(token: str = Depends(oauth2_scheme)) -> ResponseMessage:
    try:
        jwt_auth_service.get_access_token_payload(token)
        return ResponseMessage(title=EAuthenticationStatus.AUTHENTICATED,
                               description=f"Users authentication status: {EAuthenticationStatus.AUTHENTICATED}.",
                               code=status.HTTP_200_OK)
    except errors.JWTTokenSignatureExpiredError:
        return ResponseMessage(title=EAuthenticationStatus.EXPIRED,
                               description=f"Users authentication status: {EAuthenticationStatus.EXPIRED}.",
                               code=status.HTTP_200_OK)
    except errors.InvalidCredentialsError:
        return ResponseMessage(title=EAuthenticationStatus.UNAUTHENTICATED,
                               description=f"Users authentication status: {EAuthenticationStatus.UNAUTHENTICATED}.",
                               code=status.HTTP_200_OK)
    except Exception as e:
        raise_500(e)


@router.get("/jwt_auth_test", tags=["JWT Authentication Test"],
            responses=get_response_models(ResponseMessage, [200, 401, 500]))
async def jwt_auth_test(token: str = Depends(oauth2_scheme)) -> ResponseMessage:
    try:
        jwt_auth_service.get_access_token_payload(token)
        return ResponseMessage(title="JWT Authentication works.",
                               description="JWT Authentication worked successfully.",
                               code=status.HTTP_200_OK)
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
