import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("iglesias", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistroAuditoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("accion", models.CharField(max_length=80)),
                ("modulo", models.CharField(max_length=80)),
                ("registro_afectado", models.CharField(blank=True, max_length=120)),
                ("valor_anterior", models.JSONField(blank=True, null=True)),
                ("valor_nuevo", models.JSONField(blank=True, null=True)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("motivo", models.TextField(blank=True)),
                ("iglesia", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="iglesias.iglesia")),
                ("usuario", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "registro de auditoria", "verbose_name_plural": "registros de auditoria", "ordering": ("-creado_en",)},
        ),
    ]
