import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("iglesias", "0001_initial"),
        ("miembros", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cargo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("nombre", models.CharField(max_length=120, unique=True)),
                ("descripcion", models.TextField(blank=True)),
                ("es_nacional", models.BooleanField(default=False)),
            ],
            options={"verbose_name": "cargo", "verbose_name_plural": "cargos", "ordering": ("nombre",)},
        ),
        migrations.CreateModel(
            name="AsignacionCargo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("fecha_inicio", models.DateField()),
                ("fecha_fin", models.DateField(blank=True, null=True)),
                ("estado", models.CharField(choices=[("VIGENTE", "Vigente"), ("FINALIZADO", "Finalizado"), ("ANULADO", "Anulado")], default="VIGENTE", max_length=20)),
                ("documento", models.FileField(blank=True, upload_to="cargos/documentos/")),
                ("observacion", models.TextField(blank=True)),
                ("cargo", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="asignaciones", to="cargos.cargo")),
                ("iglesia", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cargos_asignacioncargo_items", to="iglesias.iglesia")),
                ("miembro", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cargos", to="miembros.miembro")),
                ("usuario", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cargos", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "asignacion de cargo", "verbose_name_plural": "asignaciones de cargos", "ordering": ("-fecha_inicio",)},
        ),
    ]
