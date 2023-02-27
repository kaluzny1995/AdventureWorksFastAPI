class InvalidCredentialsError(Exception):
    """ Raised when user authentication failed """
    pass


class JWTTokenSignatureExpiredError(Exception):
    """ Raised when JWT token signature expired """
    pass


class NotFoundError(Exception):
    """ Raised when the requested document does not exist """
    pass


class IntegrityError(Exception):
    """ Raised when the insertion/update violates some object db constraints """
    pass


class EmptyFieldsError(Exception):
    """ Raised when all or certain group of fields are empty """
    pass
