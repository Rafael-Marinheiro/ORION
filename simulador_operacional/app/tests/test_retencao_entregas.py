"""Retencao de entregas por evento -- 8.4.

O codigo tratava "X% das entregas sao retidas para a proxima rodada" como
queda de demanda na cidade: a carga chegava, o mercado e que comprava menos,
e na rodada seguinte nao voltava nada. Dois erros de uma vez -- a carga nao
ficava retida e o perecivel nao se perdia.
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
    Evento,
    EventoRodada,
    Grupo,
    MateriaPrima,
    Produto,
    Rodada,
)
from app.services.retencao import aplicar_retencao_de_entregas


class SeedDaGreveTest(TestCase):
    """A greve do 8.4 tem DOIS efeitos; o codigo so aplicava um."""

    def setUp(self):
        call_command("seed_dados_base")

    def test_greve_encarece_e_retem(self):
        greve = Evento.objects.get(nome="Greve de caminhoneiros")

        self.assertEqual(greve.impacto_percentual, 30)
        self.assertEqual(greve.retencao_entregas_percent, 30)

    def test_enchentes_so_retem(self):
        enchentes = Evento.objects.get(nome="Enchentes nas regiões")

        self.assertEqual(enchentes.retencao_entregas_percent, 20)
        self.assertEqual(enchentes.impacto_percentual, 0)

    def test_eventos_sem_efeito_logistico_nao_retem(self):
        sem_retencao = Evento.objects.exclude(
            nome__in=["Greve de caminhoneiros", "Enchentes nas regiões"]
        )

        for evento in sem_retencao:
            self.assertEqual(evento.retencao_entregas_percent, 0, evento.nome)


class RetencaoDeEnviosTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100000"))
        mp = MateriaPrima.objects.create(codigo="MP1", nome="MP1", preco_unitario=Decimal("2"))
        self.duravel = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=1, perecivel=False
        )
        self.perecivel = Produto.objects.create(
            codigo="B", nome="Produto B", tempo_producao_min=1, perecivel=True, validade_rodadas=1
        )
        for produto in (self.duravel, self.perecivel):
            ComposicaoProduto.objects.create(
                produto=produto, materia_prima=mp, quantidade_por_unidade=Decimal("10")
            )
        self.cidade = Cidade.objects.create(nome="Caico", distancia_km=100, demanda=500)

    def _envio(self, produto, quantidade):
        return Distribuicao.objects.create(
            grupo=self.grupo,
            produto=produto,
            cidade=self.cidade,
            rodada=1,
            quantidade=quantidade,
            preco_unitario=Decimal("50"),
            custo_transporte=Decimal("300"),
        )

    def test_parcela_retida_sai_da_rodada_corrente(self):
        envio = self._envio(self.duravel, 100)

        aplicar_retencao_de_entregas([envio], 30, rodada_numero=1)

        envio.refresh_from_db()
        self.assertEqual(envio.quantidade, 70)

    def test_parcela_retida_volta_na_rodada_seguinte(self):
        envio = self._envio(self.duravel, 100)

        aplicar_retencao_de_entregas([envio], 30, rodada_numero=1)

        proximo = Distribuicao.objects.get(grupo=self.grupo, rodada=2)
        self.assertEqual(proximo.quantidade, 30)
        self.assertEqual(proximo.produto_id, self.duravel.id)
        self.assertEqual(proximo.cidade_id, self.cidade.id)

    def test_carga_retida_nao_paga_frete_de_novo(self):
        """O caminhao ja saiu: cobrar duas vezes puniria duas vezes."""
        envio = self._envio(self.duravel, 100)

        aplicar_retencao_de_entregas([envio], 30, rodada_numero=1)

        proximo = Distribuicao.objects.get(grupo=self.grupo, rodada=2)
        self.assertEqual(proximo.custo_transporte, Decimal("0"))

    def test_perecivel_retido_e_perdido_nao_reenviado(self):
        """8.4: "Produtos pereciveis sao perdidos"."""
        envio = self._envio(self.perecivel, 100)

        perdas = aplicar_retencao_de_entregas([envio], 30, rodada_numero=1)

        self.assertFalse(Distribuicao.objects.filter(grupo=self.grupo, rodada=2).exists())
        # 30 unidades x 10 kg x R$ 2
        self.assertEqual(perdas[self.grupo.id], Decimal("600"))

    def test_sem_evento_de_retencao_nada_muda(self):
        envio = self._envio(self.duravel, 100)

        perdas = aplicar_retencao_de_entregas([envio], 0, rodada_numero=1)

        envio.refresh_from_db()
        self.assertEqual(envio.quantidade, 100)
        self.assertEqual(perdas, {})
        self.assertFalse(Distribuicao.objects.filter(rodada=2).exists())

    def test_envio_pequeno_demais_nao_some(self):
        """1 unidade com 20% de retencao arredonda para 0: a carga segue."""
        envio = self._envio(self.duravel, 1)

        aplicar_retencao_de_entregas([envio], 20, rodada_numero=1)

        envio.refresh_from_db()
        self.assertEqual(envio.quantidade, 1)


class FechamentoComRetencaoTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100000"))
        mp = MateriaPrima.objects.create(codigo="MP1", nome="MP1", preco_unitario=Decimal("2"))
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=1, perecivel=False
        )
        ComposicaoProduto.objects.create(
            produto=self.produto, materia_prima=mp, quantidade_por_unidade=Decimal("10")
        )
        self.cidade = Cidade.objects.create(nome="Caico", distancia_km=100, demanda=1000)
        Rodada.objects.create(numero=1, fim=timezone.now() - timedelta(minutes=1))
        Decisao.objects.create(grupo=self.grupo, rodada=1, descricao="ok", quantidade=0)
        enchentes = Evento.objects.create(
            nome="Enchentes nas regiões",
            tipo="custo_transporte",
            modo_aplicacao="percentual",
            impacto_percentual=0,
            retencao_entregas_percent=20,
            probabilidade=15,
        )
        EventoRodada.objects.create(rodada=1, jogo=None, evento=enchentes)
        Distribuicao.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            cidade=self.cidade,
            rodada=1,
            quantidade=100,
            preco_unitario=Decimal("50"),
            custo_transporte=Decimal("0"),
        )

    def test_so_a_carga_que_chegou_e_vendida(self):
        """A demanda da cidade comporta tudo; o que limita e a retencao."""
        call_command("fechar_rodadas")

        envio = Distribuicao.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(envio.quantidade, 80)
        self.assertEqual(envio.quantidade_vendida, 80)

    def test_o_retido_fica_esperando_a_rodada_seguinte(self):
        call_command("fechar_rodadas")

        retido = Distribuicao.objects.get(grupo=self.grupo, rodada=2)
        self.assertEqual(retido.quantidade, 20)
        self.assertFalse(retido.processada)
