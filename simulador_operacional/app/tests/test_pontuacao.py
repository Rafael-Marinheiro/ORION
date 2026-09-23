"""Classificacao multicriterio do documento 12.

Ate aqui o fechamento pontuava por quatro metricas inventadas pelo codigo
(lucro normalizado, market share, atendimento, eficiencia de estoque) e
Sustentabilidade -- um dos cinco eixos do 12.2 -- nao existia em lugar
nenhum. Estes testes fixam as formulas do documento.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from app.models import (
    Cidade,
    ComposicaoProduto,
    Decisao,
    Distribuicao,
    EstoqueMateriaPrima,
    EstoqueProduto,
    Grupo,
    MateriaPrima,
    Producao,
    Produto,
    Rodada,
)
from app.parametros import PESOS_DF, PESOS_DS, PESOS_EIXOS, PESOS_EO, PESOS_SD
from app.services.pontuacao import (
    calcular_eixos,
    coletar_insumos,
    desempenho_financeiro,
    eficiencia_estoques,
    eficiencia_operacional,
    ordenar_classificacao,
    pontuacao_total,
    satisfacao_demanda,
    sustentabilidade,
    valor_dos_estoques,
)


class PesosDoDocumentoTest(TestCase):
    def test_eixos_somam_um(self):
        """12.2: "Os pesos P1 a P5 devem somar 1"."""
        self.assertEqual(sum(PESOS_EIXOS.values()), Decimal("1"))

    def test_pesos_da_tabela_12_4(self):
        self.assertEqual(
            PESOS_EIXOS,
            {
                "EO": Decimal("0.30"),
                "DF": Decimal("0.25"),
                "EE": Decimal("0.15"),
                "SD": Decimal("0.20"),
                "DS": Decimal("0.10"),
            },
        )

    def test_pesos_internos_somam_um(self):
        for pesos in (PESOS_EO, PESOS_DF, PESOS_DS, PESOS_SD):
            self.assertEqual(sum(pesos), Decimal("1"), pesos)


class FormulasTest(TestCase):
    def test_eficiencia_operacional(self):
        # 0,8x0,4 + 0,9x0,4 + (1-0,1)x0,2
        eo = eficiencia_operacional(
            produzido=80, planejado=100, vendidos=90, disponiveis=100, perdas=100, base_perdas=1000
        )

        self.assertEqual(eo, Decimal("86.0"))

    def test_eficiencia_de_estoques_e_giro_e_passa_de_cem(self):
        """O proprio exemplo do 12.6 mostra EE de 102 a 110: nao ha teto."""
        self.assertEqual(
            eficiencia_estoques(custo_das_vendas=5000, estoque_medio=2500), Decimal("200")
        )

    def test_desempenho_financeiro(self):
        # IL=20, IR=5, IE=200 -> 0,4x20 + 0,3x5 + 0,3x200
        df = desempenho_financeiro(
            lucro=200, receita=1000, ativos_medios=4000, custo_das_vendas=5000, estoque_medio=2500
        )

        self.assertEqual(df, Decimal("69.5"))

    def test_satisfacao_da_demanda(self):
        # 0,6x0,6 + 0,5x0,4
        sd = satisfacao_demanda(
            vendidos=60, demanda_potencial=100, pracas_atendidas=2, pracas_ativas=4
        )

        self.assertEqual(sd, Decimal("56.0"))

    def test_satisfacao_da_demanda_nao_passa_de_cem(self):
        """Vender acima da demanda prevista nao vira credito extra."""
        sd = satisfacao_demanda(
            vendidos=500, demanda_potencial=100, pracas_atendidas=4, pracas_ativas=4
        )

        self.assertEqual(sd, Decimal("100"))

    def test_sustentabilidade(self):
        # 0,9x0,5 + (1-0,25)x0,3 + 0,5x0,2
        ds = sustentabilidade(
            perdas=100,
            base_perdas=1000,
            distancia_media_compras=50,
            distancia_maxima=200,
            enviados_regionais=30,
            enviados_total=60,
        )

        self.assertEqual(ds, Decimal("77.5"))

    def test_pontuacao_total(self):
        eixos = {
            "EO": Decimal("86"),
            "DF": Decimal("69.5"),
            "EE": Decimal("200"),
            "SD": Decimal("56"),
            "DS": Decimal("77.5"),
        }

        self.assertEqual(pontuacao_total(eixos), Decimal("92.125"))

    def test_rodada_sem_atividade_nao_divide_por_zero(self):
        zerado = dict.fromkeys(
            (
                "produzido",
                "planejado",
                "vendidos",
                "disponiveis",
                "perdas",
                "base_perdas",
                "lucro",
                "receita",
                "ativos_medios",
                "custo_das_vendas",
                "estoque_medio",
                "estoque_medio_operacional",
                "demanda_potencial",
                "pracas_atendidas",
                "pracas_ativas",
                "distancia_media_compras",
                "distancia_maxima",
                "enviados_regionais",
                "enviados_total",
            ),
            0,
        )

        eixos = calcular_eixos(zerado)

        # sem perdas registradas o aproveitamento e integral: EO e DS nao zeram
        self.assertEqual(eixos["EO"], Decimal("20.0"))
        self.assertEqual(eixos["DS"], Decimal("80.0"))
        self.assertEqual(eixos["EE"], Decimal("0"))


class DesempateTest(TestCase):
    """12.5: EO, depois SD, DS, receita bruta e ordem alfabetica."""

    def _linha(self, nome, **kwargs):
        base = {
            "nome": nome,
            "pontuacao": Decimal("70"),
            "EO": Decimal("80"),
            "SD": Decimal("80"),
            "DS": Decimal("80"),
            "receita": Decimal("1000"),
        }
        base.update(kwargs)
        return base

    def _ordem(self, linhas):
        return [linha["nome"] for linha in ordenar_classificacao(linhas)]

    def test_pontuacao_vem_primeiro(self):
        linhas = [self._linha("A", pontuacao=Decimal("70")), self._linha("B", pontuacao=Decimal("71"))]

        self.assertEqual(self._ordem(linhas), ["B", "A"])

    def test_empate_na_pontuacao_desempata_por_eo(self):
        linhas = [self._linha("A", EO=Decimal("70")), self._linha("B", EO=Decimal("90"))]

        self.assertEqual(self._ordem(linhas), ["B", "A"])

    def test_empate_em_eo_desempata_por_sd(self):
        linhas = [self._linha("A", SD=Decimal("70")), self._linha("B", SD=Decimal("90"))]

        self.assertEqual(self._ordem(linhas), ["B", "A"])

    def test_empate_em_sd_desempata_por_ds(self):
        linhas = [self._linha("A", DS=Decimal("70")), self._linha("B", DS=Decimal("90"))]

        self.assertEqual(self._ordem(linhas), ["B", "A"])

    def test_empate_em_ds_desempata_por_receita(self):
        linhas = [self._linha("A", receita=Decimal("900")), self._linha("B", receita=Decimal("1200"))]

        self.assertEqual(self._ordem(linhas), ["B", "A"])

    def test_empate_total_cai_na_ordem_alfabetica(self):
        linhas = [self._linha("Zeta"), self._linha("Alfa")]

        self.assertEqual(self._ordem(linhas), ["Alfa", "Zeta"])


class FechamentoGravaOsCincoEixosTest(TestCase):
    """Sustentabilidade nao era calculada em lugar nenhum antes disto."""

    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100000"))
        mp = MateriaPrima.objects.create(codigo="MP1", nome="MP1", preco_unitario=Decimal("2"))
        self.produto = Produto.objects.create(codigo="A", nome="Produto A", tempo_producao_min=1)
        ComposicaoProduto.objects.create(
            produto=self.produto, materia_prima=mp, quantidade_por_unidade=Decimal("10")
        )
        self.cidade = Cidade.objects.create(nome="Caico", distancia_km=100, demanda=200)
        Cidade.objects.create(nome="Natal", distancia_km=172, demanda=1550)
        self.rodada = Rodada.objects.create(
            numero=1, fim=timezone.now() - timedelta(minutes=1)
        )
        Decisao.objects.create(grupo=self.grupo, rodada=1, descricao="ok", quantidade=0)
        Producao.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            rodada=1,
            quantidade_planejada=100,
            quantidade_produzida=100,
        )
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.produto, rodada_entrada=1, quantidade=50
        )
        Distribuicao.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            cidade=self.cidade,
            rodada=1,
            quantidade=100,
            preco_unitario=Decimal("40"),
            custo_transporte=Decimal("0"),
        )

    def test_consolidado_traz_os_cinco_eixos(self):
        call_command("fechar_rodadas")

        consolidado = self.grupo.consolidados_rodada.get(rodada=1)
        # producao 100/100 e venda integral: EO alto
        self.assertGreater(consolidado.eo_percent, Decimal("90"))
        self.assertGreater(consolidado.sd_percent, Decimal("0"))
        self.assertGreater(consolidado.ds_percent, Decimal("0"))
        self.assertGreater(consolidado.eficiencia_estoque_percent, Decimal("0"))
        self.assertGreater(consolidado.valor_estoques, Decimal("0"))

    def test_pontuacao_e_a_soma_ponderada_dos_eixos_gravados(self):
        call_command("fechar_rodadas")

        c = self.grupo.consolidados_rodada.get(rodada=1)
        esperado = pontuacao_total(
            {
                "EO": c.eo_percent,
                "DF": c.df_percent,
                "EE": c.eficiencia_estoque_percent,
                "SD": c.sd_percent,
                "DS": c.ds_percent,
            }
        )

        self.assertAlmostEqual(c.score_multicriterio, esperado, places=1)

    def test_estoque_medio_usa_o_valor_da_rodada_anterior(self):
        call_command("fechar_rodadas")
        Rodada.objects.create(numero=2, fim=timezone.now() - timedelta(minutes=1))
        Decisao.objects.create(grupo=self.grupo, rodada=2, descricao="ok", quantidade=0)

        call_command("fechar_rodadas")

        anterior = self.grupo.consolidados_rodada.get(rodada=1)
        self.assertGreater(anterior.valor_estoques, Decimal("0"))


class EstoqueFinanceiroEOperacionalTest(TestCase):
    """12.3.2 e 12.3.3 pedem denominadores diferentes.

    O IE que vive dentro do DF e a "Eficiencia de Estoques (financeira)" e
    olha o ativo de estoque inteiro. O EE do 12.3.3 mede "eficiencia
    logistica operacional" sobre o "Estoque Medio Operacional". Enquanto os
    dois recebiam o mesmo estoque medio, o EE era um clone do IE e o giro
    pesava duas vezes na nota.
    """

    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Estoque", capital=Decimal("100000"))
        self.materia_prima = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("10")
        )
        # custo_unitario_estimado e derivado da composicao: 2 kg x R$ 10 = R$ 20
        self.produto = Produto.objects.create(codigo="A", nome="Produto A")
        ComposicaoProduto.objects.create(
            produto=self.produto,
            materia_prima=self.materia_prima,
            quantidade_por_unidade=2,
        )

    def test_valor_dos_estoques_separa_materia_prima_do_acabado(self):
        EstoqueMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=self.materia_prima, quantidade_kg=Decimal("30")
        )
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.produto, rodada_entrada=1, quantidade=10
        )

        total, operacional = valor_dos_estoques(self.grupo)

        self.assertEqual(total, Decimal("500"))  # 30x10 de MP + 10x20 de acabado
        self.assertEqual(operacional, Decimal("200"))

    def test_ee_usa_o_estoque_operacional_e_ie_o_total(self):
        insumos = {
            "produzido": 0, "planejado": 0, "vendidos": 0, "disponiveis": 0,
            "perdas": 0, "base_perdas": 0, "lucro": 0, "receita": 0,
            "ativos_medios": 0, "demanda_potencial": 0, "pracas_atendidas": 0,
            "pracas_ativas": 0, "distancia_media_compras": 0, "distancia_maxima": 0,
            "enviados_regionais": 0, "enviados_total": 0,
            "custo_das_vendas": Decimal("1000"),
            "estoque_medio": Decimal("1000"),          # total: MP + acabado
            "estoque_medio_operacional": Decimal("250"),  # so o acabado
        }

        eixos = calcular_eixos(insumos)

        # EE gira sobre 250: 1000/250 = 400%
        self.assertEqual(eixos["EE"], Decimal("400"))
        # o IE dentro do DF gira sobre 1000 (100%) e entra com peso W3 = 0,3
        self.assertEqual(eixos["DF"], Decimal("30.0"))

    def test_estoque_medio_operacional_usa_a_rodada_anterior(self):
        """12.3.3: "(Estoque Inicial + Estoque Final) / 2"."""
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.produto, rodada_entrada=1, quantidade=10
        )

        insumos = coletar_insumos(
            grupo=self.grupo, rodada=1, perdas=0, lucro=0, receita=0, saldo_caixa=0,
            valor_estoques_anterior=Decimal("600"),
            valor_operacional_anterior=Decimal("400"),
        )

        self.assertEqual(insumos["valor_estoques_operacional"], Decimal("200"))
        self.assertEqual(insumos["estoque_medio_operacional"], Decimal("300"))
        self.assertEqual(insumos["estoque_medio"], Decimal("400"))
