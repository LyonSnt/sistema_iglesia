from rest_framework import serializers

from apps.cargos.models import AsignacionCargo, Cargo
from apps.familias.models import Familia, Matrimonio, MiembroFamilia
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.ministerios.models import Ministerio, ParticipacionMinisterio


class IglesiaResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Iglesia
        fields = ("id", "codigo", "nombre", "tipo")


class MiembroResumenSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = Miembro
        fields = ("id", "nombres", "apellidos", "nombre_completo", "cedula", "estado", "activo")


class MiembroSerializer(serializers.ModelSerializer):
    iglesia = IglesiaResumenSerializer(read_only=True)
    sexo_display = serializers.CharField(source="get_sexo_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    estado_civil_display = serializers.CharField(source="get_estado_civil_display", read_only=True)

    class Meta:
        model = Miembro
        fields = (
            "id",
            "iglesia",
            "nombres",
            "apellidos",
            "cedula",
            "fecha_nacimiento",
            "sexo",
            "sexo_display",
            "estado_civil",
            "estado_civil_display",
            "telefono",
            "direccion",
            "fecha_conversion",
            "fecha_bautismo",
            "fecha_membresia",
            "estado",
            "estado_display",
            "fecha_fallecimiento",
            "observacion",
            "activo",
            "creado_en",
            "actualizado_en",
        )


class MiembroFamiliaSerializer(serializers.ModelSerializer):
    miembro = MiembroResumenSerializer(read_only=True)
    relacion_display = serializers.CharField(source="get_relacion_display", read_only=True)

    class Meta:
        model = MiembroFamilia
        fields = ("id", "miembro", "relacion", "relacion_display", "activo")


class FamiliaSerializer(serializers.ModelSerializer):
    iglesia = IglesiaResumenSerializer(read_only=True)
    jefe_hogar = MiembroResumenSerializer(read_only=True)
    integrantes = MiembroFamiliaSerializer(many=True, read_only=True)

    class Meta:
        model = Familia
        fields = (
            "id",
            "iglesia",
            "nombre",
            "jefe_hogar",
            "direccion",
            "telefono",
            "activo",
            "integrantes",
            "creado_en",
            "actualizado_en",
        )


class MatrimonioSerializer(serializers.ModelSerializer):
    iglesia = IglesiaResumenSerializer(read_only=True)
    conyuge_1 = MiembroResumenSerializer(read_only=True)
    conyuge_2 = MiembroResumenSerializer(read_only=True)
    familia = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Matrimonio
        fields = (
            "id",
            "iglesia",
            "conyuge_1",
            "conyuge_2",
            "fecha_matrimonio",
            "familia",
            "observacion",
            "activo",
            "creado_en",
            "actualizado_en",
        )


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ("id", "nombre", "descripcion", "es_nacional", "activo")


class UsuarioResumenSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    rol = serializers.CharField(read_only=True)


class AsignacionCargoSerializer(serializers.ModelSerializer):
    iglesia = IglesiaResumenSerializer(read_only=True)
    cargo = CargoSerializer(read_only=True)
    miembro = MiembroResumenSerializer(read_only=True)
    usuario = UsuarioResumenSerializer(read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    asignado_a = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = AsignacionCargo
        fields = (
            "id",
            "iglesia",
            "cargo",
            "miembro",
            "usuario",
            "asignado_a",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "estado_display",
            "observacion",
            "activo",
            "creado_en",
            "actualizado_en",
        )


class ParticipacionMinisterioSerializer(serializers.ModelSerializer):
    ministerio_nombre = serializers.CharField(source="ministerio.nombre", read_only=True)
    miembro = MiembroResumenSerializer(read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = ParticipacionMinisterio
        fields = (
            "id",
            "ministerio",
            "ministerio_nombre",
            "miembro",
            "cargo",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "estado_display",
            "motivo_salida",
            "activo",
            "creado_en",
            "actualizado_en",
        )


class MinisterioSerializer(serializers.ModelSerializer):
    iglesia = IglesiaResumenSerializer(read_only=True)
    responsable = MiembroResumenSerializer(read_only=True)
    lider = UsuarioResumenSerializer(read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    participaciones = ParticipacionMinisterioSerializer(many=True, read_only=True)

    class Meta:
        model = Ministerio
        fields = (
            "id",
            "iglesia",
            "nombre",
            "tipo",
            "tipo_display",
            "descripcion",
            "responsable",
            "lider",
            "activo",
            "participaciones",
            "creado_en",
            "actualizado_en",
        )
