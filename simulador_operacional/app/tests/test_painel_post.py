"""Caminhos de erro de PainelGrupoView.post -- ORION-C-24.

O post tem cinco ramos (compra de materia-prima, producao, envio,
investimento, decisao) e cada um deles barra a operacao por um motivo
diferente antes de mexer no capital ou no estoque do grupo. Os testes de
fluxo feliz de cada ramo ja existem em test_views.py, test_regras_investimento.py
e test_frete_distribuicao.py; o que falta e provar que o bloqueio realmente
bloqueia -- sem isso, um refactor pode remover o "if" da validacao e nenhum
teste percebe, porque o caminho feliz continua passando.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    AplicacaoFinanceiraGrupo,
    Cidade,
    CompraMateriaPrima,
    ComposicaoProduto,
    Distribuicao,
    EstoqueMateriaPrima,
    EstoqueProduto,
    Grupo,
    Investimento,
    MateriaPrima,
    Produto,
    Producao,
    Rodada,
)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class PainelPostErrosTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.ceo = User.objects.create_user(
            email_usuario="ceo-erros@example.com",
            nome_usuario="CEO Erros",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Erros", capital=Decimal("1000000"))
        self.grupo.membros.add(self.ceo)
        # 7.1: Fortaleza fornece MP1; MP2 vem de Recife ou Porto Alegre --
        # usado no teste de fornecedor invalido.
        self.cidade = Cidade.objects.create(nome="Fortaleza", distancia_km=527, demanda=6000)
        self.mp1 = MateriaPrima.objects.create(codigo="MP1", nome="MP1", preco_unitario=Decimal("3"))
        self.mp2 = MateriaPrima.objects.create(codigo="MP2", nome="MP2", preco_unitario=Decimal("5.5"))
        self.produto = Produto.objects.create(codigo="A", nome="Produto A", ativo=True)
        ComposicaoProduto.objects.create(
            produto=self.produto,
            materia_prima=self.mp1,
            quantidade_por_unidade=2,
        )
        ComposicaoProduto.objects.create(
            produto=self.produto,
            materia_prima=self.mp2,
            quantidade_por_unidade=1,
        )
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.client.login(username="ceo-erros@example.com", password="pass")

    def test_compra_mp_barrada_por_fornecedor_invalido(self):
        """MP2 nao e fornecida por Fortaleza: a compra nao pode ser aceita la."""
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_compra_mp": "1",
                "materia_prima": self.mp2.id,
                "cidade_fornecedora": self.cidade.id,
                "quantidade_kg": "10",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Cidade fornecedora invalida", response.content.decode())
        self.assertFalse(CompraMateriaPrima.objects.filter(grupo=self.grupo).exists())

    def test_compra_mp_barrada_por_capital_insuficiente(self):
        self.grupo.capital = Decimal("0")
        self.grupo.save(update_fields=["capital"])

        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_compra_mp": "1",
                "materia_prima": self.mp1.id,
                "cidade_fornecedora": self.cidade.id,
                "quantidade_kg": "10",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Capital insuficiente para compra de materia-prima", response.content.decode())
        self.assertFalse(CompraMateriaPrima.objects.filter(grupo=self.grupo).exists())

    # test_producao_barrada_por_capital_insuficiente saiu em 2026-09-24.
    # A producao deixou de ser executada na submissao (11.3.b poe "Producao"
    # entre as acoes do FECHAMENTO), entao nao ha debito de caixa no POST
    # para barrar. E nenhuma secao da especificacao condiciona produzir a ter
    # caixa: o 13.9 so diz que o custo e o valor da MP consumida, e o RN-09
    # pressupoe que o caixa pode ficar negativo -- ele restringe investir,
    # nao produzir.

    def test_envio_acima_do_estoque_avisa_e_registra_a_ordem(self):
        EstoqueProduto.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            rodada_entrada=1,
            quantidade=5,
        )
        self.grupo.estoque = 5
        self.grupo.save(update_fields=["estoque"])

        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_envio": "1",
                "produto": self.produto.id,
                "cidade": self.cidade.id,
                "quantidade": 10,
                "preco_unitario": "10",
            },
            follow=True,
        )

        # RN-05: quantidade acima do limite e "automaticamente ajustada pelo
        # sistema, com alerta ao CEO". A ordem fica registrada e o fechamento
        # expede o que houver -- pode ser que a producao desta rodada cubra.
        self.assertEqual(response.status_code, 200)
        self.assertIn("5 un de Produto A em estoque", response.content.decode())
        self.assertTrue(Distribuicao.objects.filter(grupo=self.grupo).exists())

    def test_investimento_operacional_barrado_por_capital_insuficiente(self):
        """Categoria fora de 'financeiro' cai no desconto de capital generico."""
        self.grupo.capital = Decimal("0")
        self.grupo.save(update_fields=["capital"])

        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_investimento": "1",
                "categoria": "marketing",
                "cidade": self.cidade.id,
                "valor": "5000",
                "quantidade": "1",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Capital insuficiente para registrar investimento", response.content.decode())
        self.assertFalse(Investimento.objects.filter(grupo=self.grupo).exists())

    def test_investimento_financeiro_aplicar_barrado_por_capital_insuficiente(self):
        self.grupo.capital = Decimal("0")
        self.grupo.save(update_fields=["capital"])

        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_investimento": "1",
                "categoria": "financeiro",
                "operacao_financeira": "aplicar",
                "valor": "5000",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Capital insuficiente para aplicacao financeira", response.content.decode())
        self.assertFalse(Investimento.objects.filter(grupo=self.grupo).exists())

    def test_investimento_financeiro_resgatar_barrado_por_saldo_insuficiente(self):
        AplicacaoFinanceiraGrupo.objects.create(grupo=self.grupo, saldo_aplicado=Decimal("100"))

        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_investimento": "1",
                "categoria": "financeiro",
                "operacao_financeira": "resgatar",
                "valor": "5000",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Saldo aplicado insuficiente para resgate", response.content.decode())
        self.assertFalse(Investimento.objects.filter(grupo=self.grupo).exists())
