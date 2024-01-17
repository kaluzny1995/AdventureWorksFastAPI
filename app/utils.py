import re
from typing import Dict, Tuple

from app import errors
from app.models import ForeignKeyErrorDetails


def get_filter_params(filter_string: str) -> Dict[str, str]:
    # Example query string: "pt:GC,fnph:Joh,lnph:D"
    try:
        filter_params = dict(map(lambda p: p.split(":"), filter_string.split(",")))
    except ValueError as e:
        raise errors.InvalidFilterStringError(f"Invalid filter string: {filter_string}.")

    return filter_params


def get_username_from_message(error_message: str) -> str:
    # Example error message: "Current user 'testuser' has readonly restricted access."
    return re.findall("'([^']*)'", error_message)[0]


def get_unique_field_details_from_message(error_message: str) -> Tuple[str, str]:
    # Example error message: "Provided username 'testuser' already exists."
    field, value = error_message.replace("Provided ", "").replace(" already exists.", "").split(" ")
    return field, value[1:-1]


def get_validation_error_details_from_message(error_message: str,
                                              is_required_skipped: bool = False) -> Tuple[str, Dict[str, str]]:
    # Example:
    # 1 validation error for Request
    # body -> first_name
    #   field required (type=value_error.missing)
    # email_promotion
    #   ensure this value is less than or equal to 2 (type=value_error.number.not_le; limit_value=2)

    lines = error_message.split("\n")
    error_details = list(map(lambda i: (lines[1:][i*2], lines[1:][i*2+1]), range(len(lines[1:])//2)))
    error_dict = dict(map(lambda ed: (ed[0].strip().replace("body -> ", ""),
                                      re.sub(r" [(\[].*?[)\]]", "", ed[1].strip())),
                          error_details))
    if is_required_skipped:
        error_dict = dict(filter(lambda ed: "field required" not in ed[1], error_dict.items()))

    return lines[0], error_dict


def get_foreign_key_violence_details(error_message: str) -> ForeignKeyErrorDetails:
    # Example error message: "DETAIL:  Key (PhoneNumberTypeID)=(10) is not present in table "PhoneNumberType"."
    line_of_interest = error_message.split("\n")[1]

    quotations = list(map(lambda p: p.start(), re.finditer("\"", line_of_interest)))
    foreign_entity = line_of_interest[quotations[0] + 1:quotations[1]]

    left_brackets = list(map(lambda p: p.start(), re.finditer("\\(", line_of_interest)))
    right_brackets = list(map(lambda p: p.start(), re.finditer("\\)", line_of_interest)))
    foreign_key_column = line_of_interest[left_brackets[0] + 1:right_brackets[0]]
    foreign_key_value = line_of_interest[left_brackets[1] + 1:right_brackets[1]]

    return ForeignKeyErrorDetails(line=line_of_interest, entity=foreign_entity,
                                  key_column=foreign_key_column, key_value=foreign_key_value)
