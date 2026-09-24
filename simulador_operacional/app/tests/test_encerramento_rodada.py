from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Grupo, ResultadoFinanceiro, Rodada, User


class EncerramentoRodadaViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email_usuario="ceo@teste.com",
            nome_usuario="CEO",
            password="senha123",
            tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("50000"))
        self.grupo.membros.add(self.user)
        self.client.force_login(self.user)

    def test_exibe_o_resultado_da_ultima_rodada_fechada_do_proprio_grupo(self):
        Rodada.objects.create(
            numero=1, fim=timezone.now() - timedelta(minutes=2), fechada=True
        )
        Rodada.objects.create(
            numero=2, fim=timezone.now() + timedelta(minutes=30), fechada=False
        )
        resultado_fechado = ResultadoFinanceiro.objects.create(
            grupo=self.grupo,
            rodada=1,
            receita=Decimal("1500"),
            custos=Decimal("700"),
            lucro=Decimal("800"),
            saldo_caixa=Decimal("10800"),
        )
        ResultadoFinanceiro.objects.create(
            grupo=self.grupo,
            rodada=2,
            receita=Decimal("9999"),
            custos=Decimal("0"),
            lucro=Decimal("9999"),
            saldo_caixa=Decimal("20799"),
        )

        response = self.client.get(reverse("encerramento_rodada"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["rodada"].numero, 1)
        self.assertEqual(response.context["resultado"], resultado_fechado)
        self.assertContains(response, "Receita")
        self.assertNotContains(response, "9999")
        # A convencao de moeda foi adotada no painel em 23/09/2026 e nao
        # chegou aqui: os quatro numeros sairam por meses sem simbolo.
        self.assertContains(response, "R$ 1.500,00")
        # Lucro e saldo passam pelo partial de sinal, entao o simbolo e o
        # numero nao sao texto contiguo.
        self.assertContains(response, '<span class="o-money">10.800,00</span>')
        self.assertContains(response, '<span class="o-money">800,00</span>')

    def test_prejuizo_sai_marcado_como_negativo(self):
        """Prejuizo e a informacao que o aluno precisa ver primeiro; ate
        24/09/2026 saia na mesma tinta do lucro."""
        Rodada.objects.create(
            numero=1, fim=timezone.now() - timedelta(minutes=2), fechada=True
        )
        ResultadoFinanceiro.objects.create(
            grupo=self.grupo, rodada=1, receita=Decimal("300"),
            custos=Decimal("900"), lucro=Decimal("-600"),
            saldo_caixa=Decimal("-100"),
        )

        response = self.client.get(reverse("encerramento_rodada"))

        self.assertContains(response, '<span class="o-money o-money--neg">-600,00</span>')
        self.assertContains(response, '<span class="o-money o-money--neg">-100,00</span>')

    def test_sem_rodada_fechada_exibe_estado_vazio(self):
        Rodada.objects.create(
            numero=1, fim=timezone.now() + timedelta(minutes=30), fechada=False
        )

        response = self.client.get(reverse("encerramento_rodada"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["rodada"])
        self.assertIsNone(response.context["resultado"])
        self.assertContains(response, "Nenhuma rodada foi encerrada até agora.")
