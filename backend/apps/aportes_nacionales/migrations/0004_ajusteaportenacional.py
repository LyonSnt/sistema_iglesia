from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("aportes_nacionales", "0003_merge_0002_anulacion_aporte_0002_aportenacional_numero_recibo_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AjusteAporteNacional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("tipo", models.CharField(choices=[("CARGO", "Cargo"), ("ABONO", "Abono")], max_length=20)),
                ("monto", models.DecimalField(decimal_places=2, max_digits=12)),
                ("motivo", models.TextField()),
                ("observacion", models.TextField(blank=True)),
                (
                    "aporte",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ajustes",
                        to="aportes_nacionales.aportenacional",
                    ),
                ),
                (
                    "iglesia",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="%(app_label)s_%(class)s_items",
                        to="iglesias.iglesia",
                    ),
                ),
                (
                    "registrado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ajustes_aportes_nacionales_registrados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "ajuste de aporte nacional",
                "verbose_name_plural": "ajustes de aportes nacionales",
                "ordering": ("-creado_en",),
            },
        ),
    ]
