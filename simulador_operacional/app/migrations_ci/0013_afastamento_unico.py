from django.db import migrations


class Migration(migrations.Migration):
    """O afastamento do evento de decisao passou a ser valor unico.

    A faixa (piso + teto) saiu: o Product Owner decidiu que todas as
    equipes que recusarem a oferta tem o MESMO afastamento, para o jogo
    ser simetrico. Sobra o campo do valor.
    """

    dependencies = [
        ('app', '0012_avaliacao_simulador'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='evento',
            name='impacto_percentual_minimo',
        ),
    ]
