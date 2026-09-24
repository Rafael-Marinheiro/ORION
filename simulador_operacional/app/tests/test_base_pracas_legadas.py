"""A base do 9.1 substitui a anterior -- nao convive com ela.

`seed_dados_base` usava `update_or_create`, que so acrescenta. Quem ja
tinha rodado a versao regional ficava com as dez pracas do 9.1 MAIS as
nove antigas: "Joao Pessoa" duplicando "Joao Pessoa" com outra distancia,
e Currais Novos a 0 km -- frete zero, que anula o 9.2a e domina a
estrategia de quem descobrir.

Praca sem movimento e apagada. Praca com movimento sai de jogo por
demanda zero: apagar levaria junto o historico de envios das turmas
passadas, porque `Distribuicao.cidade` e CASCADE.
"""

from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from app.forms import CompraMateriaPrimaForm, DistribuicaoForm
from app.models import (
    Cidade,
    DemandaCidadeProduto,
    Distribuicao,
    Grupo,
    Produto,
)

PRACAS_DO_91 = {
    "São Paulo", "Rio de Janeiro", "Recife", "João Pessoa", "Aracaju",
    "Fortaleza", "Goiânia", "Belém", "Maceió", "Porto Alegre",
}


@override_settings(MIGRATION_MODULES={"app": None})
class AposentadoriaDePracasLegadasTest(TestCase):
    def setUp(self):
        # O estado de quem rodou a versao regional: pracas antigas ja no
        # banco ANTES do seed do 9.1 chegar.
        self.sem_historico = Cidade.objects.create(
            nome="Currais Novos", distancia_km=0, demanda=100
        )
        self.com_historico = Cidade.objects.create(
            nome="Caico", distancia_km=88, demanda=150
        )

    def _semear(self):
        call_command("seed_dados_base", stdout=StringIO())

    def _dar_historico(self, cidade):
        """Um envio de turma passada, que nao pode ser perdido."""
        produto = Produto.objects.create(
            codigo="X", nome="Produto legado", tempo_producao_min=1
        )
        DemandaCidadeProduto.objects.create(
            cidade=cidade, produto=produto, demanda_maxima=150
        )
        grupo = Grupo.objects.create(nome="Equipe de 2025", capital=Decimal("1000"))
        return Distribuicao.objects.create(
            grupo=grupo, produto=produto, cidade=cidade, rodada=1,
            quantidade=10, preco_unitario=Decimal("100"),
            custo_transporte=Decimal("0"),
        )

    def test_praca_fora_do_91_sem_movimento_e_apagada(self):
        self._semear()

        self.assertFalse(Cidade.objects.filter(nome="Currais Novos").exists())

    def test_praca_com_historico_sobrevive_com_demanda_zero(self):
        envio = self._dar_historico(self.com_historico)

        self._semear()

        self.com_historico.refresh_from_db()
        self.assertEqual(self.com_historico.demanda, 0)
        self.assertTrue(Distribuicao.objects.filter(pk=envio.pk).exists())

    def test_demanda_por_produto_da_praca_aposentada_tambem_zera(self):
        """O fechamento le DemandaCidadeProduto antes de Cidade.demanda."""
        self._dar_historico(self.com_historico)

        self._semear()

        self.assertEqual(
            DemandaCidadeProduto.objects.filter(cidade=self.com_historico)
            .values_list("demanda_maxima", flat=True)
            .first(),
            0,
        )

    def test_sobram_as_dez_pracas_do_91_mais_as_que_guardam_historico(self):
        self._dar_historico(self.com_historico)

        self._semear()

        self.assertEqual(
            set(Cidade.objects.values_list("nome", flat=True)),
            PRACAS_DO_91 | {"Caico"},
        )

    def test_base_limpa_fica_so_com_as_dez(self):
        self._semear()

        self.assertEqual(set(Cidade.objects.values_list("nome", flat=True)), PRACAS_DO_91)

    def test_praca_cadastrada_pelo_professor_nao_e_varrida(self):
        """A lista de remocao e nomeada: so a base regional sai. Praca
        propria do professor sobrevive, mesmo sem movimento nenhum."""
        propria = Cidade.objects.create(
            nome="Praça personalizada", distancia_km=10, demanda=20
        )

        self._semear()

        self.assertTrue(Cidade.objects.filter(pk=propria.pk).exists())

    def test_praca_aposentada_sai_dos_formularios(self):
        self._dar_historico(self.com_historico)

        self._semear()

        destinos = DistribuicaoForm().fields["cidade"].queryset
        fornecedores = CompraMateriaPrimaForm().fields["cidade_fornecedora"].queryset

        self.assertNotIn(self.com_historico, destinos)
        self.assertNotIn(self.com_historico, fornecedores)
        self.assertEqual(destinos.count(), 10)

    def test_semear_duas_vezes_nao_muda_nada(self):
        self._semear()
        antes = sorted(Cidade.objects.values_list("nome", "demanda"))

        self._semear()

        self.assertEqual(sorted(Cidade.objects.values_list("nome", "demanda")), antes)
