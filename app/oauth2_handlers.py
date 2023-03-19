from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app import errors
from app.models import AWFAPIUser
from app.services import JWTAuthenticationService
from app.error_handlers import raise_400, raise_401, raise_500

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> AWFAPIUser:
    jwt_auth_service = JWTAuthenticationService()

    try:
        user = jwt_auth_service.get_user_from_token(token)
        return user

    except (errors.JWTTokenSignatureExpiredError, errors.InvalidCredentialsError) as e:
        raise_401(e)
    except Exception as e:
        raise_500(e)


async def get_current_active_user(current_user: AWFAPIUser = Depends(get_current_user)) -> AWFAPIUser:
    if current_user.is_readonly:
        raise_400(errors.InactiveUserError(f"{current_user.username}, Current user is inactive."))
    return current_user
