import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("iglesias", "0001_initial"),
        ("miembros", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Ministerio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("nombre", models.CharField(max_length=150)),
                ("tipo", models.CharField(choices=[("DEPARTAMENTO", "Departamento"), ("MINISTERIO", "Ministerio"), ("EQUIPO", "Equipo"), ("GRUPO", "Grupo")], default="MINISTERIO", max_length=20)),
                ("descripcion", models.TextField(blank=True)),
                ("iglesia", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ministerios_ministerio_items", to="iglesias.iglesia")),
                ("responsable", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="miembros.miembro")),
            ],
            options={"verbose_name": "ministerio", "verbose_name_plural": "ministerios", "ordering": ("nombre",), "unique_together": {("iglesia", "nombre")}},
        ),
        migrations.CreateModel(
            name="ParticipacionMinisterio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("cargo", models.CharField(blank=True, max_length=120)),
                ("fecha_inicio", models.DateField()),
                ("fecha_fin", models.DateField(blank=True, null=True)),
                ("estado", models.CharField(choices=[("ACTIVO", "Activo"), ("INACTIVO", "Inactivo"), ("FINALIZADO", "Finalizado")], default="ACTIVO", max_length=20)),
                ("motivo_salida", models.TextField(blank=True)),
                ("miembro", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ministerios", to="miembros.miembro")),
                ("ministerio", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="participaciones", to="ministerios.ministerio")),
            ],
            options={"verbose_name": "participacion ministerial", "verbose_name_plural": "participaciones ministeriales", "ordering": ("-fecha_inicio",)},
        ),
    ]
