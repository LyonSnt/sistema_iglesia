from django.urls import path

from . import views

app_name = "traslados"

urlpatterns = [
    path("", views.TrasladoListView.as_view(), name="list"),
    path("crear/", views.TrasladoCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TrasladoDetailView.as_view(), name="detail"),
    path("<int:pk>/aceptar/", views.AceptarTrasladoView.as_view(), name="aceptar"),
    path("<int:pk>/rechazar/", views.RechazarTrasladoView.as_view(), name="rechazar"),
    path("<int:pk>/anular/", views.AnularTrasladoView.as_view(), name="anular"),
    path("<int:pk>/recepcion/", views.ConfirmarRecepcionTrasladoView.as_view(), name="recepcion"),
    path("<int:pk>/integracion/familia/", views.RevisarIntegracionFamiliarView.as_view(), name="integracion-familia"),
    path("<int:pk>/integracion/escuela/", views.RevisarIntegracionEscuelaView.as_view(), name="integracion-escuela"),
    path("<int:pk>/integracion/familia/vincular/", views.VincularFamiliaDestinoView.as_view(), name="vincular-familia"),
    path("<int:pk>/integracion/escuela/matricular/", views.MatricularEscuelaDestinoView.as_view(), name="matricular-escuela"),
    path("<int:pk>/tareas/crear/", views.CrearTareaPastoralTrasladoView.as_view(), name="tarea-create"),
    path(
        "<int:pk>/tareas/<int:tarea_pk>/completar/",
        views.CompletarTareaPastoralTrasladoView.as_view(),
        name="tarea-completar",
    ),
    path("<int:pk>/documentos/subir/", views.AdjuntarDocumentoTrasladoView.as_view(), name="document-create"),
    path("<int:pk>/documentos/<int:documento_pk>/", views.DescargarDocumentoTrasladoView.as_view(), name="document-download"),
    path("<int:pk>/documentos/<int:documento_pk>/anular/", views.AnularDocumentoTrasladoView.as_view(), name="document-deactivate"),
]
