from enum import Enum


class EConstraintViolation(str, Enum):
    UNIQUE_VIOLATION = "UniqueViolation"
    FOREIGN_KEY_VIOLATION = "ForeignKeyViolation"
