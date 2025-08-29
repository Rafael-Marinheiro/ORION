from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0008_grupo_materia_prima"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultadofinanceiro",
            name="penalidades",
            field=models.DecimalField(max_digits=12, decimal_places=2, default=0),
        ),
    ]

