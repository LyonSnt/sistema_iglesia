from contextvars import ContextVar


_request_actual = ContextVar("auditoria_request_actual", default=None)


def obtener_request_actual():
    return _request_actual.get()


class AuditoriaRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _request_actual.set(request)
        try:
            return self.get_response(request)
        finally:
            _request_actual.reset(token)
