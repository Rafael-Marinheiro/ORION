from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0006_consolidado_estoque_operacional"),
    ]

    operations = [
        migrations.AddField(
            model_name="distribuicao",
            name="expedida",
            field=models.BooleanField(default=False),
        ),
    ]
