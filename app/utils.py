import re
from typing import Dict, Tuple, Union, List

from app import errors
from app.models import PrimaryKeyErrorDetails, ForeignKeyErrorDetails, E400BadRequest


def get_filter_params(filter_string: str) -> Dict[str, str]:
    """
    Returns parsed dictionary of filtering parameters.

    Example filter strings:
        1) "pt:GC,fnph:Joh,lnph:D"
        2) "pt:3,fnph:Joh,lnph:D"
        3) "pt:3,fnph:[Joh|Doe|Foe],lnph:D"
        4) "pt:3,fnph:Joh,lnph:[3|6|21]"

    Should return:
        1) {'pt': "GC", 'fnph': "Joh", 'lnph': "D"}
        2) {'pt': 3, 'fnph': "Joh", 'lnph': "D"}
        3) {'pt': 3, 'fnph': ["Joh", "Doe", "Foe"], 'lnph': "D"}
        4) {'pt': 3, 'fnph': "Joh", 'lnph': [3, 6, 21]}
    """
    try:
        filter_params = dict(map(lambda p: p.split(":"), filter_string.split(",")))
    except ValueError:
        raise errors.InvalidFilterStringError(f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                              f"Invalid filter string: {filter_string}.")

    return filter_params


def adjust_filter_params(filter_params: Dict[str, str]) -> Dict[str, Union[int, float, str, List[int], List[float], List[str]]]:
    """
    Adjusts the types of values in filter parameters dictionary.

    Example parameter dictionaries:
        1) {'pt': "GC", 'fnph': "Joh", 'lnph': "D"}
        2) {'pt': "3", 'fnph': "Joh", 'lnph': "D"}
        3) {'pt': "3", 'fnph': "[Joh|Doe|Foe]", 'lnph': "D"}
        4) {'pt': "3.1", 'fnph': "Joh", 'lnph': "[3|6|21]"}

    Should return:
        1) {'pt': "GC", 'fnph': "Joh", 'lnph': "D"}
        2) {'pt': 3, 'fnph': "Joh", 'lnph': "D"}
        3) {'pt': 3, 'fnph': ["Joh", "Doe", "Foe"], 'lnph': "D"}
        4) {'pt': 3.1, 'fnph': "Joh", 'lnph': [3, 6, 21]}
    """

    def __is_int(v: str) -> bool:
        """ Checks if the value type is an integer """
        try:
            int(v)
            return True
        except ValueError:
            return False

    def __is_float(v: str) -> bool:
        """ Checks if the value type is a floating point """
        try:
            float(v)
            return True if "." in v else False
        except ValueError:
            return False

    def __is_list(v: str) -> bool:
        """ Checks if the value type is a list """
        return True if v.startswith("[") and v.endswith("]") else False

    def __is_list_of_ints(vl: List[Union[int, float, str]]) -> bool:
        """ Checks if all list item types are integers """
        return all(list(map(lambda k: __is_int(k), vl)))

    def __is_list_of_floats(vl: List[Union[int, float, str]]) -> bool:
        """ Checks if all list item types are integers """
        return all(list(map(lambda k: __is_float(k), vl)))

    def __get_list(v: str) -> Union[List[int], List[float], List[str]]:
        """ Returns a list of integer, float or string values from given string value"""
        vl = v[1:-1].split("|")
        if __is_list_of_ints(vl):
            return list(map(lambda k: int(k), vl))
        elif __is_list_of_floats(vl):
            return list(map(lambda k: float(k), vl))
        else:
            return vl

    def __validate(v: str) -> None:
        """ Checks if value does not contain '[' or ']' characters in inappropriate places and raises error if so """
        if __is_list(v):
            if "[" in v[1:-1] or "]" in v[1:-1]:
                raise errors.InvalidFilterStringError(f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                                      f"Wrong value of list items: '{v[1:-1]}'. Cannot contain '[' or ']'.")
        elif "[" in v or "]" in v:
            raise errors.InvalidFilterStringError(f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                                  f"Wrong value: '{v}'. Cannot contain '[' or ']'.")

    params = dict({})
    for key, value in filter_params.items():
        __validate(value)
        if __is_int(value):
            params[key] = int(value)
        elif __is_float(value):
            params[key] = float(value)
        elif __is_list(value):
            params[key] = __get_list(value)
        else:
            params[key] = value

    return params


def get_endpoint_url_param_string(url: str) -> str:
    """
    Returns a part of url string with only the positional or optional parameters

    Example url: /delete_person_phone/2//1

    Should return: -1//-1
    """

    return "/".join(url.split("/")[2:])


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


def get_primary_key_violence_details(error_message: str) -> PrimaryKeyErrorDetails:
    """
    Returns parsed primary key violation details from error message.

    Example error message:
        E400_003: (psycopg2.errors.UniqueViolation) duplicate key value
        violates unique constraint "PK_PersonPhone_BusinessEntityID_PhoneNumber_PhoneNumberTypeID"
        DETAIL:  Key ("BusinessEntityID", "PhoneNumber", "PhoneNumberTypeID")=(20789, 001 002 003, 5) already exists.

    Should return:
        PrimaryKeyErrorDetails(key_column="\"BusinessEntityID\", \"PhoneNumber\", \"PhoneNumberTypeID\"", key_value="20789, 001 002 003, 5")
    """

    line_of_interest = error_message.split("\n")[1]
    column, value = tuple(re.findall(r"\((.*?)\)", line_of_interest))

    return PrimaryKeyErrorDetails(key_column=column, key_value=value)


def get_foreign_key_violence_details(error_message: str) -> ForeignKeyErrorDetails:
    """
    Returns parsed foreign key violation details from error message.

    Example error message:
        E400_004: (psycopg2.errors.ForeignKeyViolation) insert or update on table "PersonPhone"
        violates foreign key constraint "FK_PersonPhone_PhoneNumberType_PhoneNumberTypeID"\n
        DETAIL:  Key (PhoneNumberTypeID)=(10) is not present in table "PhoneNumberType".

    Should return:
        ForeignKeyErrorDetails(entity="PhoneNumberType", key_column="PhoneNumberTypeID", key_value="10")
    """

    line_of_interest = error_message.split("\n")[1]
    name = re.findall(r"\"(.*?)\"", line_of_interest)[0]
    column, value = tuple(re.findall(r"\((.*?)\)", line_of_interest))

    return ForeignKeyErrorDetails(entity=name, key_column=column, key_value=value)
