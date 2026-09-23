"""O custo do ranking nao pode crescer com o numero de rodadas fechadas.

O grafico de posicoes e a evolucao do grupo percorrem todas as rodadas
fechadas. Enquanto filtravam por rodada dentro do laco, cada rodada nova
custava duas consultas a mais -- e a simulacao fecha uma rodada por aula.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import ConsolidadoRodadaGrupo, Grupo, Rodada


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RankingNaoEscalaEmConsultasTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.professor = User.objects.create_user(
            email_usuario="professor-ranking@example.com",
            nome_usuario="Professor",
            password="pass",
            tipo_usuario="gamemaster",
        )
        self.grupos = [
            Grupo.objects.create(nome=f"Equipe {letra}", capital=Decimal("1000000"))
            for letra in "ABCD"
        ]
        self.client.login(username="professor-ranking@example.com", password="pass")

    def _fechar_rodada(self, numero):
        Rodada.objects.create(
            numero=numero, fim=timezone.now() - timedelta(days=1), fechada=True
        )
        for posicao, grupo in enumerate(self.grupos):
            ConsolidadoRodadaGrupo.objects.create(
                grupo=grupo,
                rodada=numero,
                score_multicriterio=Decimal(90 - posicao),
                receita_vendas=Decimal("1000"),
                lucro_rodada=Decimal("100"),
            )

    def _consultas_do_ranking(self):
        with CaptureQueriesContext(connection) as consultas:
            resposta = self.client.get(reverse("ranking"))
        self.assertEqual(resposta.status_code, 200)
        return len(consultas)

    def test_consultas_nao_crescem_com_as_rodadas(self):
        self._fechar_rodada(1)
        self._fechar_rodada(2)
        com_duas = self._consultas_do_ranking()

        for numero in range(3, 9):
            self._fechar_rodada(numero)
        com_oito = self._consultas_do_ranking()

        self.assertEqual(
            com_oito,
            com_duas,
            f"ranking passou de {com_duas} para {com_oito} consultas ao fechar mais seis rodadas",
        )
