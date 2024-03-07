from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app import errors
from app.models import AWFAPIUser, E400BadRequest
from app.services import JWTAuthenticationService
from app.error_handlers import raise_400, raise_401, raise_500


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
jwt_auth_service = JWTAuthenticationService()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> AWFAPIUser:
    try:
        user = jwt_auth_service.get_user_from_token(token)
        return user

    except (errors.JWTTokenSignatureExpiredError, errors.InvalidCredentialsError) as e:
        raise_401(e)
    except Exception as e:
        raise_500(e)


async def get_current_nonreadonly_user(current_user: AWFAPIUser = Depends(get_current_user)) -> AWFAPIUser:
    error_message = (f"{E400BadRequest.READONLY_ACCESS_FOR_USER}: [{current_user.username}] "
                     f"Current user '{current_user.username}' has readonly restricted access.")
    if current_user.is_readonly:
        raise_400(errors.ReadonlyUserError(error_message))
    return current_user
