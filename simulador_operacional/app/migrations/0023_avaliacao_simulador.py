from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0022_evento_de_decisao'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvaliacaoSimulador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('papel', models.CharField(choices=[('aluno', 'Aluno'), ('docente', 'Docente/Moderador')], max_length=10)),
                ('respostas', models.JSONField(blank=True, default=dict)),
                ('comentarios', models.JSONField(blank=True, default=dict)),
                ('data', models.DateTimeField(auto_now_add=True)),
                ('jogo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='avaliacoes', to='app.jogo')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avaliacoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Avaliacao do Simulador',
                'verbose_name_plural': 'Avaliacoes do Simulador',
                'db_table': 'AVALIACOES_SIMULADOR',
                'ordering': ['-data'],
            },
        ),
        migrations.AddConstraint(
            model_name='avaliacaosimulador',
            constraint=models.UniqueConstraint(fields=('usuario', 'jogo'), name='avaliacao_unica_por_usuario_e_turma'),
        ),
    ]
