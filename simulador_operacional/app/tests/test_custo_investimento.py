"""Preco da maquina e custo da contratacao -- 14.2.4 e 14.3.

14.2.4: "Custo por maquina: valor FIXADO PELO SIMULADOR (ex: R$ 8.000,00)".
Ate 2026-09-24 o preco vinha do formulario preenchido pelo proprio aluno, e
nada impedia comprar vinte maquinas por R$ 1,00.

14.3: "O custo por funcionario e de R$ 1.800,00 mensais, sendo registrado
como custo fixo operacional". Nenhuma secao cobra taxa de contratacao, e o
fechamento ja lanca a folha por rodada -- debitar um valor de entrada
cobraria a mesma contratacao duas vezes.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import Cidade, Grupo, Investimento, Produto, Rodada, User
from app.parametros import CUSTO_MAQUINA


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class CustoDoInvestimentoTest(TestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(
            email_usuario="ceo-invest@example.com",
            nome_usuario="CEO",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000000"))
        self.grupo.membros.add(self.ceo)
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=1
        )
        # 14.1: marketing e por cidade, entao o formulario exige a praca.
        self.cidade = Cidade.objects.create(
            nome="Recife", distancia_km=290, demanda=4000
        )
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.client.login(username="ceo-invest@example.com", password="pass")

    def _investir(self, categoria, quantidade, valor):
        dados = {
            "enviar_investimento": "1",
            "categoria": categoria,
            "produto": self.produto.id,
            "quantidade": quantidade,
            "valor": str(valor),
        }
        if categoria == "marketing":
            dados["cidade"] = self.cidade.id
        return self.client.post(reverse("painel_grupo"), dados, follow=True)

    def test_preco_da_maquina_vem_do_simulador_nao_do_formulario(self):
        """O aluno digita R$ 1,00 e paga o preco do 14.2.4 mesmo assim."""
        self._investir("maquinas", 2, "1.00")

        investimento = Investimento.objects.get(grupo=self.grupo, categoria="maquinas")
        self.assertEqual(investimento.valor, CUSTO_MAQUINA * 2)

    def test_capital_e_debitado_pelo_preco_do_simulador(self):
        capital_antes = self.grupo.capital

        self._investir("maquinas", 3, "1.00")

        self.grupo.refresh_from_db()
        self.assertEqual(capital_antes - self.grupo.capital, CUSTO_MAQUINA * 3)

    def test_o_ceo_ve_o_preco_unitario_e_o_total(self):
        resposta = self._investir("maquinas", 2, "1.00")

        corpo = resposta.content.decode()
        self.assertIn("2 máquina(s) a R$ 8000.00 cada", corpo)
        self.assertIn("total de R$ 16000.00", corpo)

    def test_o_ceo_e_lembrado_de_contratar_a_equipe(self):
        """14.2.3: maquina sem os dois operadores fica inativa, sem reembolso."""
        resposta = self._investir("maquinas", 3, "1.00")

        self.assertIn("contratar 6 operadores", resposta.content.decode())

    def test_contratar_nao_cobra_taxa_de_entrada(self):
        capital_antes = self.grupo.capital

        self._investir("rh", 4, "5000.00")

        self.grupo.refresh_from_db()
        investimento = Investimento.objects.get(grupo=self.grupo, categoria="rh")
        self.assertEqual(investimento.valor, Decimal("0"))
        self.assertEqual(self.grupo.capital, capital_antes)

    def test_marketing_continua_com_o_valor_escolhido(self):
        """14.1: no marketing, o investimento E a decisao de quanto gastar."""
        self._investir("marketing", 1, "5000.00")

        investimento = Investimento.objects.get(grupo=self.grupo, categoria="marketing")
        self.assertEqual(investimento.valor, Decimal("5000.00"))
