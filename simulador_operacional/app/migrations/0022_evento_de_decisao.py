from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_pool_eventos_estendidos'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='impacto_percentual_minimo',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='evento',
            name='custo_unitario_decisao',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.CreateModel(
            name='DecisaoEventoGrupo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rodada', models.PositiveIntegerField()),
                ('aceitou', models.BooleanField(default=False)),
                ('custo', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('afetados_percent', models.PositiveIntegerField(default=0)),
                ('data', models.DateTimeField(auto_now_add=True)),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decisoes', to='app.evento')),
                ('grupo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decisoes_evento', to='app.grupo')),
            ],
            options={
                'verbose_name': 'Decisao de Evento',
                'verbose_name_plural': 'Decisoes de Evento',
                'db_table': 'DECISOES_EVENTO',
            },
        ),
        migrations.AddConstraint(
            model_name='decisaoeventogrupo',
            constraint=models.UniqueConstraint(fields=('grupo', 'rodada', 'evento'), name='decisao_evento_unica_por_rodada'),
        ),
    ]
