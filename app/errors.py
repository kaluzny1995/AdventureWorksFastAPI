class NotFoundError(Exception):
    """ Raised when the requested document does not exist """
    pass


class IntegrityError(Exception):
    """ Raised when the insertion/update violates some object db constraints """
    pass
