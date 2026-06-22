from collections import Counter

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    AsistenciaEscuelaDominical,
    MatriculaEscuelaDominical,
    NivelEscuelaDominical,
    ProcesoPromocionEscuelaDominical,
    ResultadoPromocionEscuelaDominical,
)


def calcular_edad(fecha_nacimiento, fecha_corte):
    return fecha_corte.year - fecha_nacimiento.year - (
        (fecha_corte.month, fecha_corte.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )


def generar_resultados(proceso):
    niveles = list(
        NivelEscuelaDominical.objects.filter(iglesia=proceso.iglesia, activo=True).order_by(
            "orden", "nombre"
        )
    )
    siguiente_por_id = {nivel.pk: niveles[indice + 1] for indice, nivel in enumerate(niveles[:-1])}
    ultimo_id = niveles[-1].pk if niveles else None
    matriculas = MatriculaEscuelaDominical.objects.filter(
        clase__iglesia=proceso.iglesia,
        clase__periodo=proceso.periodo_origen,
        estado=MatriculaEscuelaDominical.Estado.ACTIVA,
        activo=True,
        alumno__fecha_nacimiento__isnull=False,
    ).select_related("alumno", "clase__nivel")

    creados = []
    for matricula in matriculas:
        edad = calcular_edad(matricula.alumno.fecha_nacimiento, proceso.fecha_corte)
        nivel_actual = matricula.clase.nivel
        siguiente = siguiente_por_id.get(nivel_actual.pk)
        destino = None
        nivel_destino = None
        if siguiente and siguiente.edad_minima is not None and edad >= siguiente.edad_minima:
            destino = ResultadoPromocionEscuelaDominical.Destino.NIVEL_SIGUIENTE
            nivel_destino = siguiente
        elif (
            nivel_actual.pk == ultimo_id
            and nivel_actual.edad_maxima is not None
            and edad >= nivel_actual.edad_maxima
        ):
            destino = ResultadoPromocionEscuelaDominical.Destino.JOVENES
        if not destino:
            continue

        conteos = matricula.asistencias.filter(
            sesion__cerrada=True, sesion__fecha__lte=proceso.fecha_corte
        ).aggregate(
            sesiones=Count("id"),
            presentes=Count("id", filter=Q(estado=AsistenciaEscuelaDominical.Estado.PRESENTE)),
            ausentes=Count("id", filter=Q(estado=AsistenciaEscuelaDominical.Estado.AUSENTE)),
            justificados=Count("id", filter=Q(estado=AsistenciaEscuelaDominical.Estado.JUSTIFICADO)),
        )
        resultado, _ = ResultadoPromocionEscuelaDominical.objects.update_or_create(
            proceso=proceso,
            matricula_origen=matricula,
            defaults={
                "edad_al_corte": edad,
                "destino": destino,
                "nivel_destino": nivel_destino,
                "sesiones_consideradas": conteos["sesiones"],
                "presentes": conteos["presentes"],
                "ausentes": conteos["ausentes"],
                "justificados": conteos["justificados"],
            },
        )
        creados.append(resultado)
    return creados


@transaction.atomic
def confirmar_promocion(proceso, usuario):
    proceso = ProcesoPromocionEscuelaDominical.objects.select_for_update().get(pk=proceso.pk)
    if proceso.estado == proceso.Estado.CONFIRMADO:
        return proceso
    resultados = list(proceso.resultados.select_related("matricula_origen", "clase_destino"))
    if not resultados:
        raise ValidationError("El proceso no tiene alumnos candidatos.")
    incompletos = [r for r in resultados if r.destino == r.Destino.NIVEL_SIGUIENTE and not r.clase_destino_id]
    if incompletos:
        raise ValidationError("Todos los alumnos promovidos deben tener una clase destino.")

    destinos = Counter(
        resultado.clase_destino_id
        for resultado in resultados
        if resultado.destino == resultado.Destino.NIVEL_SIGUIENTE
    )
    for resultado in resultados:
        resultado.full_clean()
    for clase_id, cantidad in destinos.items():
        clase = next(r.clase_destino for r in resultados if r.clase_destino_id == clase_id)
        if clase.cupo is not None:
            ocupados = clase.matriculas.filter(
                activo=True, estado=MatriculaEscuelaDominical.Estado.ACTIVA
            ).count()
            if ocupados + cantidad > clase.cupo:
                raise ValidationError(f"La clase destino {clase.nombre} no tiene cupo suficiente.")

    for resultado in resultados:
        origen = resultado.matricula_origen
        if origen.estado != origen.Estado.ACTIVA:
            raise ValidationError(f"La matricula de {origen.alumno} ya no esta activa.")
        if resultado.destino == resultado.Destino.NIVEL_SIGUIENTE:
            destino, _ = MatriculaEscuelaDominical.objects.get_or_create(
                clase=resultado.clase_destino,
                alumno=origen.alumno,
                defaults={"fecha_inscripcion": proceso.fecha_corte},
            )
            resultado.matricula_destino = destino
            resultado.save(update_fields=["matricula_destino", "actualizado_en"])
        origen.estado = origen.Estado.PROMOVIDA
        origen.fecha_salida = proceso.fecha_corte
        origen.save(update_fields=["estado", "fecha_salida", "actualizado_en"])

    proceso.estado = proceso.Estado.CONFIRMADO
    proceso.confirmado_por = usuario
    proceso.confirmado_en = timezone.now()
    proceso.save(update_fields=["estado", "confirmado_por", "confirmado_en", "actualizado_en"])
    return proceso
