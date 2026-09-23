from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0005_remove_legacy_machine_capacity"),
    ]

    operations = [
        migrations.AddField(
            model_name="consolidadorodadagrupo",
            name="valor_estoques_operacional",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
    ]
