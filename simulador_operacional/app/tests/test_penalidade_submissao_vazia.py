# -*- coding: utf-8 -*-
"""11.2 -- a multa e por decisao nao informada, nao por botao nao clicado.

O 11.2 se chama "Tratamento de Decisoes Nao Informadas" e dispara "caso o
grupo nao tenha submetido SUAS DECISOES ate o prazo-limite". Ate 14/10/2026
a multa olhava apenas a existencia da linha de submissao: quem clicava em
"Enviar submissao" sem registrar nada recebia o tratamento do 11.2 --
repeticao automatica dos valores da rodada anterior -- SEM a multa que o
11.2 impoe junto. O botao sozinho anulava a penalidade.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from app.models import (
    Cidade,
    CompraMateriaPrima,
    ConsolidadoRodadaGrupo,
    Decisao,
    GameConfig,
    Grupo,
    Investimento,
    Jogo,
    MateriaPrima,
    Producao,
    Produto,
    Rodada,
)
from app.services.penalidade_service import registrou_decisao


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RegistrouDecisaoTest(TestCase):
    """As quatro variaveis decisorias que o 11.2 lista."""

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=3)
        )
        self.grupo = Grupo.objects.create(
            nome="Equipe Vega", jogo=self.jogo, capital=Decimal("1000000")
        )
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2
        )
        self.mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("3")
        )
        self.cidade = Cidade.objects.create(
            nome="Recife", distancia_km=290, demanda=4000
        )

    def test_rodada_sem_nada_registrado(self):
        self.assertFalse(registrou_decisao(self.grupo, 1))

    def test_compra_conta_como_decisao(self):
        CompraMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=self.mp,
            cidade_fornecedora=self.cidade, rodada_pedido=1,
            rodada_recebimento=2, quantidade_kg=Decimal("100"),
            preco_unitario=Decimal("3"), custo_logistico=Decimal("0"),
            valor_total=Decimal("300"),
        )

        self.assertTrue(registrou_decisao(self.grupo, 1))

    def test_producao_conta_como_decisao(self):
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1,
            quantidade_planejada=10,
        )

        self.assertTrue(registrou_decisao(self.grupo, 1))

    def test_investimento_conta_como_decisao(self):
        Investimento.objects.create(
            grupo=self.grupo, rodada=1, valor=Decimal("1000")
        )

        self.assertTrue(registrou_decisao(self.grupo, 1))

    def test_decisao_de_outra_rodada_nao_vale_para_esta(self):
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1,
            quantidade_planejada=10,
        )

        self.assertFalse(registrou_decisao(self.grupo, 2))


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class MultaPorSubmissaoVaziaTest(TestCase):
    def setUp(self):
        call_command("seed_dados_base")
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=3)
        )
        self.produto = Produto.objects.get(codigo="A")

    def _grupo(self, nome):
        return Grupo.objects.create(
            nome=nome, jogo=self.jogo, capital=Decimal("1000000"),
            maquinas=40, maquinas_a=15, maquinas_b=15, maquinas_c=10,
            trabalhadores=80,
        )

    def _fechar(self, numero):
        Rodada.objects.create(
            jogo=self.jogo, numero=numero,
            fim=timezone.now() - timedelta(seconds=1),
        )
        call_command("fechar_rodadas")

    def _penalidade(self, grupo, rodada):
        consolidado = ConsolidadoRodadaGrupo.objects.get(
            grupo=grupo, rodada=rodada
        )
        return consolidado.penalidade_sem_submissao

    def test_quem_nao_submete_e_multado(self):
        grupo = self._grupo("Equipe Ausente")

        self._fechar(1)

        self.assertGreater(self._penalidade(grupo, 1), 0)

    def test_quem_submete_vazio_tambem_e_multado(self):
        """O botao sozinho nao anula a penalidade."""
        grupo = self._grupo("Equipe do Botao")
        Decisao.objects.create(
            grupo=grupo, rodada=1, descricao="Decisões da rodada 1"
        )

        self._fechar(1)

        self.assertGreater(self._penalidade(grupo, 1), 0)

    def test_quem_submete_com_decisao_nao_e_multado(self):
        grupo = self._grupo("Equipe Ativa")
        Decisao.objects.create(
            grupo=grupo, rodada=1, descricao="Decisões da rodada 1"
        )
        Producao.objects.create(
            grupo=grupo, produto=self.produto, rodada=1,
            quantidade_planejada=5,
        )

        self._fechar(1)

        self.assertEqual(self._penalidade(grupo, 1), 0)

    def test_decidir_sem_submeter_continua_sendo_multado(self):
        """11.2 exige as duas coisas: decidir E submeter no prazo."""
        grupo = self._grupo("Equipe que esqueceu de enviar")
        Producao.objects.create(
            grupo=grupo, produto=self.produto, rodada=1,
            quantidade_planejada=5,
        )

        self._fechar(1)

        self.assertGreater(self._penalidade(grupo, 1), 0)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class IndicadorUsaAMesmaRegraTest(TestCase):
    """O indicador do 15.4.c e a multa do 11.2 nao podem divergir.

    Duas definicoes do que e "decidir" discordam na primeira mudanca, e o
    professor veria o relatorio contradizer a penalidade aplicada.
    """

    def test_consistencia_bate_com_o_criterio_da_multa(self):
        from app.services.avaliacao import indicadores_de_uso

        jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=2)
        )
        produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2
        )
        for numero in (1, 2):
            Rodada.objects.create(
                jogo=jogo, numero=numero,
                fim=timezone.now() - timedelta(hours=1), fechada=True,
            )
        grupo = Grupo.objects.create(nome="Equipe do Botao", jogo=jogo)
        # submeteu as duas, decidiu em uma
        for numero in (1, 2):
            Decisao.objects.create(
                grupo=grupo, rodada=numero, descricao=f"Rodada {numero}"
            )
        Producao.objects.create(
            grupo=grupo, produto=produto, rodada=1, quantidade_planejada=5
        )

        linha = indicadores_de_uso(jogo)["participacao"][0]

        self.assertEqual(linha["participacao_percent"], 100.0)
        self.assertEqual(linha["consistencia_percent"], 50.0)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class QuantidadeZeroNaoEDecisaoTest(TestCase):
    """Registrar zero seria a forma trivial de burlar a multa.

    Uma ordem de producao de 0 unidade, ou uma compra de 0 kg, custa nada e
    criaria a linha. O 11.2 fala em variaveis decisorias INFORMADAS, e
    informar zero e o mesmo que nao informar.
    """

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=3)
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2
        )

    def test_producao_zero_nao_conta(self):
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1,
            quantidade_planejada=0,
        )

        self.assertFalse(registrou_decisao(self.grupo, 1))

    def test_investimento_zero_nao_conta(self):
        Investimento.objects.create(
            grupo=self.grupo, rodada=1, valor=Decimal("0")
        )

        self.assertFalse(registrou_decisao(self.grupo, 1))

    def test_producao_de_uma_unidade_ja_conta(self):
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1,
            quantidade_planejada=1,
        )

        self.assertTrue(registrou_decisao(self.grupo, 1))
