from datetime import date

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.cargos.models import Cargo
from apps.iglesias.models import Iglesia
from apps.parametros.models import ParametroGeneral, Periodo
from apps.usuarios.models import Usuario
from apps.zonas.models import Zona


class Command(BaseCommand):
    help = "Carga datos base iniciales de Ecclesia."

    ZONAS = (
        ("COSTA", "Costa"),
        ("SIERRA", "Sierra"),
        ("ORIENTE", "Oriente"),
        ("INSULAR", "Insular"),
    )

    CARGOS = (
        ("Presidente", True),
        ("Vicepresidente", True),
        ("Secretario", True),
        ("Tesorero", True),
        ("Auditor", True),
        ("Vocal", True),
        ("Pastor", False),
        ("Encargado", False),
        ("Lider de ministerio", False),
        ("Maestro", False),
        ("Director de Escuela Dominical", False),
    )

    PARAMETROS = (
        ("APORTE_NACIONAL_PORCENTAJE", "Porcentaje de aporte nacional", "10", ParametroGeneral.TipoDato.DECIMAL),
        ("ESCUELA_DOMINICAL_DIA_CORTE", "Dia de corte de Escuela Dominical", "15", ParametroGeneral.TipoDato.ENTERO),
        ("CERTIFICADOS_PREFIJO", "Prefijo de certificados", "EC", ParametroGeneral.TipoDato.TEXTO),
        ("CERTIFICADOS_SECUENCIAL_INICIAL", "Secuencial inicial de certificados", "1", ParametroGeneral.TipoDato.ENTERO),
    )

    PERMISOS_POR_ROL = {
        Usuario.Rol.SUPERADMIN: "__all__",
        Usuario.Rol.ADMIN_NACIONAL: (
            ("iglesias", "iglesia", ("view", "add", "change")),
            ("zonas", "zona", ("view",)),
            ("auditoria", "registroauditoria", ("view",)),
        ),
        Usuario.Rol.PASTOR_FILIAL: (),
        Usuario.Rol.ENCARGADO_FILIAL: (),
        Usuario.Rol.SECRETARIO_FILIAL: (),
        Usuario.Rol.TESORERO_FILIAL: (),
        Usuario.Rol.SOLO_LECTURA: (),
    }

    GRUPOS_OBSOLETOS = (
        "PRESIDENTE_NACIONAL",
        "VICEPRESIDENTE_NACIONAL",
        "SECRETARIO_NACIONAL",
        "TESORERO_NACIONAL",
        "AUDITOR_NACIONAL",
        "LIDER_MINISTERIO",
        "MAESTRO",
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            self._crear_zonas()
            iglesia_nacional = self._crear_iglesia_nacional()
            self._crear_iglesia_pruebas(iglesia_nacional)
            self._crear_cargos()
            self._crear_parametros()
            self._crear_periodo_actual()
            self._crear_grupos_y_permisos()

        self.stdout.write(self.style.SUCCESS("Seed inicial completado."))

    def _crear_zonas(self):
        for codigo, nombre in self.ZONAS:
            zona, created = Zona.objects.get_or_create(
                codigo=codigo,
                defaults={"nombre": nombre, "descripcion": f"Zona {nombre}"},
            )
            self._log(created, "zona", zona.nombre)

    def _crear_iglesia_nacional(self):
        iglesia, created = Iglesia.objects.get_or_create(
            codigo="NACIONAL",
            defaults={
                "nombre": "Iglesia Nacional",
                "tipo": Iglesia.Tipo.NACIONAL,
                "estado": Iglesia.Estado.ACTIVA,
                "responsable_principal": "Directiva nacional",
            },
        )
        self._log(created, "iglesia", iglesia.nombre)
        return iglesia

    def _crear_iglesia_pruebas(self, iglesia_nacional):
        zona, _ = Zona.objects.get_or_create(codigo="SIERRA", defaults={"nombre": "Sierra"})
        iglesia, created = Iglesia.objects.get_or_create(
            codigo="PRUEBAS",
            defaults={
                "nombre": "Iglesia Filial Pruebas",
                "tipo": Iglesia.Tipo.FILIAL,
                "zona": zona,
                "iglesia_matriz": iglesia_nacional,
                "estado": Iglesia.Estado.ACTIVA,
                "responsable_principal": "Responsable de pruebas",
            },
        )
        self._log(created, "iglesia", iglesia.nombre)

    def _crear_cargos(self):
        for nombre, es_nacional in self.CARGOS:
            cargo, created = Cargo.objects.get_or_create(
                nombre=nombre,
                defaults={"es_nacional": es_nacional},
            )
            self._log(created, "cargo", cargo.nombre)

    def _crear_parametros(self):
        for clave, nombre, valor, tipo_dato in self.PARAMETROS:
            parametro, created = ParametroGeneral.objects.get_or_create(
                clave=clave,
                defaults={
                    "nombre": nombre,
                    "valor": valor,
                    "tipo_dato": tipo_dato,
                },
            )
            self._log(created, "parametro", parametro.clave)

    def _crear_periodo_actual(self):
        year = date.today().year
        periodo, created = Periodo.objects.get_or_create(
            nombre=str(year),
            defaults={
                "fecha_inicio": date(year, 1, 1),
                "fecha_fin": date(year, 12, 31),
            },
        )
        self._log(created, "periodo", periodo.nombre)

    def _crear_grupos_y_permisos(self):
        Group.objects.filter(name__in=self.GRUPOS_OBSOLETOS).delete()
        permisos = list(Permission.objects.select_related("content_type"))
        for rol, acciones in self.PERMISOS_POR_ROL.items():
            group, created = Group.objects.get_or_create(name=rol)
            if acciones == "__all__":
                group.permissions.set(permisos)
            else:
                permisos_rol = []
                for app_label, modelo, acciones_modelo in acciones:
                    permisos_rol.extend(
                        permiso
                        for permiso in permisos
                        if permiso.content_type.app_label == app_label
                        and permiso.content_type.model == modelo
                        and permiso.codename.split("_", 1)[0] in acciones_modelo
                    )
                group.permissions.set(permisos_rol)
            self._log(created, "grupo", group.name)

    def _log(self, created, tipo, nombre):
        estado = "creado" if created else "existente"
        self.stdout.write(f"{tipo}: {nombre} ({estado})")
