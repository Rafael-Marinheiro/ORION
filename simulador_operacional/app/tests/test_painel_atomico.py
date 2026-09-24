"""A submissao do painel move capital em saves separados.

Cada ramo de PainelGrupoView.post grava o registro, debita o capital do
grupo e atualiza o ResultadoFinanceiro em tres saves. Sem transacao, uma
falha entre eles deixa compra registrada sem debito, ou capital debitado
sem lancamento contabil -- e o DRE do grupo para de fechar.
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    Cidade,
    ComposicaoProduto,
    CompraMateriaPrima,
    Grupo,
    MateriaPrima,
    ResultadoFinanceiro,
    Produto,
    Rodada,
)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class SubmissaoAtomicaTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.ceo = User.objects.create_user(
            email_usuario="ceo-atomico@example.com",
            nome_usuario="CEO Atomico",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Atomica", capital=Decimal("1000000"))
        self.grupo.membros.add(self.ceo)
        # 7.1: MP1 vem de Fortaleza ou Maceio. Distancia ate Natal pelo 9.1.
        self.cidade = Cidade.objects.create(nome="Fortaleza", distancia_km=527, demanda=6000)
        self.mp1 = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("3")
        )
        # RN-05 limita a compra a 150% do que a fabrica consome: sem linha de
        # producao que use a MP, o teto e zero e nao ha compra para testar.
        produto = Produto.objects.create(codigo="A", nome="Produto A", tempo_producao_min=1)
        ComposicaoProduto.objects.create(
            produto=produto, materia_prima=self.mp1, quantidade_por_unidade=Decimal("2")
        )
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.client.login(username="ceo-atomico@example.com", password="pass")

    def _comprar(self):
        return self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_compra_mp": "1",
                "materia_prima": self.mp1.id,
                "cidade_fornecedora": self.cidade.id,
                "quantidade_kg": "10",
            },
        )

    def test_compra_valida_debita_o_capital(self):
        """Guarda o caminho feliz: o rollback do teste seguinte so vale se este passa."""
        capital_antes = self.grupo.capital

        self._comprar()

        self.grupo.refresh_from_db()
        self.assertEqual(CompraMateriaPrima.objects.filter(grupo=self.grupo).count(), 1)
        self.assertLess(self.grupo.capital, capital_antes)

    def test_falha_depois_do_debito_desfaz_a_compra_inteira(self):
        """O ResultadoFinanceiro e gravado depois do debito: falhar ali nao pode
        deixar capital a menos nem compra registrada."""
        capital_antes = self.grupo.capital

        with patch.object(
            ResultadoFinanceiro.objects,
            "get_or_create",
            side_effect=DatabaseError("falha simulada apos o debito"),
        ):
            with self.assertRaises(DatabaseError):
                self._comprar()

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.capital, capital_antes)
        self.assertEqual(CompraMateriaPrima.objects.filter(grupo=self.grupo).count(), 0)
