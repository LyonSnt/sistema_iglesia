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
            name="Familia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("nombre", models.CharField(max_length=150)),
                ("direccion", models.CharField(blank=True, max_length=255)),
                ("telefono", models.CharField(blank=True, max_length=30)),
                ("iglesia", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="familias_familia_items", to="iglesias.iglesia")),
                ("jefe_hogar", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="familias_jefatura", to="miembros.miembro")),
            ],
            options={"verbose_name": "familia", "verbose_name_plural": "familias", "ordering": ("nombre",)},
        ),
        migrations.CreateModel(
            name="MiembroFamilia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("relacion", models.CharField(choices=[("PADRE", "Padre"), ("MADRE", "Madre"), ("CONYUGE", "Conyuge"), ("HIJO", "Hijo"), ("REPRESENTANTE", "Representante"), ("OTRO", "Otro")], max_length=20)),
                ("familia", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="integrantes", to="familias.familia")),
                ("miembro", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="familias", to="miembros.miembro")),
            ],
            options={"verbose_name": "miembro de familia", "verbose_name_plural": "miembros de familias", "unique_together": {("familia", "miembro", "relacion")}},
        ),
    ]
