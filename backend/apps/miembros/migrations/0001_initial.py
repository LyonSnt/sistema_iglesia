import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("iglesias", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Miembro",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("nombres", models.CharField(max_length=120)),
                ("apellidos", models.CharField(max_length=120)),
                ("cedula", models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ("fecha_nacimiento", models.DateField(blank=True, null=True)),
                ("sexo", models.CharField(choices=[("M", "Masculino"), ("F", "Femenino")], max_length=1)),
                ("estado_civil", models.CharField(blank=True, choices=[("SOLTERO", "Soltero"), ("CASADO", "Casado"), ("VIUDO", "Viudo"), ("DIVORCIADO", "Divorciado"), ("UNION_LIBRE", "Union libre")], max_length=20)),
                ("telefono", models.CharField(blank=True, max_length=30)),
                ("direccion", models.CharField(blank=True, max_length=255)),
                ("fotografia", models.ImageField(blank=True, upload_to="miembros/fotografias/")),
                ("fecha_conversion", models.DateField(blank=True, null=True)),
                ("fecha_bautismo", models.DateField(blank=True, null=True)),
                ("fecha_membresia", models.DateField(blank=True, null=True)),
                ("estado", models.CharField(choices=[("ACTIVO", "Activo"), ("INACTIVO", "Inactivo"), ("TRASLADADO", "Trasladado"), ("FALLECIDO", "Fallecido")], default="ACTIVO", max_length=20)),
                ("fecha_fallecimiento", models.DateField(blank=True, null=True)),
                ("observacion", models.TextField(blank=True)),
                ("iglesia", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="miembros_miembro_items", to="iglesias.iglesia")),
            ],
            options={"verbose_name": "miembro", "verbose_name_plural": "miembros", "ordering": ("apellidos", "nombres")},
        ),
    ]
