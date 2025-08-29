from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("app", "0007_grupo_lider"),
    ]

    operations = [
        migrations.AddField(
            model_name="grupo",
            name="materia_prima",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
