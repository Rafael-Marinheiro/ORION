"""Aviso de risco de perda de estoque -- 6.2.

O aviso declara um estado e nada mais: "Risco de perda de estoque". Nao diz
quanto, nao diz qual produto, nao diz o que fazer. Rafael, 24/09/2026: "O
que nao acontece na vida real, eles como gestores devem conhecer os
produtos, suas caracteristicas, e efeitos das escolhas."

O aviso anterior fazia o contrario -- somava a perda, nomeava o produto e
mandava distribuir. Alem de tutelar, tinha deixado de funcionar: olhava
estoque de perecivel atravessando rodadas, e desde que o B passou a vencer
no fechamento da propria rodada isso nao existe mais.
"""

from decimal import Decimal

from django.test import TestCase, override_settings

from app.models import (
    Cidade,
    Distribuicao,
    EstoqueProduto,
    Grupo,
    Producao,
    Produto,
)
from app.services.perecibilidade import risco_de_perda_de_estoque


@override_settings(MIGRATION_MODULES={"app": None})
class RiscoDePerdaTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100000"))
        self.b = Produto.objects.create(
            codigo="B", nome="Produto B", tempo_producao_min=4,
            perecivel=True, validade_rodadas=1,
        )
        self.a = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2, perecivel=False
        )
        self.cidade = Cidade.objects.create(
            nome="Recife", distancia_km=290, demanda=4000
        )

    def _produzir(self, produto, quantidade, rodada=1):
        return Producao.objects.create(
            grupo=self.grupo, produto=produto, rodada=rodada,
            quantidade_planejada=quantidade,
        )

    def _distribuir(self, produto, quantidade, rodada=1, expedida=False):
        return Distribuicao.objects.create(
            grupo=self.grupo, produto=produto, cidade=self.cidade, rodada=rodada,
            quantidade=quantidade, preco_unitario=Decimal("10"),
            custo_transporte=Decimal("0"), expedida=expedida,
        )

    def test_producao_de_perecivel_sem_destino_acende_o_aviso(self):
        self._produzir(self.b, 500)

        self.assertTrue(risco_de_perda_de_estoque(self.grupo, 1))

    def test_producao_inteira_destinada_nao_acende(self):
        self._produzir(self.b, 500)
        self._distribuir(self.b, 500)

        self.assertFalse(risco_de_perda_de_estoque(self.grupo, 1))

    def test_sobra_parcial_acende(self):
        self._produzir(self.b, 500)
        self._distribuir(self.b, 300)

        self.assertTrue(risco_de_perda_de_estoque(self.grupo, 1))

    def test_destino_acima_da_producao_nao_acende(self):
        """Enviar mais do que produziu e outro problema -- o 13.11 apara no
        fechamento --, e nao e perda de estoque."""
        self._produzir(self.b, 300)
        self._distribuir(self.b, 500)

        self.assertFalse(risco_de_perda_de_estoque(self.grupo, 1))

    def test_produto_nao_perecivel_nunca_acende(self):
        """6.2: o A "pode ser estocado por tempo indefinido". Sobra dele vira
        custo de armazenagem, nao perda."""
        self._produzir(self.a, 5000)

        self.assertFalse(risco_de_perda_de_estoque(self.grupo, 1))

    def test_estoque_de_perecivel_parado_acende_mesmo_sem_producao(self):
        """Nao deveria existir depois do 6.2, mas se existir e perda certa."""
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=1, quantidade=40
        )

        self.assertTrue(risco_de_perda_de_estoque(self.grupo, 1))

    def test_envio_ja_expedido_nao_conta_como_destino(self):
        """Carga expedida saiu do armazem: nao absorve a producao desta rodada."""
        self._produzir(self.b, 500)
        self._distribuir(self.b, 500, expedida=True)

        self.assertTrue(risco_de_perda_de_estoque(self.grupo, 1))

    def test_destino_de_outra_rodada_nao_conta(self):
        self._produzir(self.b, 500)
        self._distribuir(self.b, 500, rodada=2)

        self.assertTrue(risco_de_perda_de_estoque(self.grupo, 1))

    def test_sem_rodada_aberta_nao_quebra(self):
        self._produzir(self.b, 500)

        self.assertFalse(risco_de_perda_de_estoque(self.grupo, None))
        self.assertFalse(risco_de_perda_de_estoque(None, 1))

    def test_grupo_sem_decisao_nao_acende(self):
        self.assertFalse(risco_de_perda_de_estoque(self.grupo, 1))
