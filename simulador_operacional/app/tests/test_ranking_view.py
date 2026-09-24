from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import ConsolidadoRodadaGrupo, GameConfig, Grupo, Jogo, Rodada, User


class RankingViewTest(TestCase):
    def setUp(self):
        usuario = User.objects.create_user(
            email_usuario="ceo@teste.com", nome_usuario="CEO", password="senha123"
        )
        self.jogo = Jogo.objects.create(nome="Turma A", config=GameConfig.objects.create())
        self.vega = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.rigel = Grupo.objects.create(nome="Equipe Rigel", jogo=self.jogo)
        self.vega.membros.add(usuario)
        self.client.force_login(usuario)

    def _consolidar(self, grupo, rodada, score, lucro=0, market_share=0):
        return ConsolidadoRodadaGrupo.objects.create(
            grupo=grupo, rodada=rodada, score_multicriterio=Decimal(score),
            lucro_rodada=Decimal(lucro), market_share_percent=Decimal(market_share),
        )

    def test_exibe_destaques_e_evolucao_com_a_posicao_de_cada_rodada(self):
        for numero in (1, 2):
            Rodada.objects.create(
                jogo=self.jogo, numero=numero,
                fim=timezone.now() - timedelta(minutes=1), fechada=True,
            )
        self._consolidar(self.vega, 1, "60", lucro="120", market_share="40")
        self._consolidar(self.rigel, 1, "80", lucro="100", market_share="60")
        self._consolidar(self.vega, 2, "90", lucro="150", market_share="55")
        self._consolidar(self.rigel, 2, "70", lucro="200", market_share="45")

        response = self.client.get(reverse("ranking"))

        self.assertContains(response, "Destaques da rodada")
        self.assertContains(response, "Maior lucro")
        self.assertContains(response, "Evolução do seu grupo")
        self.assertEqual(
            response.context["destaques"],
            [
                # `formato` acompanha o dado: ate 24/09/2026 a unidade era
                # escolhida no template pela POSICAO na lista.
                {"titulo": "Líder da rodada", "grupo": "Equipe Vega",
                 "valor": Decimal("90.00"), "formato": "pontos"},
                {"titulo": "Maior lucro", "grupo": "Equipe Rigel",
                 "valor": Decimal("200"), "formato": "moeda"},
                {"titulo": "Maior participação de mercado", "grupo": "Equipe Vega",
                 "valor": Decimal("55"), "formato": "percentual"},
            ],
        )
        self.assertEqual(
            response.context["evolucao_grupo"],
            [
                {"rodada": 1, "posicao": 2, "pontuacao": Decimal("60")},
                {"rodada": 2, "posicao": 1, "pontuacao": Decimal("90")},
            ],
        )
        self.assertEqual(
            response.context["grafico_posicoes"],
            {
                "labels": ["R1", "R2"],
                "series": [
                    {"label": "Equipe Rigel", "data": [1, 2], "type": "line"},
                    {"label": "Equipe Vega", "data": [2, 1], "type": "line"},
                ],
            },
        )

    def test_exibe_ranking_provisorio_sem_participacao_de_mercado(self):
        """Antes da primeira rodada fechada não há market share consolidado."""
        response = self.client.get(reverse("ranking"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Equipe Vega")
        self.assertContains(response, "Maior participação de mercado")
