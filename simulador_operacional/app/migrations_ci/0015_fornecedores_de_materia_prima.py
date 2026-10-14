from django.db import migrations, models


class Migration(migrations.Migration):
    """7.1 -- fornecedores por materia-prima.

    Sem isto a compra aceitava qualquer praca, e a estrategia otima virava
    trazer as quatro MPs da cidade mais proxima.
    """

    dependencies = [
        ('app', '0014_evento_unico_por_jogo'),
    ]

    operations = [
        migrations.AddField(
            model_name='materiaprima',
            name='fornecedores',
            field=models.ManyToManyField(
                blank=True, related_name='materias_fornecidas', to='app.cidade'
            ),
        ),
    ]
