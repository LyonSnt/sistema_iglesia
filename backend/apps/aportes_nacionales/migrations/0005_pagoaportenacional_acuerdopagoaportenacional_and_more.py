from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("aportes_nacionales", "0004_ajusteaportenacional"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="aportenacional",
            name="fecha_vencimiento",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="PagoAporteNacional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("monto", models.DecimalField(decimal_places=2, max_digits=12)),
                ("fecha_pago", models.DateField()),
                ("referencia_pago", models.CharField(max_length=120)),
                ("observacion", models.TextField(blank=True)),
                (
                    "aporte",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pagos",
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
                        related_name="pagos_aportes_nacionales_detallados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "pago de aporte nacional",
                "verbose_name_plural": "pagos de aportes nacionales",
                "ordering": ("fecha_pago", "creado_en"),
            },
        ),
        migrations.CreateModel(
            name="AcuerdoPagoAporteNacional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("fecha_compromiso", models.DateField()),
                ("monto_comprometido", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "estado",
                    models.CharField(
                        choices=[("VIGENTE", "Vigente"), ("CUMPLIDO", "Cumplido"), ("ANULADO", "Anulado")],
                        default="VIGENTE",
                        max_length=20,
                    ),
                ),
                ("observacion", models.TextField(blank=True)),
                (
                    "aporte",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="acuerdos",
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
                        related_name="acuerdos_aportes_nacionales_registrados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "acuerdo de pago de aporte nacional",
                "verbose_name_plural": "acuerdos de pago de aportes nacionales",
                "ordering": ("fecha_compromiso",),
            },
        ),
    ]
