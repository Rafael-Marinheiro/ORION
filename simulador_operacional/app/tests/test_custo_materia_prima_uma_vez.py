"""A materia-prima sai do caixa uma vez so -- 7.2, 7.3 e 7.5.

O 7.2 manda debitar "o custo total [...] imediatamente [...] na rodada da
compra", e o 7.5 enumera as saidas de caixa que a MP gera: "compras,
armazenagem e logistica". Consumo nao esta na lista -- o 7.3 o trata como
movimento de estoque, "automatico e proporcional ao plano de producao".

Ate 24/09/2026 o fechamento debitava de novo o valor da MP consumida,
apoiado no 13.9 ("o custo corresponde ao valor das materias-primas
consumidas"). As duas regras juntas cobravam o mesmo desembolso duas
vezes: o 13.9 descreve o custo do PRODUTO, que forma o custo unitario, o
valor do estoque e o custo das vendas do 12.3.2 -- nao um segundo
pagamento.
"""

from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    CapacidadeProdutoGrupo,
    Cidade,
    Decisao,
    ComposicaoProduto,
    EstoqueMateriaPrima,
    Grupo,
    MateriaPrima,
    Producao,
    Produto,
    ResultadoFinanceiro,
    Rodada,
    User,
)
from app.parametros import CUSTO_OPERADOR_POR_RODADA


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class MateriaPrimaCobradaUmaVezTest(TestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(
            email_usuario="ceo-mp@example.com", nome_usuario="CEO",
            password="pass", tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000000"))
        self.grupo.membros.add(self.ceo)
        self.mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("3")
        )
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=1
        )
        ComposicaoProduto.objects.create(
            produto=self.produto, materia_prima=self.mp,
            quantidade_por_unidade=Decimal("2"),
        )
        CapacidadeProdutoGrupo.objects.create(
            grupo=self.grupo, produto=self.produto, maquinas=1, operadores=2,
            minutos_por_maquina=400,
        )
        self.cidade = Cidade.objects.create(
            nome="Fortaleza", distancia_km=527, demanda=6000
        )
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.client.login(username="ceo-mp@example.com", password="pass")

    def _comprar(self, kg):
        return self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_compra_mp": "1",
                "materia_prima": self.mp.id,
                "cidade_fornecedora": self.cidade.id,
                "quantidade_kg": str(kg),
            },
            follow=True,
        )

    def test_a_compra_debita_o_caixa_na_rodada_da_compra(self):
        """7.2: e este o momento do pagamento."""
        capital_antes = self.grupo.capital

        self._comprar(100)

        self.grupo.refresh_from_db()
        # 100 kg x R$ 3,00 + frete de uma viagem (527 km x R$ 1,50)
        self.assertEqual(
            capital_antes - self.grupo.capital, Decimal("300") + Decimal("790.50")
        )

    def test_produzir_nao_debita_a_materia_prima_de_novo(self):
        self._comprar(100)
        self.grupo.refresh_from_db()
        capital_depois_da_compra = self.grupo.capital
        # a MP chega na rodada seguinte (7.3); aqui ela e posta em estoque
        # direto para isolar o efeito da producao
        EstoqueMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=self.mp, quantidade_kg=Decimal("100")
        )
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1, quantidade_planejada=50
        )

        from app.services.producao import executar_producao

        custo, _ = executar_producao(grupo=self.grupo, rodada=1)

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.capital, capital_depois_da_compra)
        # o custo do 13.9 existe -- e o custo do produto, nao um pagamento
        self.assertEqual(custo, Decimal("50") * self.produto.custo_unitario_estimado)

    def test_o_fechamento_nao_cobra_a_producao(self):
        """O caminho inteiro: comprar, produzir e fechar a rodada.

        Sem envio e com a submissao entregue, a unica saida do fechamento e
        a folha do 14.3 mais a armazenagem do 6.4 -- se a MP consumida
        tambem saisse, a queda seria R$ 300,00 maior.
        """
        self._comprar(100)
        EstoqueMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=self.mp, quantidade_kg=Decimal("100")
        )
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1, quantidade_planejada=50
        )
        Decisao.objects.create(
            grupo=self.grupo, rodada=1, descricao="Plano da rodada", quantidade=0
        )
        self.grupo.refresh_from_db()
        capital_antes_do_fechamento = self.grupo.capital

        rodada = Rodada.objects.get(numero=1)
        rodada.fim = timezone.now() - timedelta(minutes=1)
        rodada.save(update_fields=["fim"])
        call_command("fechar_rodadas", stdout=StringIO())

        self.grupo.refresh_from_db()
        producao = Producao.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(producao.quantidade_produzida, 50)

        queda = capital_antes_do_fechamento - self.grupo.capital
        folha = Decimal("2") * CUSTO_OPERADOR_POR_RODADA
        # 6.4: 2% sobre o valor de producao das 50 unidades em estoque
        armazenagem = (
            Decimal("50") * self.produto.custo_unitario_estimado * Decimal("0.02")
        )
        self.assertEqual(queda, folha + armazenagem)

    def test_o_custo_do_produto_continua_gravado_na_ordem(self):
        """O 13.9 alimenta o custo unitario, o valor do estoque e o custo das
        vendas do 12.3.2 -- some-lo quebraria os tres."""
        EstoqueMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=self.mp, quantidade_kg=Decimal("100")
        )
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1, quantidade_planejada=50
        )

        from app.services.producao import executar_producao

        executar_producao(grupo=self.grupo, rodada=1)

        ordem = Producao.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(ordem.custo_unitario, self.produto.custo_unitario_estimado)
        self.assertEqual(ordem.custo_total, Decimal("50") * ordem.custo_unitario)

    def test_o_resultado_financeiro_registra_a_compra_uma_vez(self):
        self._comprar(100)

        resultado = ResultadoFinanceiro.objects.get(grupo=self.grupo, rodada=1)

        self.assertEqual(resultado.custos, Decimal("300") + Decimal("790.50"))
