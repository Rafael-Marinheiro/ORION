"""Frete da distribuicao de produto acabado.

Ate 2026-09-18 usava R$ 0,10 por km por unidade -- taxa sem origem
documental e, pior, linear: sair de 40 para 41 unidades mudava o frete em
2%, entao nao havia licao de planejamento de carga nenhuma. Agora usa o
mesmo caminhao da compra de materia-prima, e a mesma licao vale nos dois
lados da operacao.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import (
    Cidade,
    ComposicaoProduto,
    Distribuicao,
    EstoqueProduto,
    Evento,
    EventoRodada,
    Grupo,
    MateriaPrima,
    Produto,
    Rodada,
    User,
)


class FreteDaDistribuicaoTest(TestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(
            email_usuario="ceo@teste.com",
            nome_usuario="CEO",
            password="senha123",
            tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("500000"))
        self.grupo.membros.add(self.ceo)

        # Produto A do 6.1: 300 kg por unidade, entao 40 unidades por caminhao
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2, ativo=True
        )
        mp1 = MateriaPrima.objects.create(codigo="MP1", nome="MP1", preco_unitario=3)
        ComposicaoProduto.objects.create(
            produto=self.produto, materia_prima=mp1, quantidade_por_unidade=300
        )

        self.natal = Cidade.objects.create(nome="Natal", distancia_km=172, demanda=1550)
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.client.login(username="ceo@teste.com", password="senha123")

    def _estocar(self, quantidade):
        EstoqueProduto.objects.create(
            grupo=self.grupo, produto=self.produto, rodada_entrada=1, quantidade=quantidade
        )
        self.grupo.estoque = quantidade
        self.grupo.save(update_fields=["estoque"])

    def _enviar(self, quantidade):
        return self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_envio": "1",
                "produto": self.produto.id,
                "cidade": self.natal.id,
                "quantidade": quantidade,
                "preco_unitario": "3000",
            },
            follow=True,
        )

    def test_caminhao_cheio_paga_uma_viagem(self):
        self._estocar(40)

        self._enviar(40)

        envio = Distribuicao.objects.get(grupo=self.grupo)
        # 1 viagem x 172 km x R$ 1,50
        self.assertEqual(envio.custo_transporte, Decimal("1360.00"))

    def test_uma_unidade_a_mais_dobra_o_frete(self):
        self._estocar(41)

        self._enviar(41)

        envio = Distribuicao.objects.get(grupo=self.grupo)
        self.assertEqual(envio.custo_transporte, Decimal("2720.00"))

    def test_capital_do_grupo_e_debitado(self):
        self._estocar(40)
        capital_antes = self.grupo.capital

        self._enviar(40)

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.capital, capital_antes - Decimal("1360.00"))

    def test_evento_de_custo_de_transporte_encarece_o_frete(self):
        """Greve de caminhoneiros: +30% no custo logistico (8.4)."""
        greve = Evento.objects.create(
            nome="Greve de caminhoneiros",
            tipo="custo_transporte",
            modo_aplicacao="percentual",
            impacto_percentual=30,
            probabilidade=15,
        )
        EventoRodada.objects.create(rodada=1, jogo=None, evento=greve)
        self._estocar(40)

        self._enviar(40)

        envio = Distribuicao.objects.get(grupo=self.grupo)
        self.assertEqual(envio.custo_transporte, Decimal("1768.00"))  # 1.360 x 1,30

    def test_o_aluno_ve_a_ocupacao_do_caminhao_que_pagou(self):
        """A ocupacao e o que ensina; o valor sozinho nao denuncia desperdicio."""
        self._estocar(41)

        resposta = self._enviar(41)

        corpo = resposta.content.decode()
        self.assertIn("2 viagem(ns)", corpo)
        self.assertIn("51% da capacidade", corpo)

    def test_cidade_mais_longe_custa_mais_pela_mesma_carga(self):
        acari = Cidade.objects.create(nome="Acari", distancia_km=23, demanda=50)
        self._estocar(80)

        self._enviar(40)
        self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_envio": "1",
                "produto": self.produto.id,
                "cidade": acari.id,
                "quantidade": 40,
                "preco_unitario": "3000",
            },
            follow=True,
        )

        para_natal = Distribuicao.objects.get(grupo=self.grupo, cidade=self.natal)
        para_acari = Distribuicao.objects.get(grupo=self.grupo, cidade=acari)
        self.assertGreater(para_natal.custo_transporte, para_acari.custo_transporte)
