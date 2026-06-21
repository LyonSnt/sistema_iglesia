from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Zona",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("nombre", models.CharField(max_length=100, unique=True)),
                ("codigo", models.CharField(max_length=20, unique=True)),
                ("descripcion", models.TextField(blank=True)),
            ],
            options={"verbose_name": "zona", "verbose_name_plural": "zonas", "ordering": ("nombre",)},
        ),
    ]
