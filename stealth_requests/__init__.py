from functools import partial
from .session import StealthSession, AsyncStealthSession
from curl_cffi.requests import *


def request(method: str, url: str, *args, **kwargs) -> Response:
    with StealthSession() as s:
        return s.request(method, url, *args, **kwargs)

head = partial(request, "HEAD")
get = partial(request, "GET")
post = partial(request, "POST")
put = partial(request, "PUT")
patch = partial(request, "PATCH")
delete = partial(request, "DELETE")
options = partial(request, "OPTIONS")