from django.shortcuts import redirect
from django.urls import reverse


class CambioPasswordObligatorioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False) and getattr(user, "debe_cambiar_password", False):
            rutas_permitidas = {
                reverse("core:password-change"),
                reverse("core:logout"),
            }
            if request.path not in rutas_permitidas and not request.path.startswith("/static/"):
                return redirect("core:password-change")
        return self.get_response(request)
