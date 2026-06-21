from celery import shared_task


@shared_task
def generar_notificaciones_programadas():
    return "notificaciones pendientes por implementar"
