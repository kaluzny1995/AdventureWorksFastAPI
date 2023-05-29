class InvalidCredentialsError(Exception):
    """ Raised when user authentication failed """
    pass


class JWTTokenSignatureExpiredError(Exception):
    """ Raised when JWT token signature expired """
    pass


class ReadonlyUserError(Exception):
    """ Raised when current user has readonly restricted account access """
    pass


class UsernameAlreadyExistsError(Exception):
    """ Raised when provided username already exists in the database """
    pass


class EmailAlreadyExistsError(Exception):
    """ Raised when provided email already exists in the database """
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
