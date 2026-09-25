# -*- coding: utf-8 -*-
"""O ranking classifica os grupos de UMA turma.

O 12 classifica os grupos de um jogo: equipes de turmas diferentes jogaram
rodadas diferentes, com eventos diferentes, e somar as duas listas nao
produz classificacao nenhuma.

Ate 25/09/2026 a tela nao filtrava nada para quem e `is_staff`. O professor
com mais de uma turma via todas misturadas numa lista so, e a rodada de
referencia saia da maior rodada fechada de QUALQUER jogo -- podia nem
existir na turma dele, que entao nao via as proprias equipes na tela.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import ConsolidadoRodadaGrupo, GameConfig, Grupo, Jogo, Rodada, User


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RankingPorTurmaTest(TestCase):
    def setUp(self):
        self.professor = User.objects.create_user(
            email_usuario="prof-ranking@example.com", nome_usuario="Professora",
            password="pass", tipo_usuario="gamemaster",
        )
        self.manha = Jogo.objects.create(
            nome="Turma da manhã", config=GameConfig.objects.create(numero_rodadas=4)
        )
        self.noite = Jogo.objects.create(
            nome="Turma da noite", config=GameConfig.objects.create(numero_rodadas=4)
        )
        self.vega = Grupo.objects.create(nome="Equipe Vega", jogo=self.manha)
        self.rigel = Grupo.objects.create(nome="Equipe Rigel", jogo=self.noite)
        # a turma da manha vai na rodada 1; a da noite ja fechou a 3
        self._fechar(self.manha, 1)
        self._consolidar(self.vega, 1, "40")
        for numero in (1, 2, 3):
            self._fechar(self.noite, numero)
            self._consolidar(self.rigel, numero, "80")
        self.client.force_login(self.professor)

    def _fechar(self, jogo, numero):
        Rodada.objects.create(
            jogo=jogo, numero=numero,
            fim=timezone.now() - timedelta(minutes=numero), fechada=True,
        )

    def _consolidar(self, grupo, rodada, score):
        ConsolidadoRodadaGrupo.objects.create(
            grupo=grupo, rodada=rodada, score_multicriterio=Decimal(score),
            receita_vendas=Decimal("1000"), lucro_rodada=Decimal("100"),
        )

    def test_a_tela_mostra_uma_turma_de_cada_vez(self):
        resposta = self.client.get(reverse("ranking"), {"jogo": self.manha.id})

        nomes = [item["grupo"].nome for item in resposta.context["ranking"]]
        self.assertEqual(nomes, ["Equipe Vega"])
        self.assertEqual(resposta.context["rodada_referencia"], 1)
        self.assertEqual(resposta.context["turma_em_foco"], "Turma da manhã")

    def test_trocar_de_turma_troca_a_rodada_de_referencia(self):
        resposta = self.client.get(reverse("ranking"), {"jogo": self.noite.id})

        nomes = [item["grupo"].nome for item in resposta.context["ranking"]]
        self.assertEqual(nomes, ["Equipe Rigel"])
        self.assertEqual(resposta.context["rodada_referencia"], 3)

    def test_turma_inexistente_cai_na_turma_corrente(self):
        """O parametro vem da querystring: numero solto nao pode dar erro."""
        for valor in ("999", "-1", "abc", ""):
            with self.subTest(jogo=valor):
                resposta = self.client.get(reverse("ranking"), {"jogo": valor})

                self.assertEqual(resposta.status_code, 200)
                self.assertIn(
                    resposta.context["turma_em_foco"],
                    ["Turma da manhã", "Turma da noite"],
                )

    def test_a_tela_oferece_as_turmas_existentes(self):
        resposta = self.client.get(reverse("ranking"))

        self.assertEqual(
            [opcao["nome"] for opcao in resposta.context["turmas"]],
            ["Turma da manhã", "Turma da noite"],
        )

    def test_o_aluno_continua_preso_a_propria_turma(self):
        """Escolher turma e da professora: o grupo ve a dele, e so."""
        ceo = User.objects.create_user(
            email_usuario="ceo-turma@example.com", nome_usuario="CEO",
            password="pass", tipo_usuario="lider_grupo",
        )
        self.vega.membros.add(ceo)
        self.client.force_login(ceo)

        resposta = self.client.get(reverse("ranking"), {"jogo": self.noite.id})

        nomes = [item["grupo"].nome for item in resposta.context["ranking"]]
        self.assertEqual(nomes, ["Equipe Vega"])

    def test_a_classificacao_final_segue_a_mesma_turma(self):
        resposta = self.client.get(
            reverse("classificacao_final"), {"jogo": self.manha.id}
        )

        self.assertEqual(resposta.context["turma_em_foco"], "Turma da manhã")
        self.assertContains(resposta, "Turma da manhã")


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RankingAntesDoPrimeiroFechamentoTest(TestCase):
    """Turma recem-aberta nao tem lider de rodada.

    A lista sem rodada fechada existe so para mostrar quem esta no jogo. Com
    ela, a tela coroava "Lider da rodada" com 0,00 pontos -- um desempenho
    que ninguem teve.
    """

    def setUp(self):
        self.professor = User.objects.create_user(
            email_usuario="prof-nova@example.com", nome_usuario="Professora",
            password="pass", tipo_usuario="gamemaster",
        )
        self.jogo = Jogo.objects.create(
            nome="Turma nova", config=GameConfig.objects.create(numero_rodadas=4)
        )
        Grupo.objects.create(nome="Equipe Cassiopeia", jogo=self.jogo)
        Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() + timedelta(hours=2)
        )
        self.client.force_login(self.professor)

    def test_sem_rodada_fechada_nao_ha_destaque(self):
        resposta = self.client.get(reverse("ranking"))

        self.assertTrue(resposta.context["sem_rodada_fechada"])
        self.assertEqual(resposta.context["destaques"], [])
        self.assertNotContains(resposta, "Líder da rodada")

    def test_a_tela_explica_que_a_rodada_ainda_nao_fechou(self):
        resposta = self.client.get(reverse("ranking"))

        self.assertContains(resposta, "Nenhuma rodada desta turma foi encerrada")
        self.assertContains(resposta, "rodada ainda não encerrada")
        self.assertNotContains(resposta, "sem operação nesta rodada")
