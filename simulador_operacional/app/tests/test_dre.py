"""DRE e Fluxo de Caixa -- 10.3.

O documento pede os dois na Tela de Relatorios Financeiros; a tela tinha
tabela de consolidado, que e outra coisa: lista os campos, nao demonstra o
resultado. O que estes testes protegem e a propriedade que faz um relatorio
contabil servir de aula: ele fecha.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import ConsolidadoRodadaGrupo, Grupo, Rodada, User
from app.services.dre import (
    conferir_dre,
    montar_dre,
    montar_fluxo_de_caixa,
    resumo_do_fluxo,
)


def _consolidado(grupo, rodada, **campos):
    valores = {
        "receita_vendas": Decimal("10000"),
        "custos_operacionais": Decimal("4000"),
        "penalidade_sem_submissao": Decimal("0"),
        "perda_pereciveis": Decimal("500"),
        "custo_armazenagem_mp": Decimal("200"),
        "custo_armazenagem_produtos": Decimal("300"),
        "custos_totais": Decimal("5000"),
        "lucro_rodada": Decimal("5000"),
        "saldo_caixa": Decimal("50000"),
    }
    valores.update(campos)
    return ConsolidadoRodadaGrupo.objects.create(grupo=grupo, rodada=rodada, **valores)


class DRETest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("50000"))

    def test_deducoes_somadas_a_receita_dao_o_lucro(self):
        consolidado = _consolidado(self.grupo, 1)

        self.assertEqual(conferir_dre(consolidado), Decimal("0"))

    def test_deducoes_aparecem_negativas(self):
        linhas = montar_dre(_consolidado(self.grupo, 1))

        deducoes = [linha for linha in linhas if linha["tipo"] == "deducao"]
        self.assertTrue(deducoes)
        for linha in deducoes:
            self.assertLess(linha["valor"], 0, linha["rotulo"])

    def test_linha_zerada_nao_polui_o_demonstrativo(self):
        """Penalidade zero e a regra, nao a excecao: nao vira linha."""
        linhas = montar_dre(_consolidado(self.grupo, 1, penalidade_sem_submissao=Decimal("0")))

        rotulos = [linha["rotulo"] for linha in linhas]
        self.assertNotIn("Penalidade por não submissão", rotulos)

    def test_penalidade_aplicada_vira_linha(self):
        linhas = montar_dre(
            _consolidado(
                self.grupo,
                1,
                penalidade_sem_submissao=Decimal("1000"),
                custos_totais=Decimal("6000"),
                lucro_rodada=Decimal("4000"),
            )
        )

        rotulos = [linha["rotulo"] for linha in linhas]
        self.assertIn("Penalidade por não submissão", rotulos)

    def test_termina_no_lucro_da_rodada(self):
        consolidado = _consolidado(self.grupo, 1)

        ultima = montar_dre(consolidado)[-1]

        self.assertEqual(ultima["tipo"], "total")
        self.assertEqual(ultima["valor"], consolidado.lucro_rodada)


class FluxoDeCaixaTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("50000"))

    def test_saldo_inicial_e_o_saldo_final_da_rodada_anterior(self):
        _consolidado(self.grupo, 1, saldo_caixa=Decimal("50000"))
        _consolidado(self.grupo, 2, saldo_caixa=Decimal("53000"))

        fluxo = montar_fluxo_de_caixa(self.grupo.consolidados_rodada.all())

        self.assertEqual(fluxo[1]["saldo_inicial"], Decimal("50000"))

    def test_cada_linha_fecha_no_saldo_final(self):
        _consolidado(self.grupo, 1, saldo_caixa=Decimal("50000"))
        _consolidado(self.grupo, 2, saldo_caixa=Decimal("53000"))

        for linha in montar_fluxo_de_caixa(self.grupo.consolidados_rodada.all()):
            fechamento = (
                linha["saldo_inicial"]
                + linha["entradas"]
                - linha["saidas"]
                + linha["outras_movimentacoes"]
            )
            self.assertEqual(fechamento, linha["saldo_final"], f"rodada {linha['rodada']}")

    def test_compra_de_insumo_aparece_como_movimentacao(self):
        """Saiu caixa sem virar custo da rodada: o relatorio nao pode sumir."""
        _consolidado(self.grupo, 1, saldo_caixa=Decimal("50000"))
        # lucro de 5.000 mas o caixa caiu: o grupo comprou materia-prima
        _consolidado(self.grupo, 2, saldo_caixa=Decimal("40000"))

        fluxo = montar_fluxo_de_caixa(self.grupo.consolidados_rodada.all())

        self.assertEqual(fluxo[1]["outras_movimentacoes"], Decimal("-15000"))

    def test_rodadas_fora_de_ordem_nao_embaralham_o_fluxo(self):
        _consolidado(self.grupo, 2, saldo_caixa=Decimal("53000"))
        _consolidado(self.grupo, 1, saldo_caixa=Decimal("50000"))

        fluxo = montar_fluxo_de_caixa(self.grupo.consolidados_rodada.all())

        self.assertEqual([linha["rodada"] for linha in fluxo], [1, 2])

    def test_resumo_traz_o_saldo_da_ultima_rodada(self):
        _consolidado(self.grupo, 1, saldo_caixa=Decimal("50000"))
        _consolidado(self.grupo, 2, saldo_caixa=Decimal("53000"))

        resumo = resumo_do_fluxo(montar_fluxo_de_caixa(self.grupo.consolidados_rodada.all()))

        self.assertEqual(resumo["saldo_final"], Decimal("53000"))
        self.assertEqual(resumo["entradas"], Decimal("20000"))

    def test_sem_rodada_fechada_nao_ha_resumo(self):
        self.assertIsNone(resumo_do_fluxo([]))


class TelaDeRelatoriosTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email_usuario="ceo@teste.com",
            nome_usuario="CEO",
            password="senha123",
            tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("50000"))
        self.grupo.membros.add(self.user)
        Rodada.objects.create(
            numero=1, fim=timezone.now() - timedelta(minutes=1), fechada=True
        )
        _consolidado(self.grupo, 1)
        self.client.force_login(self.user)

    def test_aluno_ve_o_dre_do_proprio_grupo_sem_filtrar(self):
        html = self.client.get(reverse("relatorios")).content.decode()

        self.assertIn("Demonstrativo de resultados", html)
        self.assertIn("Fluxo de caixa por rodada", html)
