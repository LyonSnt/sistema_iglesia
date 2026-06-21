from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.iglesias.models import Iglesia
from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = "Normaliza un superusuario tecnico con rol y grupo SUPERADMIN."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="admin",
            help="Username del superusuario tecnico a normalizar.",
        )

    def handle(self, *args, **options):
        username = options["username"]

        with transaction.atomic():
            try:
                usuario = Usuario.objects.get(username=username)
            except Usuario.DoesNotExist as exc:
                raise CommandError(f"No existe el usuario tecnico '{username}'.") from exc

            if not usuario.is_superuser:
                raise CommandError(f"El usuario '{username}' no es superusuario.")

            try:
                group = Group.objects.get(name=Usuario.Rol.SUPERADMIN)
            except Group.DoesNotExist as exc:
                raise CommandError(
                    "No existe el grupo SUPERADMIN. Ejecuta primero python manage.py seed_inicial."
                ) from exc

            iglesia_nacional = Iglesia.objects.filter(codigo="NACIONAL").first()
            if iglesia_nacional is None:
                raise CommandError(
                    "No existe la iglesia NACIONAL. Ejecuta primero python manage.py seed_inicial."
                )

            usuario.rol = Usuario.Rol.SUPERADMIN
            usuario.iglesia = iglesia_nacional
            usuario.is_staff = True
            usuario.is_active = True
            usuario.debe_cambiar_password = False
            usuario.save(
                update_fields=[
                    "rol",
                    "iglesia",
                    "is_staff",
                    "is_active",
                    "debe_cambiar_password",
                ]
            )
            usuario.groups.set([group])

        self.stdout.write(
            self.style.SUCCESS(
                f"Superusuario '{usuario.username}' normalizado como SUPERADMIN en iglesia NACIONAL."
            )
        )
