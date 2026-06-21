from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ParametroGeneral",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("clave", models.CharField(max_length=100, unique=True)),
                ("nombre", models.CharField(max_length=150)),
                ("valor", models.CharField(max_length=255)),
                ("tipo_dato", models.CharField(choices=[("TEXTO", "Texto"), ("ENTERO", "Entero"), ("DECIMAL", "Decimal"), ("BOOLEANO", "Booleano"), ("FECHA", "Fecha")], default="TEXTO", max_length=20)),
                ("descripcion", models.TextField(blank=True)),
            ],
            options={"verbose_name": "parametro general", "verbose_name_plural": "parametros generales", "ordering": ("clave",)},
        ),
        migrations.CreateModel(
            name="Periodo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("nombre", models.CharField(max_length=80)),
                ("fecha_inicio", models.DateField()),
                ("fecha_fin", models.DateField()),
                ("cerrado", models.BooleanField(default=False)),
            ],
            options={"verbose_name": "periodo", "verbose_name_plural": "periodos", "ordering": ("-fecha_inicio",)},
        ),
    ]
