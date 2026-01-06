from functools import wraps
from typing import Awaitable, Callable

from fastapi import Response

_DecoratedFuncType = Callable[..., Awaitable[Response]]


def add_hx_trigger_header_on_success(header_value: str) -> Callable[[_DecoratedFuncType], _DecoratedFuncType]:
    """
    Adds the 'HX-Trigger' header to the response if the response status code is a success code.
    See https://htmx.org/attributes/hx-trigger/#triggering-via-the-hx-trigger-header and
    https://htmx.org/headers/hx-trigger/ for details on this header.
    This is a workaround for https://github.com/maces/fastapi-htmx/issues/46
    :param header_value: the value to set for the 'HX-Trigger' header
    """

    def decorator(func: _DecoratedFuncType) -> _DecoratedFuncType:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            if isinstance(response, Response):
                is_success_status_code = 200 <= response.status_code < 300
                if is_success_status_code:
                    response.headers.append("HX-Trigger", header_value)

            return response

        return wrapper

    return decorator
