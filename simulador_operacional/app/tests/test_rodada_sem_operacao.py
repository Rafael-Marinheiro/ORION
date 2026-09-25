"""A tela não apresenta como medida o que a rodada não mediu.

Pelo §7.3 a matéria-prima pedida "fica disponível a partir da rodada
seguinte ao pedido": na rodada 1 nenhuma equipe produz nem vende. Ainda
assim o fechamento gravava EO 20,0 e DS 76,6 para todas — o terceiro termo
do §12.3.1 e o DS₁ do §12.3.4 dão 1 quando não há perdas, e não há o que
perder. São artefatos de denominador vazio, não desempenho.

A pontuação e a posição de uma rodada assim deixam de ser exibidas.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    Cidade,
    ConsolidadoRodadaGrupo,
    Distribuicao,
    GameConfig,
    Grupo,
    Jogo,
    Producao,
    Produto,
    Rodada,
    User,
)
from app.services.pontuacao import pares_com_operacao


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class OperacaoDaRodadaTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            email_usuario="ceo-op@teste.com", nome_usuario="CEO", password="senha123"
        )
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create()
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.grupo.membros.add(self.usuario)
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2
        )
        self.cidade = Cidade.objects.create(
            nome="Recife", distancia_km=290, demanda=4000
        )
        self.client.force_login(self.usuario)

    def _fechar(self, numero):
        Rodada.objects.create(
            jogo=self.jogo, numero=numero,
            fim=timezone.now() - timedelta(minutes=1), fechada=True,
        )

    def _consolidar(self, rodada, score="50"):
        return ConsolidadoRodadaGrupo.objects.create(
            grupo=self.grupo, rodada=rodada,
            score_multicriterio=Decimal(score),
            eo_percent=Decimal("20"), ds_percent=Decimal("76.62"),
        )

    def test_comprar_materia_prima_nao_conta_como_operacao(self):
        """7.3: a MP da rodada 1 só serve à produção da 2."""
        self._fechar(1)
        self._consolidar(1)

        self.assertEqual(pares_com_operacao([self.grupo], [1]), set())

    def test_produzir_conta_como_operacao(self):
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=2,
            quantidade_planejada=10, quantidade_produzida=10,
        )

        self.assertEqual(
            pares_com_operacao([self.grupo], [2]), {(self.grupo.id, 2)}
        )

    def test_ordem_de_producao_que_nao_produziu_nao_conta(self):
        """13.11: sem insumo a produção sai zero -- e zero não é operação."""
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=2,
            quantidade_planejada=10, quantidade_produzida=0,
        )

        self.assertEqual(pares_com_operacao([self.grupo], [2]), set())

    def test_despachar_conta_como_operacao(self):
        """Vender estoque de rodada anterior é operar, mesmo sem produzir."""
        Distribuicao.objects.create(
            grupo=self.grupo, produto=self.produto, cidade=self.cidade,
            rodada=3, quantidade=5, preco_unitario=Decimal("100"),
            custo_transporte=Decimal("0"),
        )

        self.assertEqual(
            pares_com_operacao([self.grupo], [3]), {(self.grupo.id, 3)}
        )

    def test_a_evolucao_marca_a_rodada_sem_operacao(self):
        self._fechar(1)
        self._fechar(2)
        self._consolidar(1, "8.26")
        self._consolidar(2, "52.78")
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=2,
            quantidade_planejada=10, quantidade_produzida=10,
        )

        evolucao = self.client.get(reverse("ranking")).context["evolucao_grupo"]

        self.assertEqual(
            evolucao,
            [
                {"rodada": 1, "posicao": None, "pontuacao": None, "operou": False},
                {"rodada": 2, "posicao": 1, "pontuacao": Decimal("52.78"), "operou": True},
            ],
        )

    def test_a_tela_escreve_sem_operacao_no_lugar_do_numero(self):
        self._fechar(1)
        self._consolidar(1, "8.26")

        corpo = self.client.get(reverse("ranking")).content.decode()

        self.assertIn("sem operação", corpo)
        self.assertNotIn("8,26", corpo)
        # os artefatos de denominador vazio tambem somem da tabela
        self.assertNotIn("20,0", corpo)
        self.assertNotIn("76,6", corpo)

    def test_a_tela_explica_por_que_a_rodada_nao_classifica(self):
        self._fechar(1)
        self._consolidar(1, "8.26")

        resposta = self.client.get(reverse("ranking"))

        self.assertTrue(resposta.context["rodada_sem_operacao"])
        self.assertContains(resposta, "só fica disponível na rodada seguinte")

    def test_rodada_sem_operacao_nao_tem_destaques(self):
        """Coroar o lider de uma rodada que ninguem jogou nao ensina nada."""
        self._fechar(1)
        self._consolidar(1, "8.26")

        resposta = self.client.get(reverse("ranking"))

        self.assertEqual(resposta.context["destaques"], [])
        self.assertNotContains(resposta, "Líder da rodada")

    def test_rodada_com_operacao_continua_classificando(self):
        self._fechar(2)
        self._consolidar(2, "52.78")
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=2,
            quantidade_planejada=10, quantidade_produzida=10,
        )

        resposta = self.client.get(reverse("ranking"))

        self.assertFalse(resposta.context["rodada_sem_operacao"])
        self.assertContains(resposta, "52,78")
        self.assertContains(resposta, "Líder da rodada")

    def test_o_grafico_deixa_lacuna_na_rodada_sem_operacao(self):
        self._fechar(1)
        self._fechar(2)
        self._consolidar(1, "8.26")
        self._consolidar(2, "52.78")
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=2,
            quantidade_planejada=10, quantidade_produzida=10,
        )

        grafico = self.client.get(reverse("ranking")).context["grafico_posicoes"]

        self.assertEqual(grafico["series"][0]["data"], [None, 1])
