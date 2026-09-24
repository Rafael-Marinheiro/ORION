"""Producao parcial no fechamento -- 13.7 e 13.11.

O 13.7 descreve a logica da rodada terminando em "producao parcial, se
necessario, limitada pelo tempo ou insumos", e o 13.11 repete: "sem insumos
suficientes -> producao parcial por linha" e "tempo excedido em determinada
linha -> producao ajustada ao tempo disponivel por produto".

Ate 2026-09-24 nao havia producao parcial: o painel recusava a ordem que
excedesse capacidade ou insumo, e gravava quantidade_produzida igual a
planejada. Estes testes existem para isso nao voltar.
"""

from decimal import Decimal

from django.test import TestCase, override_settings

from app.models import (
    CapacidadeProdutoGrupo,
    ComposicaoProduto,
    EstoqueMateriaPrima,
    EstoqueProduto,
    Grupo,
    MateriaPrima,
    Producao,
    Produto,
)
from app.services.producao import executar_producao


@override_settings(MIGRATION_MODULES={"app": None})
class ProducaoParcialTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100000"))
        self.mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("3")
        )
        # 1 minuto e 2 kg por unidade: o tempo nunca limita nestes cenarios,
        # entao quem manda e o insumo.
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=1
        )
        ComposicaoProduto.objects.create(
            produto=self.produto, materia_prima=self.mp, quantidade_por_unidade=Decimal("2")
        )
        CapacidadeProdutoGrupo.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            maquinas=1,
            operadores=2,
            minutos_por_maquina=400,
        )

    def _estocar_mp(self, kg):
        EstoqueMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=self.mp, quantidade_kg=Decimal(str(kg))
        )

    def _ordenar(self, quantidade):
        return Producao.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            rodada=1,
            quantidade_planejada=quantidade,
        )

    def _produzido(self):
        return Producao.objects.get(grupo=self.grupo, rodada=1).quantidade_produzida

    def _saldo_mp(self):
        return EstoqueMateriaPrima.objects.get(
            grupo=self.grupo, materia_prima=self.mp
        ).quantidade_kg

    def test_ordem_de_dez_com_insumo_para_oito_produz_oito(self):
        """O caso do 13.11: falta insumo, sai o que da."""
        self._estocar_mp(16)  # 16 kg / 2 kg por unidade = 8 unidades
        self._ordenar(10)

        executar_producao(grupo=self.grupo, rodada=1)

        self.assertEqual(self._produzido(), 8)
        self.assertEqual(self._saldo_mp(), Decimal("0"))

    def test_sobra_o_que_nao_completa_uma_unidade(self):
        """Nao se produz meia unidade: 17 kg dao 8 unidades e sobra 1 kg."""
        self._estocar_mp(17)
        self._ordenar(10)

        executar_producao(grupo=self.grupo, rodada=1)

        self.assertEqual(self._produzido(), 8)
        self.assertEqual(self._saldo_mp(), Decimal("1"))

    def test_insumo_de_sobra_produz_o_pedido_e_nao_mais(self):
        """Producao parcial nao vira producao livre: o pedido e o teto."""
        self._estocar_mp(1000)
        self._ordenar(10)

        executar_producao(grupo=self.grupo, rodada=1)

        self.assertEqual(self._produzido(), 10)
        self.assertEqual(self._saldo_mp(), Decimal("980"))

    def test_sem_insumo_nenhum_nao_produz_e_nao_cobra(self):
        self._estocar_mp(0)
        self._ordenar(10)

        custo, ajustes = executar_producao(grupo=self.grupo, rodada=1)

        self.assertEqual(self._produzido(), 0)
        self.assertEqual(custo, Decimal("0"))
        self.assertEqual(ajustes[0]["limitador"], "matéria-prima")

    def test_tempo_da_linha_limita_antes_do_insumo(self):
        """13.11: "tempo excedido -> producao ajustada ao tempo disponivel".

        A linha tem 400 min e o produto leva 1 min: teto de 400 unidades,
        mesmo com insumo para 1.000.
        """
        self._estocar_mp(2000)
        self._ordenar(1000)

        _, ajustes = executar_producao(grupo=self.grupo, rodada=1)

        self.assertEqual(self._produzido(), 400)
        self.assertEqual(ajustes[0]["limitador"], "tempo de linha")

    def test_so_cobra_o_que_saiu(self):
        """13.9: "o custo corresponde ao valor das materias-primas consumidas"."""
        self._estocar_mp(16)
        self._ordenar(10)

        custo, _ = executar_producao(grupo=self.grupo, rodada=1)

        # 8 unidades x 2 kg x R$ 3 = R$ 48, nao as 10 pedidas
        self.assertEqual(custo, Decimal("48"))

    def test_o_produzido_vai_para_o_estoque_de_acabados(self):
        """13.7, ultimo passo: "transferencia para o estoque de acabados"."""
        self._estocar_mp(16)
        self._ordenar(10)

        executar_producao(grupo=self.grupo, rodada=1)

        lote = EstoqueProduto.objects.get(grupo=self.grupo, produto=self.produto)
        self.assertEqual(lote.quantidade, 8)
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.estoque, 8)
