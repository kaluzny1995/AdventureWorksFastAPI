import re
from typing import Dict, Tuple

from app import errors
from app.models import ForeignKeyErrorDetails, E400BadRequest


def get_filter_params(filter_string: str) -> Dict[str, str]:
    """
    Returns parsed dictionary of filtering parameters.

    Example filter string:
        "pt:GC,fnph:Joh,lnph:D"

    Should return:
        {'pt': "GC", 'fnph': "Joh", 'lnph': "D"}
    """
    try:
        filter_params = dict(map(lambda p: p.split(":"), filter_string.split(",")))
    except ValueError:
        raise errors.InvalidFilterStringError(f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                              f"Invalid filter string: {filter_string}.")

    return filter_params


def get_username_from_message(error_message: str) -> str:
    """
    Returns parsed username from error message.

    Example error message:
        E400_000: [testuser] Current user 'testuser' has readonly restricted access.

    Should return:
        "testuser"
    """

    return re.findall(r"\[(.*?)]", error_message)[0]


def get_unique_field_details_from_message(error_message: str) -> Tuple[str, str]:
    """
    Returns parsed unique field name and unique constraint violating value from error message.

    Example error message:
        E400_001: [username] [testuser]
        Field 'username' must have unique values. Provided username 'testuser' already exists.

    Should return:
        ("username", "testuser")
    """

    field, value = tuple(re.findall(r"\[(.*?)]", error_message))
    return field, value


def get_validation_error_details_from_message(error_message: str,
                                              is_required_skipped: bool = False) -> Tuple[str, Dict[str, str]]:
    """
    Returns parsed object validation error details from error message.

    Example error message:
        E422_001: 1 validation error for Request\n
        body -> first_name
            field required (type=value_error.missing)
        email_promotion
            ensure this value is less than or equal to 2 (type=value_error.number.not_le; limit_value=2)

    Should return:
        ("1 validation error for Request",
        {'first_name': "field required", 'email_promotion': "ensure this value is less than or equal to 2"})
    """

    lines = error_message.split("\n")
    title = lines[0][10:].strip()
    error_details = list(map(lambda i: (lines[1:][i*2], lines[1:][i*2+1]), range(len(lines[1:])//2)))
    error_dict = dict(map(lambda ed: (ed[0].strip().replace("body -> ", ""),
                                      re.sub(r" [(\[].*?[)\]]", "", ed[1].strip())),
                          error_details))
    if is_required_skipped:
        error_dict = dict(filter(lambda ed: "field required" not in ed[1], error_dict.items()))

    return title, error_dict


def get_foreign_key_violence_details(error_message: str) -> ForeignKeyErrorDetails:
    """
    Returns parsed foreign key violation details from error message.

    Example error message:
        E400_003: (psycopg2.errors.ForeignKeyViolation) insert or update on table "PersonPhone"
        violates foreign key constraint "FK_PersonPhone_PhoneNumberType_PhoneNumberTypeID"\n
        DETAIL:  Key (PhoneNumberTypeID)=(10) is not present in table "PhoneNumberType".

    Should return:
        ForeignKeyErrorDetails(entity="PhoneNumberType", key_column="PhoneNumberTypeID", key_value="10")
    """

    line_of_interest = error_message.split("\n")[1]
    name = re.findall(r"\"(.*?)\"", line_of_interest)[0]
    column, value = tuple(re.findall(r"\((.*?)\)", line_of_interest))

    return ForeignKeyErrorDetails(entity=name, key_column=column, key_value=value)
