import app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_evento_frase_indicativa'),
    ]

    operations = [
        migrations.AddField(
            model_name='consolidadorodadagrupo',
            name='eo_percent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='consolidadorodadagrupo',
            name='df_percent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='consolidadorodadagrupo',
            name='sd_percent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='consolidadorodadagrupo',
            name='ds_percent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='consolidadorodadagrupo',
            name='valor_estoques',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='evento',
            name='retencao_entregas_percent',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='gameconfig',
            name='ranking_pesos',
            field=models.JSONField(blank=True, default=app.models.default_ranking_pesos),
        ),
    ]
