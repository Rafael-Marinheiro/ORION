"""Remocao definitiva das pracas da base regional -- comando a parte.

O `seed_dados_base` aposenta zerando a demanda e nao apaga praca com
movimento: `Distribuicao.cidade` e CASCADE, e popular a base nao pode
destruir historico de brinde. Este comando e o caminho explicito para
quando o historico e descartavel, e so age com `--confirmar`.
"""

from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from app.models import (
    Cidade,
    CompraMateriaPrima,
    Distribuicao,
    Grupo,
    MateriaPrima,
    Produto,
)


@override_settings(MIGRATION_MODULES={"app": None})
class LimparPracasLegadasTest(TestCase):
    def setUp(self):
        self.legada = Cidade.objects.create(
            nome="Currais Novos", distancia_km=0, demanda=0
        )
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2
        )
        self.grupo = Grupo.objects.create(nome="Equipe de 2025", capital=Decimal("1000"))
        self.envio = Distribuicao.objects.create(
            grupo=self.grupo, produto=self.produto, cidade=self.legada, rodada=1,
            quantidade=10, preco_unitario=Decimal("100"), custo_transporte=Decimal("0"),
        )

    def _rodar(self, *args):
        saida = StringIO()
        call_command("limpar_pracas_legadas", *args, stdout=saida, stderr=saida)
        return saida.getvalue()

    def test_sem_confirmar_nao_apaga_nada(self):
        saida = self._rodar()

        self.assertTrue(Cidade.objects.filter(pk=self.legada.pk).exists())
        self.assertTrue(Distribuicao.objects.filter(pk=self.envio.pk).exists())
        self.assertIn("--confirmar", saida)

    def test_com_confirmar_apaga_a_praca_e_o_historico(self):
        self._rodar("--confirmar")

        self.assertFalse(Cidade.objects.filter(pk=self.legada.pk).exists())
        self.assertFalse(Distribuicao.objects.filter(pk=self.envio.pk).exists())

    def test_nao_toca_nas_pracas_do_91(self):
        recife = Cidade.objects.create(nome="Recife", distancia_km=290, demanda=4000)

        self._rodar("--confirmar")

        self.assertTrue(Cidade.objects.filter(pk=recife.pk).exists())

    def test_recusa_quando_ha_compra_de_materia_prima(self):
        """Compra ja debitou caixa: apagar aqui mascararia o financeiro."""
        mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("3")
        )
        CompraMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=mp, cidade_fornecedora=self.legada,
            rodada_pedido=1, rodada_recebimento=2, quantidade_kg=Decimal("10"),
            preco_unitario=Decimal("3"),
        )

        saida = self._rodar("--confirmar")

        self.assertTrue(Cidade.objects.filter(pk=self.legada.pk).exists())
        self.assertIn("caixa já debitado", saida)

    def test_banco_ja_limpo_nao_quebra(self):
        self._rodar("--confirmar")

        saida = self._rodar("--confirmar")

        self.assertIn("Nenhuma praça da base regional", saida)
