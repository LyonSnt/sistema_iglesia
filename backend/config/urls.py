from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.api.urls")),
    path("cargos/", include("apps.cargos.urls")),
    path("certificados/", include("apps.certificados.urls")),
    path("escuela-dominical/", include("apps.escuela_dominical.urls")),
    path("familias/", include("apps.familias.urls")),
    path("iglesias/", include("apps.iglesias.urls")),
    path("miembros/", include("apps.miembros.urls")),
    path("ministerios/", include("apps.ministerios.urls")),
    path("usuarios/", include("apps.usuarios.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
