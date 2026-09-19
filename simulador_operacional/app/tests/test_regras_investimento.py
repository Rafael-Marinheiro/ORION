"""Limite de expansao (14.2.1) e restricao por caixa negativo (RN-09).

As duas regras estavam na especificacao e em lugar nenhum do codigo: dava
para comprar maquina sem teto e para investir insolvente, que sao exatamente
os dois movimentos que a aula quer punir.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import (
    Cidade,
    ConsolidadoRodadaGrupo,
    GameConfig,
    Grupo,
    Investimento,
    Produto,
    Rodada,
    User,
)
from app.services.investimentos import (
    caixa_negativo_consecutivo,
    impedimento_para_investir,
    limite_de_expansao,
)


class LimiteDeExpansaoTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000000"))
        self.produto = Produto.objects.create(codigo="A", nome="Produto A", tempo_producao_min=1)
        GameConfig.objects.create(maquinas_iniciais=40)

    def _compra(self, quantidade):
        return Investimento(
            grupo=self.grupo,
            categoria="maquinas",
            produto=self.produto,
            quantidade=quantidade,
            valor=Decimal("8000"),
        )

    def test_teto_e_metade_do_parque_inicial(self):
        """14.2.1: "ate 50% sobre a quantidade inicial instalada"."""
        self.assertEqual(limite_de_expansao(self.grupo)["teto"], 20)

    def test_compra_dentro_do_teto_passa(self):
        self.assertIsNone(impedimento_para_investir(self.grupo, self._compra(20)))

    def test_compra_acima_do_teto_e_barrada(self):
        impedimento = impedimento_para_investir(self.grupo, self._compra(21))

        self.assertIn("Limite de expansão", impedimento)

    def test_teto_vale_para_a_simulacao_toda_nao_por_rodada(self):
        Investimento.objects.create(
            grupo=self.grupo,
            rodada=1,
            categoria="maquinas",
            produto=self.produto,
            quantidade=20,
            valor=Decimal("160000"),
        )

        self.assertEqual(limite_de_expansao(self.grupo)["restante"], 0)
        self.assertIsNotNone(impedimento_para_investir(self.grupo, self._compra(1)))

    def test_compra_pendente_ja_consome_o_limite(self):
        """Nao processada ainda, mas ja comprometida: senao da para furar o teto."""
        Investimento.objects.create(
            grupo=self.grupo,
            rodada=1,
            categoria="maquinas",
            produto=self.produto,
            quantidade=15,
            valor=Decimal("120000"),
            processado=False,
        )

        self.assertEqual(limite_de_expansao(self.grupo)["restante"], 5)

    def test_outras_categorias_nao_esbarram_no_teto(self):
        investimento = Investimento(
            grupo=self.grupo, categoria="rh", produto=self.produto, quantidade=500, valor=Decimal("1")
        )

        self.assertIsNone(impedimento_para_investir(self.grupo, investimento))


class RestricaoPorCaixaNegativoTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000"))
        GameConfig.objects.create(maquinas_iniciais=40)

    def _fechamento(self, rodada, saldo):
        ConsolidadoRodadaGrupo.objects.create(
            grupo=self.grupo, rodada=rodada, saldo_caixa=Decimal(saldo)
        )

    def _marketing(self):
        return Investimento(grupo=self.grupo, categoria="marketing", valor=Decimal("1000"))

    def test_uma_rodada_negativa_ainda_permite_investir(self):
        self._fechamento(1, 5000)
        self._fechamento(2, -100)

        self.assertEqual(caixa_negativo_consecutivo(self.grupo), 1)
        self.assertIsNone(impedimento_para_investir(self.grupo, self._marketing()))

    def test_duas_rodadas_negativas_bloqueiam(self):
        """RN-09: "por duas rodadas consecutivas implica na restricao"."""
        self._fechamento(1, -50)
        self._fechamento(2, -100)

        impedimento = impedimento_para_investir(self.grupo, self._marketing())

        self.assertIn("RN-09", impedimento)

    def test_recuperar_o_caixa_libera_de_novo(self):
        self._fechamento(1, -50)
        self._fechamento(2, -100)
        self._fechamento(3, 200)

        self.assertEqual(caixa_negativo_consecutivo(self.grupo), 0)
        self.assertIsNone(impedimento_para_investir(self.grupo, self._marketing()))

    def test_resgate_de_aplicacao_nunca_e_bloqueado(self):
        """Quem esta sem caixa precisa justamente resgatar: RN-09 restringe investir."""
        self._fechamento(1, -50)
        self._fechamento(2, -100)
        resgate = Investimento(
            grupo=self.grupo,
            categoria="financeiro",
            operacao_financeira="resgatar",
            valor=Decimal("1000"),
        )

        self.assertIsNone(impedimento_para_investir(self.grupo, resgate))

    def test_aplicar_com_caixa_negativo_e_bloqueado(self):
        self._fechamento(1, -50)
        self._fechamento(2, -100)
        aplicacao = Investimento(
            grupo=self.grupo,
            categoria="financeiro",
            operacao_financeira="aplicar",
            valor=Decimal("1000"),
        )

        self.assertIsNotNone(impedimento_para_investir(self.grupo, aplicacao))


class PainelBloqueiaOInvestimentoTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email_usuario="ceo@teste.com",
            nome_usuario="CEO",
            password="senha123",
            tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000000"))
        self.grupo.membros.add(self.user)
        self.grupo.lider = self.user
        self.grupo.save()
        self.produto = Produto.objects.create(codigo="A", nome="Produto A", tempo_producao_min=1)
        GameConfig.objects.create(maquinas_iniciais=40)
        self.cidade = Cidade.objects.create(nome="Caico", distancia_km=100, demanda=200)
        Rodada.objects.create(numero=3, fim=timezone.now() + timedelta(hours=1))
        ConsolidadoRodadaGrupo.objects.create(grupo=self.grupo, rodada=1, saldo_caixa=Decimal("-10"))
        ConsolidadoRodadaGrupo.objects.create(grupo=self.grupo, rodada=2, saldo_caixa=Decimal("-20"))
        self.client.force_login(self.user)

    def test_investimento_bloqueado_nao_debita_o_capital(self):
        capital_antes = self.grupo.capital

        resposta = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_investimento": "1",
                "categoria": "marketing",
                "cidade": self.cidade.id,
                "valor": "5000",
                "quantidade": "1",
            },
            follow=True,
        )

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.capital, capital_antes)
        self.assertEqual(Investimento.objects.filter(grupo=self.grupo).count(), 0)
        self.assertIn("RN-09", resposta.content.decode())
