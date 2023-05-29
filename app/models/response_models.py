from typing import List, Dict

from app.models import Message


def get_response_models(main_model: object, codes: List[int]) -> Dict[int, Dict[str, object]]:
    response_mapping = dict({
        200: main_model,
        201: main_model,
        400: Message,
        401: Message,
        404: Message,
        500: Message
    })

    response_models = dict(list(map(lambda code: (code, {"model": response_mapping[code]}), codes)))

    return response_models
