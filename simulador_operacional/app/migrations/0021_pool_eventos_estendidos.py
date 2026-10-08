from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_evento_manual'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='extensao',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='gameconfig',
            name='eventos_estendidos',
            field=models.BooleanField(default=False),
        ),
    ]
