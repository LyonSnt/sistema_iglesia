import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("zonas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Iglesia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("codigo", models.CharField(max_length=30, unique=True)),
                ("nombre", models.CharField(max_length=180)),
                ("tipo", models.CharField(choices=[("NACIONAL", "Nacional"), ("FILIAL", "Filial")], default="FILIAL", max_length=20)),
                ("direccion", models.CharField(blank=True, max_length=255)),
                ("telefono", models.CharField(blank=True, max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("estado", models.CharField(choices=[("ACTIVA", "Activa"), ("INACTIVA", "Inactiva"), ("EN_REVISION", "En revision")], default="ACTIVA", max_length=20)),
                ("responsable_principal", models.CharField(blank=True, max_length=180)),
                ("iglesia_matriz", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="iglesias.iglesia")),
                ("zona", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="zonas.zona")),
            ],
            options={"verbose_name": "iglesia", "verbose_name_plural": "iglesias", "ordering": ("nombre",)},
        ),
    ]
