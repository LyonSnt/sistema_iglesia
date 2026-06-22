from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia
from apps.usuarios.models import Usuario

from .contexto import obtener_request_actual
from .models import RegistroAuditoria


def _valor_json(valor):
    if valor is None or isinstance(valor, (bool, int, float, str)):
        return valor
    if isinstance(valor, (date, datetime, time, Decimal, UUID)):
        return str(valor)
    return str(valor)


def _serializar_instancia(instance):
    return {
        field.name: _valor_json(field.value_from_object(instance))
        for field in instance._meta.concrete_fields
        if field.name not in {"password", "last_login", "creado_en", "actualizado_en"}
    }


def _resolver_iglesia(instance):
    if isinstance(instance, Iglesia):
        return instance

    iglesia = getattr(instance, "iglesia", None)
    if iglesia is not None:
        return iglesia

    for relacion in ("familia", "ministerio", "clase"):
        objeto = getattr(instance, relacion, None)
        if objeto is not None:
            return getattr(objeto, "iglesia", None)
    return None


def _request_auditable(instance):
    request = obtener_request_actual()
    user = getattr(request, "user", None) if request is not None else None
    iglesia = _resolver_iglesia(instance)
    if request is None or not getattr(user, "is_authenticated", False) or iglesia is None:
        return None
    if usuario_es_nacional(user) and iglesia.tipo == Iglesia.Tipo.FILIAL:
        return request, user, iglesia, "Intervencion de usuario nacional sobre datos de una filial."
    if isinstance(instance, Usuario) and user.iglesia_id == iglesia.id:
        return request, user, iglesia, "Administracion delegada de una cuenta local."
    return None


@receiver(pre_save)
def capturar_valor_anterior(sender, instance, raw=False, **kwargs):
    if raw or sender is RegistroAuditoria or not instance.pk:
        return
    if _request_auditable(instance) is None:
        return
    try:
        anterior = sender._default_manager.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    instance._auditoria_valor_anterior = _serializar_instancia(anterior)
    if isinstance(instance, Usuario) and anterior.password != instance.password:
        instance._auditoria_password_modificada = True


@receiver(post_save)
def registrar_cambio_nacional(sender, instance, created, raw=False, **kwargs):
    if raw or sender is RegistroAuditoria:
        return
    contexto = _request_auditable(instance)
    if contexto is None:
        return

    request, user, iglesia, motivo = contexto
    valor_anterior = getattr(instance, "_auditoria_valor_anterior", None)
    valor_nuevo = _serializar_instancia(instance)
    if getattr(instance, "_auditoria_password_modificada", False):
        valor_nuevo["password_modificada"] = True
    if not created and valor_anterior == valor_nuevo:
        return

    RegistroAuditoria.objects.create(
        usuario=user,
        accion="CREAR" if created else "MODIFICAR",
        modulo=instance._meta.app_label,
        registro_afectado=f"{instance._meta.label}:{instance.pk}"[:120],
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
        ip=request.META.get("REMOTE_ADDR") or None,
        iglesia=iglesia,
        motivo=motivo,
    )
