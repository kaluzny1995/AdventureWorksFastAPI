import re
from typing import Dict, Tuple


def get_username_from_message(error_message: str) -> str:
    # Example error message: "Current user 'testuser' has readonly restricted access."
    return re.findall("'([^']*)'", error_message)[0]


def get_unique_field_name_from_message(error_message: str) -> Tuple[str, str]:
    field, value = error_message.replace("Provided ", "").replace(" already exists.", "").split(" ")
    # Example error message: "Provided username 'testuser' already exists."
    return field, value[1:-1]


def get_foreign_key_violence_details(error_message: str) -> Dict[str, str]:
    line_of_interest = error_message.split("\n")[1]

    quotations = list(map(lambda p: p.start(), re.finditer("\"", line_of_interest)))
    foreign_entity = line_of_interest[quotations[0] + 1:quotations[1]]

    left_brackets = list(map(lambda p: p.start(), re.finditer("\\(", line_of_interest)))
    right_brackets = list(map(lambda p: p.start(), re.finditer("\\)", line_of_interest)))
    foreign_key_column = line_of_interest[left_brackets[0] + 1:right_brackets[0]]
    foreign_key_value = line_of_interest[left_brackets[1] + 1:right_brackets[1]]

    return dict(line=line_of_interest, entity=foreign_entity,
                key_column=foreign_key_column, key_value=foreign_key_value)
