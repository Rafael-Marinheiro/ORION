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
        # 6.2: entrou na rodada 3 e nao foi enviado -> morre no fechamento
        # da propria rodada 3.
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=3, quantidade=300
        )

        self.assertEqual(len(lotes_a_vencer(self.grupo, 3)), 1)

    def test_validade_maior_sobrevive_ao_proprio_fechamento(self):
        """`validade_rodadas` conta a propria rodada de producao: 2 da ao
        lote a rodada de entrada mais a seguinte."""
        duradouro = Produto.objects.create(
            codigo="D", nome="Produto D", perecivel=True, validade_rodadas=2,
            tempo_producao_min=1,
        )
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=duradouro, rodada_entrada=4, quantidade=300
        )

        self.assertEqual(lotes_a_vencer(self.grupo, 4), [])
        self.assertEqual(len(lotes_a_vencer(self.grupo, 5)), 1)

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

        resumo = resumo_vencimento(self.grupo, 3)

        self.assertEqual(resumo["quantidade"], 200)
        self.assertEqual(resumo["produtos"], ["B"])

    def test_sem_rodada_ativa_nao_quebra(self):
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.b, rodada_entrada=1, quantidade=50
        )

        self.assertIsNone(resumo_vencimento(self.grupo, None))
        self.assertIsNone(resumo_vencimento(None, 4))


class CriterioIgualAoFechamentoTest(TestCase):
    """O aviso tem que prever exatamente o que o fechamento descarta.

    A condicao vivia duplicada nos dois lugares; hoje ha uma so, em
    `lote_vencido`. Comparar a lista prevista com os lotes que o fechamento
    de fato zerou continua valendo -- e o que prova que a tela nao mente.
    """

    def test_o_aviso_prediz_exatamente_os_lotes_que_o_fechamento_zera(self):
        from app.management.commands.fechar_rodadas import Command

        grupo = Grupo.objects.create(nome="Equipe Rigel", capital=Decimal("1000"))
        b = Produto.objects.create(
            codigo="B", nome="Produto B", perecivel=True, validade_rodadas=1,
            tempo_producao_min=4,
        )
        for entrada in range(1, 5):
            EstoqueProduto.objects.create(
                grupo=grupo, produto=b, rodada_entrada=entrada, quantidade=10
            )

        avisados = {lote.id for lote in lotes_a_vencer(grupo, 3)}

        Command().processar_perecibilidade(grupo, 3)

        zerados = {
            lote.id
            for lote in EstoqueProduto.objects.filter(grupo=grupo, quantidade=0)
        }
        self.assertEqual(avisados, zerados)
        self.assertTrue(avisados, "o cenario precisa ter algo a vencer")
