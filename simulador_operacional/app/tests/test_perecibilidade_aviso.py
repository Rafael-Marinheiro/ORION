"""O aviso de vencimento tem que usar o mesmo criterio do fechamento.

Se os dois divergirem, o aluno recebe aviso de perda que nao acontece, ou
perde lote sem ter sido avisado -- os dois casos destroem a confianca na
simulacao.
"""

from decimal import Decimal

from django.test import TestCase

from app.models import EstoqueProduto, Grupo, Produto
from app.services.perecibilidade import lotes_a_vencer, resumo_vencimento


class AvisoDeVencimentoTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000"))
        # 6.2: B e o unico perecivel, com validade de 1 rodada
        self.b = Produto.objects.create(
            codigo="B", nome="Produto B", perecivel=True, validade_rodadas=1,
            tempo_producao_min=4,
        )
        self.a = Produto.objects.create(
            codigo="A", nome="Produto A", perecivel=False, validade_rodadas=0,
            tempo_producao_min=2,
        )

    def test_lote_que_vence_no_fechamento_desta_rodada_e_avisado(self):
        # entrou na rodada 3, validade 1 -> morre no fechamento da rodada 4
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=3, quantidade=300
        )

        self.assertEqual(len(lotes_a_vencer(self.grupo, 4)), 1)

    def test_lote_ainda_dentro_da_validade_nao_e_avisado(self):
        # entrou na rodada 4, validade 1 -> so morre no fechamento da rodada 5
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=4, quantidade=300
        )

        self.assertEqual(lotes_a_vencer(self.grupo, 4), [])

    def test_produto_nao_perecivel_nunca_entra_no_aviso(self):
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.a, rodada_entrada=1, quantidade=500
        )

        self.assertEqual(lotes_a_vencer(self.grupo, 9), [])

    def test_lote_zerado_nao_gera_aviso(self):
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=1, quantidade=0
        )

        self.assertIsNone(resumo_vencimento(self.grupo, 5))

    def test_resumo_soma_quantidade_e_lista_produtos(self):
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=2, quantidade=120
        )
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=3, quantidade=80
        )

        resumo = resumo_vencimento(self.grupo, 4)

        self.assertEqual(resumo["quantidade"], 200)
        self.assertEqual(resumo["produtos"], ["B"])

    def test_sem_rodada_ativa_nao_quebra(self):
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=1, quantidade=50
        )

        self.assertIsNone(resumo_vencimento(self.grupo, None))
        self.assertIsNone(resumo_vencimento(None, 4))


class CriterioIgualAoFechamentoTest(TestCase):
    """A condicao do aviso e a mesma do descarte, lote a lote."""

    def test_aviso_e_descarte_concordam_em_varias_rodadas(self):
        grupo = Grupo.objects.create(nome="Equipe Rigel", capital=Decimal("1000"))
        b = Produto.objects.create(
            codigo="B", nome="Produto B", perecivel=True, validade_rodadas=1,
            tempo_producao_min=4,
        )

        for entrada in range(1, 5):
            EstoqueProduto.objects.create(
                grupo=grupo, produto=b, rodada_entrada=entrada, quantidade=10
            )

        for rodada in range(1, 7):
            avisados = {lote.rodada_entrada for lote in lotes_a_vencer(grupo, rodada)}
            # mesma condicao de fechar_rodadas.processar_perecibilidade
            esperado = {
                lote.rodada_entrada
                for lote in EstoqueProduto.objects.filter(
                    grupo=grupo, produto__perecivel=True, quantidade__gt=0
                )
                if rodada >= lote.rodada_entrada + (lote.produto.validade_rodadas or 1)
            }
            self.assertEqual(avisados, esperado, "divergiu na rodada {}".format(rodada))
