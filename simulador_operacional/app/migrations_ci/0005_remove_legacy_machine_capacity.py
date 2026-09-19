# Generated manually to keep the consolidated migration graph aligned with C-20.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0004_consolidado_eixos_multicriterio"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="gameconfig",
            name="capacidade_maquina",
        ),
        migrations.RemoveField(
            model_name="grupo",
            name="capacidade_maquina",
        ),
    ]
