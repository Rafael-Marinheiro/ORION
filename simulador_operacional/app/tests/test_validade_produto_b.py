"""Validade do produto perecivel -- 6.2, ratificado pelo Dr. Pio em 24/09/2026.

"Produto B: produzido e enviado na mesma rodada. O que ficar para ser
enviado depois vira perda." E o que o 6.2 ja dizia por escrito: "perde
validade apos 1 rodada. Unidades nao comercializadas ate o encerramento da
rodada sao descartadas automaticamente."

Ate 24/09/2026 o codigo dava ao B uma rodada de sobrevida -- produzido em N,
ainda vendavel em N+1. Duas rodadas de vida sao a regra do 13.8, que a
decisao B2 tinha descartado em favor do 6.2. Estes testes existem para o B
nao virar de novo "um A com prazo".
"""

from decimal import Decimal

from django.test import TestCase, override_settings

from app.models import (
    ComposicaoProduto,
    EstoqueProduto,
    Grupo,
    MateriaPrima,
    Produto,
)
from app.services.perecibilidade import lote_vencido, lotes_a_vencer


@override_settings(MIGRATION_MODULES={"app": None})
class ValidadeDoPerecivelTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100000"))
        # 6.2: B e o unico perecivel do portfolio.
        self.b = Produto.objects.create(
            codigo="B", nome="Produto B", tempo_producao_min=4,
            perecivel=True, validade_rodadas=1,
        )
        self.a = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2,
            perecivel=False, validade_rodadas=0,
        )

    def _lote(self, produto, rodada_entrada, quantidade=10):
        return EstoqueProduto.objects.create(
            grupo=self.grupo,
            produto=produto,
            rodada_entrada=rodada_entrada,
            quantidade=quantidade,
        )

    def test_b_nao_enviado_vence_no_fechamento_da_propria_rodada(self):
        """O que ficou para ser enviado depois ja e perda."""
        lote = self._lote(self.b, rodada_entrada=3)

        self.assertTrue(lote_vencido(lote, 3))

    def test_b_nao_sobrevive_para_a_rodada_seguinte(self):
        """Sobrevida de uma rodada seria a validade de 2 rodadas do 13.8."""
        lote = self._lote(self.b, rodada_entrada=3)

        self.assertTrue(lote_vencido(lote, 4))

    def test_a_nunca_vence(self):
        """6.2: "estocado por tempo indefinido"; producao antecipada e a
        estrategia propria do A."""
        lote = self._lote(self.a, rodada_entrada=1)

        self.assertEqual(lotes_a_vencer(self.grupo, 9), [])

    def test_o_aviso_de_tela_usa_a_mesma_regra_do_fechamento(self):
        """A condicao vivia duplicada; uma copia podia mudar sem a outra."""
        lote = self._lote(self.b, rodada_entrada=2)

        self.assertEqual(lotes_a_vencer(self.grupo, 2), [lote])


@override_settings(MIGRATION_MODULES={"app": None})
class PerdaTotalNoFechamentoTest(TestCase):
    """O vencido vira perda total: sem venda com desconto, sem reembolso."""

    def setUp(self):
        from app.management.commands.fechar_rodadas import Command

        self.fechar = Command()
        self.grupo = Grupo.objects.create(nome="Equipe Rigel", capital=Decimal("100000"))
        self.b = Produto.objects.create(
            codigo="B", nome="Produto B", tempo_producao_min=4,
            perecivel=True, validade_rodadas=1,
        )
        # `custo_unitario_estimado` e derivado da composicao (6.1): 2 kg a
        # R$ 3 dao R$ 6 por unidade, que e o valor da perda por unidade.
        mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("3")
        )
        ComposicaoProduto.objects.create(
            produto=self.b, materia_prima=mp, quantidade_por_unidade=Decimal("2")
        )

    def test_o_saldo_nao_enviado_e_baixado_e_lancado_como_perda(self):
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=1, quantidade=10
        )

        perda = self.fechar.processar_perecibilidade(self.grupo, 1)

        self.assertEqual(perda, Decimal("60"))
        lote = EstoqueProduto.objects.get(grupo=self.grupo, produto=self.b)
        self.assertEqual(lote.quantidade, 0)

    def test_sem_estoque_de_perecivel_nao_ha_perda(self):
        self.assertEqual(self.fechar.processar_perecibilidade(self.grupo, 1), Decimal("0"))
