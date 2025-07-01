from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_gameconfig_trabalhadores_iniciais_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameconfig',
            name='maquinas_iniciais_a',
            field=models.PositiveIntegerField(default=15),
        ),
        migrations.AddField(
            model_name='gameconfig',
            name='maquinas_iniciais_b',
            field=models.PositiveIntegerField(default=15),
        ),
        migrations.AddField(
            model_name='gameconfig',
            name='maquinas_iniciais_c',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AddField(
            model_name='grupo',
            name='maquinas_a',
            field=models.PositiveIntegerField(default=15),
        ),
        migrations.AddField(
            model_name='grupo',
            name='maquinas_b',
            field=models.PositiveIntegerField(default=15),
        ),
        migrations.AddField(
            model_name='grupo',
            name='maquinas_c',
            field=models.PositiveIntegerField(default=10),
        ),
    ]
