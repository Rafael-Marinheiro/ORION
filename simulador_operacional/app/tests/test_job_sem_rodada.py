"""Chamada sem rodada a fechar nao vira linha na tela de execucoes.

Na turma o `fechar_rodadas` roda de segundo em segundo (ver
`docker-compose.turma.yml`) para cumprir o "momento exato do prazo-limite"
do 11.1. Cada chamada gravava um `ExecucaoJob`, e a tela de execucoes --
onde o professor procura o que aconteceu no prazo -- mostra as 200 ultimas:
em pouco mais de tres minutos de aula nenhum fechamento de verdade cabia
mais na lista.
"""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from app.models import ExecucaoJob, Rodada


@override_settings(MIGRATION_MODULES={"app": None})
class JobDeFechamentoTest(TestCase):
    def test_sem_rodada_vencida_nao_grava_execucao(self):
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))

        call_command("fechar_rodadas", stdout=StringIO())

        self.assertFalse(ExecucaoJob.objects.exists())

    def test_fechamento_de_verdade_continua_registrado(self):
        Rodada.objects.create(numero=1, fim=timezone.now() - timedelta(minutes=1))

        call_command("fechar_rodadas", stdout=StringIO())

        job = ExecucaoJob.objects.get()
        self.assertEqual(job.comando, "fechar_rodadas")
        self.assertEqual(job.status, "sucesso")
        self.assertIsNotNone(job.finalizado_em)
