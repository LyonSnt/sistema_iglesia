from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("aportes_nacionales", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="aportenacional",
            name="anulado_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="aportenacional",
            name="anulado_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aportes_nacionales_anulados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="aportenacional",
            name="motivo_anulacion",
            field=models.TextField(blank=True),
        ),
    ]
