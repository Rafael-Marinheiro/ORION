"""As caracteristicas dos produtos precisam estar em tela -- 6.1, 6.2 e 13.3.

Ate 24/09/2026 a unica mencao a perecibilidade em toda a interface vivia
dentro de um aviso do painel. Sem a informacao em lugar nenhum, a regra do
6.2 deixava de ser conhecimento do negocio e virava pegadinha.

A tabela e lida do banco: o 6.1 avisa que os precos de MP "sao
parametrizaveis e podem variar entre rodadas", entao valor escrito a mao no
template envelhece na primeira alteracao do professor.
"""

from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from app.models import ComposicaoProduto, MateriaPrima, Produto


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class AjudaProdutosTest(TestCase):
    def setUp(self):
        self.mp1 = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("3")
        )
        # 6.1/13.3: B leva 360 kg de MP1 e 4 minutos de maquina.
        self.b = Produto.objects.create(
            codigo="B", nome="Produto B", tempo_producao_min=4,
            perecivel=True, validade_rodadas=1,
        )
        ComposicaoProduto.objects.create(
            produto=self.b, materia_prima=self.mp1,
            quantidade_por_unidade=Decimal("360"),
        )

    def _ajuda(self):
        return self.client.get(reverse("ajuda")).content.decode()

    def test_a_composicao_aparece_na_ajuda(self):
        corpo = self._ajuda()

        self.assertIn("MP1", corpo)
        self.assertIn("360", corpo)

    def test_o_tempo_de_maquina_aparece(self):
        self.assertIn("4 min", self._ajuda())

    def test_o_custo_acompanha_o_preco_vigente_da_materia_prima(self):
        """360 kg x R$ 3,00 = R$ 1.080,00; mudou o preco, muda a tabela."""
        self.assertIn("1.080,00", self._ajuda())

        self.mp1.preco_unitario = Decimal("4")
        self.mp1.save(update_fields=["preco_unitario"])

        self.assertIn("1.440,00", self._ajuda())

    def test_o_perecivel_declara_quando_vence(self):
        """6.2, na redacao ratificada em 24/09/2026."""
        self.assertIn(
            "vence no fechamento da rodada em que foi produzido", self._ajuda()
        )

    def test_o_nao_perecivel_declara_que_pode_ser_estocado(self):
        Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2, perecivel=False
        )

        self.assertIn("pode ser estocado por tempo indefinido", self._ajuda())

    def test_produto_inativo_nao_aparece(self):
        Produto.objects.create(
            codigo="Z", nome="Produto Aposentado", tempo_producao_min=1, ativo=False
        )

        self.assertNotIn("Produto Aposentado", self._ajuda())

    def test_a_ajuda_abre_sem_login(self):
        """O manual e do aluno, e ele pode querer ler antes de entrar."""
        self.assertEqual(self.client.get(reverse("ajuda")).status_code, 200)
