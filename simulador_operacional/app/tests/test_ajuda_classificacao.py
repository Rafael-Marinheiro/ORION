# -*- coding: utf-8 -*-
"""A Ajuda explica como a nota e formada.

A tela dizia apenas onde ver a posicao. Sustentabilidade, que o 12.1 e o
12.7 apontam como o diferencial pedagogico do modelo, nao aparecia em tela
nenhuma -- o aluno nao podia perseguir um criterio que nao sabia existir.

Os pesos vem da configuracao da turma, nao de tabela fixa: o 12.2 permite
ajusta-los por rodada, e uma tabela escrita a mao mentiria na primeira
alteracao do professor.
"""

from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from app.models import GameConfig, Grupo, Jogo, User


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class AjudaExplicaAClassificacaoTest(TestCase):
    def setUp(self):
        GameConfig.objects.get_or_create(
            id=1, defaults={"capital_inicial": Decimal("1000000"), "numero_rodadas": 3}
        )

    def test_os_cinco_eixos_do_12_2_aparecem(self):
        resposta = self.client.get(reverse("ajuda"))

        corpo = resposta.content.decode()
        for eixo in [
            "Eficiência operacional",
            "Desempenho financeiro",
            "Eficiência de estoques",
            "Satisfação da demanda",
            "Sustentabilidade",
        ]:
            self.assertIn(eixo, corpo, eixo)

    def test_os_pesos_padrao_sao_os_do_12_4(self):
        contexto = self.client.get(reverse("ajuda")).context

        pesos = {eixo["sigla"]: eixo["peso"] for eixo in contexto["eixos_da_nota"]}
        self.assertEqual(
            pesos, {"EO": 0.30, "DF": 0.25, "EE": 0.15, "SD": 0.20, "DS": 0.10}
        )

    def test_o_aluno_ve_o_peso_da_propria_turma(self):
        """12.2: os pesos "podem ser ajustados por rodada"."""
        config = GameConfig.objects.create(
            numero_rodadas=4,
            ranking_pesos={"EO": 0.5, "DF": 0.2, "EE": 0.1, "SD": 0.1, "DS": 0.1},
        )
        jogo = Jogo.objects.create(nome="Turma da manhã", config=config)
        grupo = Grupo.objects.create(nome="Equipe Vega", jogo=jogo)
        aluno = User.objects.create_user(
            email_usuario="aluno-ajuda@example.com", nome_usuario="Aluno",
            password="senha12345", tipo_usuario="membro_grupo",
        )
        grupo.membros.add(aluno)
        self.client.force_login(aluno)

        contexto = self.client.get(reverse("ajuda")).context

        pesos = {eixo["sigla"]: eixo["peso"] for eixo in contexto["eixos_da_nota"]}
        self.assertEqual(pesos["EO"], 0.5)
        self.assertEqual(pesos["DF"], 0.2)

    def test_o_desempate_do_12_5_esta_descrito(self):
        resposta = self.client.get(reverse("ajuda"))

        self.assertContains(resposta, "Em caso de empate")
        self.assertContains(resposta, "ordem alfabética")
