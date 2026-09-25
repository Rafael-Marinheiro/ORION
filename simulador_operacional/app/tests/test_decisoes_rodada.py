# -*- coding: utf-8 -*-
"""A tela de decisoes decide UMA rodada, e a conferencia mostra o que sera
enviado.

O 10.3 poe "Decisoes por Rodada" com compras, producao, comercializacao e
investimentos; o 11.2 faz da submissao o ato que fecha a rodada para a
equipe. A tela existia, mas a etapa de conferencia resumia tudo em "12
registro(s) disponivel(is) para conferencia" -- um numero que nao se
confere, e que ainda contava registros de rodadas ja fechadas.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    AuditoriaSubmissaoRodada,
    CEOGrupoRodada,
    Cidade,
    CompraMateriaPrima,
    Decisao,
    Distribuicao,
    GameConfig,
    Grupo,
    Jogo,
    MateriaPrima,
    Producao,
    Produto,
    Rodada,
    User,
)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class DecisoesDaRodadaCorrenteTest(TestCase):
    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        self.grupo = Grupo.objects.create(
            nome="Equipe Vega", jogo=self.jogo, capital=Decimal("1000000")
        )
        self.ceo = User.objects.create_user(
            email_usuario="ceo-decisoes@example.com", nome_usuario="CEO",
            password="pass", tipo_usuario="lider_grupo",
        )
        self.grupo.membros.add(self.ceo)
        self.grupo.lider = self.ceo
        self.grupo.save()

        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=2
        )
        self.mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("3")
        )
        self.cidade = Cidade.objects.create(
            nome="Recife", distancia_km=290, demanda=4000
        )

        Rodada.objects.create(
            jogo=self.jogo, numero=1,
            fim=timezone.now() - timedelta(hours=2), fechada=True,
        )
        self.rodada = Rodada.objects.create(
            jogo=self.jogo, numero=2, fim=timezone.now() + timedelta(hours=2)
        )
        CEOGrupoRodada.objects.create(grupo=self.grupo, rodada=2, usuario=self.ceo)
        self.client.force_login(self.ceo)

    def _comprar(self, rodada, kg):
        return CompraMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=self.mp, cidade_fornecedora=self.cidade,
            rodada_pedido=rodada, rodada_recebimento=rodada + 1,
            quantidade_kg=Decimal(kg), preco_unitario=Decimal("3"),
            custo_logistico=Decimal("0"), valor_total=Decimal(kg) * 3,
        )

    def test_a_tela_so_lista_o_que_pertence_a_rodada_corrente(self):
        """O historico mora em Relatorios; aqui ele confunde a conferencia."""
        self._comprar(1, 100)
        self._comprar(2, 500)
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1, quantidade_planejada=10
        )
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=2, quantidade_planejada=20
        )

        contexto = self.client.get(reverse("decisoes_rodada")).context

        self.assertEqual([c.rodada_pedido for c in contexto["compras_mp"]], [2])
        self.assertEqual([p.rodada for p in contexto["producoes"]], [2])

    def test_o_painel_geral_continua_mostrando_o_historico(self):
        self._comprar(1, 100)
        self._comprar(2, 500)

        contexto = self.client.get(reverse("painel_grupo")).context

        self.assertEqual(
            sorted(c.rodada_pedido for c in contexto["compras_mp"]), [1, 2]
        )

    def test_a_conferencia_mostra_cada_decisao_com_o_que_ela_faz(self):
        self._comprar(2, 500)
        Distribuicao.objects.create(
            grupo=self.grupo, produto=self.produto, cidade=self.cidade, rodada=2,
            quantidade=40, preco_unitario=Decimal("6500"),
            custo_transporte=Decimal("0"),
        )

        resposta = self.client.get(reverse("decisoes_rodada"))

        self.assertContains(resposta, "500 kg de MP1 — Recife")
        self.assertContains(resposta, "chega na rodada 3")
        self.assertContains(resposta, "40 un de A para Recife")
        # o numero solto nao volta
        self.assertNotContains(resposta, "registro(s) disponível(is)")

    def test_rodada_sem_decisao_diz_isso_em_vez_de_contar_registros(self):
        self._comprar(1, 100)

        resposta = self.client.get(reverse("decisoes_rodada"))

        self.assertContains(resposta, "Nenhuma decisão registrada nesta rodada.")


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class SubmissaoSemTextoTest(TestCase):
    """11.2: submeter e o ato que fecha a rodada, nao um formulario.

    A tela pedia "descricao" e "quantidade" -- dois campos que nenhuma regra
    le. O fechamento so consulta se a submissao existe.
    """

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        self.grupo = Grupo.objects.create(
            nome="Equipe Vega", jogo=self.jogo, capital=Decimal("1000000")
        )
        self.ceo = User.objects.create_user(
            email_usuario="ceo-submissao@example.com", nome_usuario="CEO",
            password="pass", tipo_usuario="lider_grupo",
        )
        self.grupo.membros.add(self.ceo)
        self.grupo.lider = self.ceo
        self.grupo.save()
        Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() + timedelta(hours=2)
        )
        CEOGrupoRodada.objects.create(grupo=self.grupo, rodada=1, usuario=self.ceo)
        self.client.force_login(self.ceo)

    def test_o_botao_sozinho_registra_a_submissao(self):
        self.client.post(reverse("decisoes_rodada"), {"enviar_decisao": "1"})

        decisao = Decisao.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(decisao.descricao, "Decisões da rodada 1")
        self.assertTrue(
            AuditoriaSubmissaoRodada.objects.filter(
                grupo=self.grupo, rodada=1, usuario=self.ceo
            ).exists()
        )

    def test_a_tela_nao_pede_mais_descricao_nem_quantidade(self):
        corpo = self.client.get(reverse("decisoes_rodada")).content.decode()

        self.assertNotIn('name="descricao"', corpo)
        self.assertIn("Enviar submissão da rodada 1", corpo)

    def test_a_segunda_submissao_nao_sobrescreve_a_primeira(self):
        self.client.post(reverse("decisoes_rodada"), {"enviar_decisao": "1"})
        primeira = Decisao.objects.get(grupo=self.grupo, rodada=1)

        self.client.post(reverse("decisoes_rodada"), {"enviar_decisao": "1"})

        self.assertEqual(Decisao.objects.filter(grupo=self.grupo, rodada=1).count(), 1)
        self.assertEqual(
            Decisao.objects.get(grupo=self.grupo, rodada=1).data_criacao,
            primeira.data_criacao,
        )
