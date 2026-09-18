from decimal import Decimal

from django.test import TestCase

from app.models import ConsolidadoRodadaGrupo, Grupo
from app.services.relatorios_dashboard import montar_painel


def consolidado(grupo, rodada, receita, operacionais=0, armaz_mp=0, armaz_prod=0,
                perdas=0, penalidade=0):
    custos = Decimal(operacionais + armaz_mp + armaz_prod + perdas + penalidade)
    return ConsolidadoRodadaGrupo.objects.create(
        grupo=grupo,
        rodada=rodada,
        receita_vendas=Decimal(receita),
        custos_operacionais=Decimal(operacionais),
        custo_armazenagem_mp=Decimal(armaz_mp),
        custo_armazenagem_produtos=Decimal(armaz_prod),
        perda_pereciveis=Decimal(perdas),
        penalidade_sem_submissao=Decimal(penalidade),
        custos_totais=custos,
        lucro_rodada=Decimal(receita) - custos,
    )


class MontarPainelTest(TestCase):
    def setUp(self):
        self.vega = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100"))

    def test_sem_consolidados_sinaliza_ausencia_de_dados(self):
        painel = montar_painel(ConsolidadoRodadaGrupo.objects.none())

        self.assertFalse(painel["tem_dados"])
        self.assertNotIn("kpis", painel)

    def test_series_ficam_em_ordem_crescente_de_rodada(self):
        consolidado(self.vega, 2, 200, operacionais=100)
        consolidado(self.vega, 1, 100, operacionais=50)

        # a view entrega ordenado por -rodada; o painel precisa reordenar
        painel = montar_painel(ConsolidadoRodadaGrupo.objects.order_by("-rodada"))

        trajetoria = painel["graficos"][0]
        self.assertEqual(trajetoria["labels"], ["Rodada 1", "Rodada 2"])
        self.assertEqual(trajetoria["series"][0]["data"], [100.0, 200.0])

    def test_varias_equipes_sao_somadas_por_rodada(self):
        rigel = Grupo.objects.create(nome="Equipe Rigel", capital=Decimal("100"))
        consolidado(self.vega, 1, 100, operacionais=40)
        consolidado(rigel, 1, 300, operacionais=60)

        painel = montar_painel(ConsolidadoRodadaGrupo.objects.all())

        self.assertTrue(painel["multi_grupo"])
        self.assertEqual(painel["kpis"]["receita"], Decimal("400"))
        self.assertEqual(painel["kpis"]["custos"], Decimal("100"))

    def test_composicao_abre_o_custo_por_origem(self):
        consolidado(self.vega, 1, 1000, operacionais=100, armaz_mp=20,
                    armaz_prod=30, perdas=40, penalidade=10)

        painel = montar_painel(ConsolidadoRodadaGrupo.objects.all())

        composicao = painel["graficos"][1]
        self.assertTrue(composicao["stacked"])
        rotulos = [s["label"] for s in composicao["series"]]
        self.assertEqual(
            rotulos,
            ["Operacionais", "Armazenagem de MP", "Armazenagem de produtos",
             "Perda de perecíveis", "Penalidade"],
        )
        self.assertEqual([s["data"][0] for s in composicao["series"]],
                         [100.0, 20.0, 30.0, 40.0, 10.0])
        # a soma das partes tem que bater com o custo total do grafico anterior
        self.assertEqual(sum(s["data"][0] for s in composicao["series"]), 200.0)

    def test_variacao_compara_com_a_rodada_anterior(self):
        consolidado(self.vega, 1, 100, operacionais=50)
        consolidado(self.vega, 2, 150, operacionais=50)

        kpis = montar_painel(ConsolidadoRodadaGrupo.objects.all())["kpis"]

        self.assertEqual(kpis["rodada"], 2)
        self.assertEqual(kpis["rodada_anterior"], 1)
        self.assertEqual(kpis["receita_var"], Decimal("50"))

    def test_primeira_rodada_nao_tem_base_de_comparacao(self):
        consolidado(self.vega, 1, 100, operacionais=50)

        kpis = montar_painel(ConsolidadoRodadaGrupo.objects.all())["kpis"]

        self.assertIsNone(kpis["receita_var"])
        self.assertIsNone(kpis["rodada_anterior"])
        self.assertEqual(kpis["receita_tom"], "mute")

    def test_custo_subindo_e_lido_como_ruim_e_receita_subindo_como_boa(self):
        consolidado(self.vega, 1, 100, operacionais=50)
        consolidado(self.vega, 2, 150, operacionais=80)

        kpis = montar_painel(ConsolidadoRodadaGrupo.objects.all())["kpis"]

        self.assertEqual(kpis["receita_tom"], "ok")
        self.assertEqual(kpis["custos_tom"], "bad")

    def test_custo_caindo_e_lido_como_bom(self):
        consolidado(self.vega, 1, 100, operacionais=80)
        consolidado(self.vega, 2, 100, operacionais=50)

        kpis = montar_painel(ConsolidadoRodadaGrupo.objects.all())["kpis"]

        self.assertEqual(kpis["custos_tom"], "ok")

    def test_margem_e_percentual_do_lucro_sobre_a_receita(self):
        consolidado(self.vega, 1, 200, operacionais=150)

        kpis = montar_painel(ConsolidadoRodadaGrupo.objects.all())["kpis"]

        self.assertEqual(kpis["margem"], Decimal("25"))

    def test_receita_zero_nao_divide_por_zero_na_margem(self):
        consolidado(self.vega, 1, 0, penalidade=30)

        kpis = montar_painel(ConsolidadoRodadaGrupo.objects.all())["kpis"]

        self.assertIsNone(kpis["margem"])
        self.assertIsNone(kpis["margem_var"])

    def test_lucro_acumulado_soma_todas_as_rodadas(self):
        consolidado(self.vega, 1, 100, operacionais=40)
        consolidado(self.vega, 2, 100, operacionais=30)

        kpis = montar_painel(ConsolidadoRodadaGrupo.objects.all())["kpis"]

        self.assertEqual(kpis["lucro_acumulado"], Decimal("130"))

    def test_grafico_de_equipes_so_existe_com_mais_de_uma(self):
        consolidado(self.vega, 1, 100, operacionais=40)

        painel = montar_painel(ConsolidadoRodadaGrupo.objects.all())

        self.assertFalse(painel["multi_grupo"])
        self.assertEqual(len(painel["graficos"]), 2)

    def test_equipes_saem_ordenadas_por_lucro(self):
        rigel = Grupo.objects.create(nome="Equipe Rigel", capital=Decimal("100"))
        consolidado(self.vega, 1, 100, operacionais=90)
        consolidado(rigel, 1, 500, operacionais=100)

        painel = montar_painel(ConsolidadoRodadaGrupo.objects.all())

        grupos = painel["graficos"][2]
        self.assertEqual(grupos["labels"], ["Equipe Rigel", "Equipe Vega"])
        self.assertEqual(grupos["series"][0]["data"], [400.0, 10.0])
