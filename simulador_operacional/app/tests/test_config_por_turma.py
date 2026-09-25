# -*- coding: utf-8 -*-
"""A configuracao editada e a da turma, nao a de id 1.

Cada `Jogo` tem a sua `GameConfig`, e o fechamento le a do jogo da rodada
(`fechar_rodadas`: `config = rodada.jogo.config`). A tela de parametros e o
assistente gravavam sempre em `GameConfig.objects.get_or_create(id=1)`: com
duas turmas no sistema, o professor mudava o capital ou os pesos do 12.4,
salvava, e a turma dele continuava igual -- sem nenhum aviso de que a
escrita foi para outro lugar.
"""

from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from app.models import GameConfig, Grupo, Jogo, User


def _pesos():
    return {
        "peso_eo": "0.30", "peso_df": "0.25", "peso_ee": "0.15",
        "peso_sd": "0.20", "peso_ds": "0.10",
    }


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ParametrosPorTurmaTest(TestCase):
    def setUp(self):
        self.professor = User.objects.create_user(
            email_usuario="prof-config@example.com", nome_usuario="Professora",
            password="pass", tipo_usuario="gamemaster",
        )
        # a config de id 1 e a dos grupos sem turma
        self.avulsa, _ = GameConfig.objects.get_or_create(
            id=1, defaults={"capital_inicial": Decimal("1000000"), "numero_rodadas": 3}
        )
        self.config_manha = GameConfig.objects.create(
            capital_inicial=Decimal("500000"), numero_rodadas=5
        )
        self.manha = Jogo.objects.create(nome="Turma da manhã", config=self.config_manha)
        Grupo.objects.create(nome="Equipe Vega", jogo=self.manha)
        self.client.force_login(self.professor)

    def test_a_tela_abre_a_configuracao_da_turma_em_foco(self):
        resposta = self.client.get(reverse("game_config"), {"jogo": self.manha.id})

        self.assertEqual(resposta.context["object"], self.config_manha)
        self.assertEqual(resposta.context["turma_em_foco"], "Turma da manhã")

    def test_salvar_grava_na_turma_e_nao_na_configuracao_de_id_1(self):
        dados = {
            "capital_inicial": "750000", "estoque_inicial": "0",
            "maquinas_iniciais": "40", "maquinas_iniciais_a": "15",
            "maquinas_iniciais_b": "15", "maquinas_iniciais_c": "10",
            "trabalhadores_iniciais": "80", "numero_rodadas": "5",
            "produtos_habilitados": "", "modulo_producao": "on",
            "modulo_distribuicao": "on", "modulo_financeiro": "on",
        }
        dados.update(_pesos())

        self.client.post(f"{reverse('game_config')}?jogo={self.manha.id}", dados)

        self.config_manha.refresh_from_db()
        self.avulsa.refresh_from_db()
        self.assertEqual(self.config_manha.capital_inicial, Decimal("750000"))
        self.assertEqual(self.avulsa.capital_inicial, Decimal("1000000"))

    def test_a_tela_oferece_as_turmas(self):
        resposta = self.client.get(reverse("game_config"))

        self.assertIn(
            "Turma da manhã",
            [opcao["nome"] for opcao in resposta.context["turmas"]],
        )


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class AssistenteDeConfiguracaoTest(TestCase):
    def setUp(self):
        self.professor = User.objects.create_user(
            email_usuario="prof-wizard@example.com", nome_usuario="Professora",
            password="pass", tipo_usuario="gamemaster",
        )
        GameConfig.objects.get_or_create(
            id=1, defaults={"capital_inicial": Decimal("1000000"), "numero_rodadas": 3}
        )
        self.config_noite = GameConfig.objects.create(
            capital_inicial=Decimal("400000"), numero_rodadas=4
        )
        self.noite = Jogo.objects.create(nome="Turma da noite", config=self.config_noite)
        self.client.force_login(self.professor)

    def _passo1(self, **extra):
        dados = {
            "step": "1", "jogo": str(self.noite.id), "capital_inicial": "800000",
            "estoque_inicial": "0", "maquinas_iniciais": "40", "numero_rodadas": "6",
        }
        dados.update(extra)
        return self.client.post(reverse("game_config_wizard"), dados)

    def _passo2(self):
        return self.client.post(
            reverse("game_config_wizard"),
            {"step": "2", "produtos_habilitados": "A,B", "modulo_producao": "on"},
        )

    def test_o_assistente_pergunta_o_numero_de_rodadas(self):
        """5: e o parametro que decide quando a classificacao final libera."""
        corpo = self.client.get(reverse("game_config_wizard")).content.decode()

        self.assertIn('name="numero_rodadas"', corpo)
        self.assertIn('name="jogo"', corpo)

    def test_a_configuracao_vai_para_a_turma_escolhida(self):
        self._passo1()
        self._passo2()

        self.client.post(
            reverse("game_config_wizard"), {"step": "3", "confirmar": "1"}
        )

        self.config_noite.refresh_from_db()
        avulsa = GameConfig.objects.get(id=1)
        self.assertEqual(self.config_noite.capital_inicial, Decimal("800000"))
        self.assertEqual(self.config_noite.numero_rodadas, 6)
        self.assertEqual(avulsa.capital_inicial, Decimal("1000000"))

    def test_sem_turma_o_assistente_grava_na_configuracao_avulsa(self):
        self._passo1(jogo="")
        self._passo2()

        self.client.post(
            reverse("game_config_wizard"), {"step": "3", "confirmar": "1"}
        )

        self.config_noite.refresh_from_db()
        avulsa = GameConfig.objects.get(id=1)
        self.assertEqual(avulsa.capital_inicial, Decimal("800000"))
        self.assertEqual(self.config_noite.capital_inicial, Decimal("400000"))

    def test_a_revisao_diz_de_qual_turma_sao_os_numeros(self):
        self._passo1()
        self._passo2()

        resposta = self.client.get(f"{reverse('game_config_wizard')}?step=3")

        self.assertEqual(resposta.context["turma_escolhida"], "Turma da noite")
        self.assertContains(resposta, "Turma da noite")
        # "True" cru saiu da revisao
        self.assertContains(resposta, "Ativo")
        self.assertNotContains(resposta, "<dd>True</dd>")

    def test_rodadas_fora_da_faixa_do_5_sao_recusadas(self):
        resposta = self._passo1(numero_rodadas="2")

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("numero_rodadas", resposta.context["form"].errors)
