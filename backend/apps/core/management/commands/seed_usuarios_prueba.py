from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.iglesias.models import Iglesia
from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = "Crea usuarios de prueba para validar roles nacionales y filiales."

    DEFAULT_PASSWORD = "Cambiar12345!"

    USUARIOS = (
        {
            "username": "admin_nacional",
            "email": "admin_nacional@example.local",
            "first_name": "Admin",
            "last_name": "Nacional",
            "rol": Usuario.Rol.ADMIN_NACIONAL,
            "iglesia_codigo": "NACIONAL",
            "is_staff": True,
        },
        {
            "username": "auditor_nacional",
            "email": "auditor_nacional@example.local",
            "first_name": "Auditor",
            "last_name": "Nacional",
            "rol": Usuario.Rol.AUDITOR_NACIONAL,
            "iglesia_codigo": "NACIONAL",
            "is_staff": True,
        },
        {
            "username": "pastor_pruebas",
            "email": "pastor_pruebas@example.local",
            "first_name": "Pastor",
            "last_name": "Pruebas",
            "rol": Usuario.Rol.PASTOR_FILIAL,
            "iglesia_codigo": "PRUEBAS",
            "is_staff": True,
        },
        {
            "username": "secretario_pruebas",
            "email": "secretario_pruebas@example.local",
            "first_name": "Secretario",
            "last_name": "Pruebas",
            "rol": Usuario.Rol.SECRETARIO_FILIAL,
            "iglesia_codigo": "PRUEBAS",
            "is_staff": True,
        },
        {
            "username": "tesorero_pruebas",
            "email": "tesorero_pruebas@example.local",
            "first_name": "Tesorero",
            "last_name": "Pruebas",
            "rol": Usuario.Rol.TESORERO_FILIAL,
            "iglesia_codigo": "PRUEBAS",
            "is_staff": True,
        },
        {
            "username": "lectura_pruebas",
            "email": "lectura_pruebas@example.local",
            "first_name": "Solo",
            "last_name": "Lectura",
            "rol": Usuario.Rol.SOLO_LECTURA,
            "iglesia_codigo": "PRUEBAS",
            "is_staff": False,
        },
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=self.DEFAULT_PASSWORD,
            help="Contrasena inicial para usuarios nuevos. Solo usar en desarrollo.",
        )
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Reinicia la contrasena de usuarios existentes.",
        )

    def handle(self, *args, **options):
        password = options["password"]
        reset_passwords = options["reset_passwords"]

        if not password:
            raise CommandError("La contrasena no puede estar vacia.")

        iglesias = {
            iglesia.codigo: iglesia
            for iglesia in Iglesia.objects.filter(codigo__in={"NACIONAL", "PRUEBAS"})
        }
        faltantes = {"NACIONAL", "PRUEBAS"} - set(iglesias)
        if faltantes:
            raise CommandError(
                "Faltan iglesias base: "
                + ", ".join(sorted(faltantes))
                + ". Ejecuta primero python manage.py seed_inicial."
            )

        with transaction.atomic():
            for data in self.USUARIOS:
                self._crear_o_actualizar_usuario(data, iglesias, password, reset_passwords)

        if password == self.DEFAULT_PASSWORD:
            self.stdout.write(
                self.style.WARNING(
                    "Contrasena de desarrollo usada: Cambiar12345!. Cambiarla antes de usar datos reales."
                )
            )

        self.stdout.write(self.style.SUCCESS("Seed de usuarios de prueba completado."))

    def _crear_o_actualizar_usuario(self, data, iglesias, password, reset_passwords):
        rol = data["rol"]
        iglesia = iglesias[data["iglesia_codigo"]]
        group = Group.objects.get(name=rol)

        usuario, created = Usuario.objects.get_or_create(
            username=data["username"],
            defaults={
                "email": data["email"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "rol": rol,
                "iglesia": iglesia,
                "is_staff": data["is_staff"],
                "is_active": True,
                "debe_cambiar_password": True,
            },
        )

        if created or reset_passwords:
            usuario.set_password(password)

        usuario.email = data["email"]
        usuario.first_name = data["first_name"]
        usuario.last_name = data["last_name"]
        usuario.rol = rol
        usuario.iglesia = iglesia
        usuario.is_staff = data["is_staff"]
        usuario.is_active = True
        usuario.debe_cambiar_password = True
        usuario.save()
        usuario.groups.set([group])

        estado = "creado" if created else "actualizado"
        self.stdout.write(f"usuario: {usuario.username} ({estado}) rol={rol} iglesia={iglesia.codigo}")
