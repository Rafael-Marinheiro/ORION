from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import (
    ConsolidadoRodadaGrupo,
    GameConfig,
    Grupo,
    Jogo,
    Producao,
    Produto,
    Rodada,
    User,
)


class RankingViewTest(TestCase):
    def setUp(self):
        usuario = User.objects.create_user(
            email_usuario="ceo@teste.com", nome_usuario="CEO", password="senha123"
        )
        self.jogo = Jogo.objects.create(nome="Turma A", config=GameConfig.objects.create())
        self.vega = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.rigel = Grupo.objects.create(nome="Equipe Rigel", jogo=self.jogo)
        self.vega.membros.add(usuario)
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2
        )
        self.client.force_login(usuario)

    def _consolidar(self, grupo, rodada, score, lucro=0, market_share=0, operou=True):
        if operou:
            # Rodada em que a equipe produziu: sem isso ela conta como "sem
            # operacao" e a tela nao apresenta posicao nem pontuacao, porque
            # pelo 7.3 a rodada 1 nao tem como medir desempenho.
            Producao.objects.get_or_create(
                grupo=grupo, produto=self.produto, rodada=rodada,
                defaults={"quantidade_planejada": 10, "quantidade_produzida": 10},
            )
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
        # O grafico de posicoes responde "quem estava na frente NAQUELA
        # rodada" quando o mouse para nela; sem a bandeira o tooltip volta a
        # listar as equipes na ordem em que as series foram criadas.
        self.assertContains(response, "tooltipClassificacao: true")
        self.assertEqual(
            response.context["evolucao_grupo"],
            [
                {"rodada": 1, "posicao": 2, "pontuacao": Decimal("60"), "operou": True},
                {"rodada": 2, "posicao": 1, "pontuacao": Decimal("90"), "operou": True},
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

    def test_antes_do_primeiro_fechamento_a_tela_lista_sem_destacar(self):
        """Sem rodada fechada não há market share nem líder consolidados.

        A lista existe para mostrar quem está no jogo. Até 25/09/2026 a tela
        também coroava "Líder da rodada" com 0,00 pontos -- um desempenho que
        ninguém teve.
        """
        response = self.client.get(reverse("ranking"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Equipe Vega")
        self.assertEqual(response.context["destaques"], [])
        self.assertNotContains(response, "Maior participação de mercado")
