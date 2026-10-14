from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_afastamento_unico'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='unico_por_jogo',
            field=models.BooleanField(default=False),
        ),
    ]
