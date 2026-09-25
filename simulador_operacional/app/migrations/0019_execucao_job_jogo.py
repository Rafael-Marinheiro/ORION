# Espelha app/migrations_ci/0008: a trilha antiga precisa da mesma coluna.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0018_consolidado_eixos_multicriterio"),
    ]

    operations = [
        migrations.AddField(
            model_name="execucaojob",
            name="jogo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="execucoes_job",
                to="app.jogo",
            ),
        ),
    ]
