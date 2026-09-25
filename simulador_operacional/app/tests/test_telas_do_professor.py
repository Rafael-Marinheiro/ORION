# -*- coding: utf-8 -*-
"""As telas de gestao falam por turma, e a abertura da rodada sabe a proxima.

O 10.4 traz um menu proprio para o administrador e outro para o CEO; o 10.3
poe "Abrir / Fechar rodada" e o monitoramento no gerenciamento. Com mais de
uma turma no mesmo sistema, cada uma dessas telas precisa dizer de qual
turma esta falando.
"""

from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import ExecucaoJob, GameConfig, Grupo, Jogo, Rodada, User


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class AberturaDeRodadaTest(TestCase):
    def setUp(self):
        self.professor = User.objects.create_user(
            email_usuario="prof-abrir@example.com", nome_usuario="Professora",
            password="pass", tipo_usuario="gamemaster",
        )
        self.manha = Jogo.objects.create(
            nome="Turma da manhã", config=GameConfig.objects.create(numero_rodadas=4)
        )
        self.noite = Jogo.objects.create(
            nome="Turma da noite", config=GameConfig.objects.create(numero_rodadas=4)
        )
        Grupo.objects.create(nome="Equipe Vega", jogo=self.manha)
        Grupo.objects.create(nome="Equipe Rigel", jogo=self.noite)
        self.client.force_login(self.professor)

    def test_a_tela_sabe_a_proxima_rodada_de_cada_turma(self):
        Rodada.objects.create(
            jogo=self.manha, numero=1,
            fim=timezone.now() - timedelta(hours=1), fechada=True,
        )

        contexto = self.client.get(reverse("abrir_rodada")).context["estado_turmas"]
        estados = {estado["nome"]: estado for estado in contexto}

        self.assertEqual(estados["Turma da manhã"]["proxima"], 2)
        self.assertEqual(estados["Turma da noite"]["proxima"], 1)

    def test_a_tela_aponta_a_rodada_que_ainda_nao_fechou(self):
        """11.1: quem fecha e o prazo. Abrir outra por cima deixa duas
        rodadas recebendo decisao ao mesmo tempo."""
        Rodada.objects.create(
            jogo=self.manha, numero=1, fim=timezone.now() + timedelta(hours=1)
        )

        contexto = self.client.get(reverse("abrir_rodada")).context["estado_turmas"]
        estados = {estado["nome"]: estado for estado in contexto}

        self.assertEqual(estados["Turma da manhã"]["pendente"], 1)
        self.assertIsNone(estados["Turma da noite"]["pendente"])

    def test_a_turma_que_fechou_o_ciclo_e_marcada(self):
        for numero in (1, 2, 3, 4):
            Rodada.objects.create(
                jogo=self.noite, numero=numero,
                fim=timezone.now() - timedelta(hours=5 - numero), fechada=True,
            )

        contexto = self.client.get(reverse("abrir_rodada")).context["estado_turmas"]
        estados = {estado["nome"]: estado for estado in contexto}

        self.assertTrue(estados["Turma da noite"]["encerrada"])
        self.assertFalse(estados["Turma da manhã"]["encerrada"])

    def test_o_prazo_usa_campo_de_data_e_hora(self):
        """Era campo de texto: a professora digitava o formato de cabeca."""
        corpo = self.client.get(reverse("abrir_rodada")).content.decode()

        self.assertIn('type="datetime-local"', corpo)

    def test_o_formulario_abre_na_turma_que_esta_jogando(self):
        Rodada.objects.create(
            jogo=self.noite, numero=1, fim=timezone.now() + timedelta(hours=1)
        )

        formulario = self.client.get(reverse("abrir_rodada")).context["form"]

        self.assertEqual(formulario.initial["jogo"], self.noite.id)
        self.assertEqual(formulario.initial["numero"], 2)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class GruposPorTurmaTest(TestCase):
    def setUp(self):
        self.professor = User.objects.create_user(
            email_usuario="prof-grupos@example.com", nome_usuario="Professora",
            password="pass", tipo_usuario="gamemaster",
        )
        self.manha = Jogo.objects.create(
            nome="Turma da manhã", config=GameConfig.objects.create()
        )
        Grupo.objects.create(nome="Equipe Vega", jogo=self.manha)
        Grupo.objects.create(nome="Equipe Rigel", jogo=self.manha)
        Grupo.objects.create(nome="Equipe Solta", capital=Decimal("1000"))
        self.client.force_login(self.professor)

    def test_a_lista_separa_as_equipes_por_turma(self):
        turmas = self.client.get(reverse("lista_grupos")).context["turmas"]

        por_nome = {turma["nome"]: turma for turma in turmas}
        self.assertEqual(
            [grupo.nome for grupo in por_nome["Turma da manhã"]["grupos"]],
            ["Equipe Rigel", "Equipe Vega"],
        )
        self.assertEqual(
            [grupo.nome for grupo in por_nome["Grupos sem turma"]["grupos"]],
            ["Equipe Solta"],
        )

    def test_a_tela_nomeia_a_turma_de_cada_bloco(self):
        resposta = self.client.get(reverse("lista_grupos"))

        self.assertContains(resposta, "Turma da manhã")
        self.assertContains(resposta, "Grupos sem turma")


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ExecucoesPorTurmaTest(TestCase):
    """Uma chamada do fechamento pode encontrar rodadas de turmas diferentes.

    Ate 25/09/2026 ela virava UMA execucao, sem turma e sem numero de
    rodada: a tela dizia que "algo rodou" e o professor com duas turmas nao
    sabia qual.
    """

    def setUp(self):
        self.professor = User.objects.create_user(
            email_usuario="prof-jobs@example.com", nome_usuario="Professora",
            password="pass", tipo_usuario="gamemaster",
        )
        self.manha = Jogo.objects.create(
            nome="Turma da manhã", config=GameConfig.objects.create()
        )
        self.noite = Jogo.objects.create(
            nome="Turma da noite", config=GameConfig.objects.create()
        )
        Grupo.objects.create(nome="Equipe Vega", jogo=self.manha)
        Grupo.objects.create(nome="Equipe Rigel", jogo=self.noite)
        self.client.force_login(self.professor)

    def _vencer(self, jogo, numero):
        Rodada.objects.create(
            jogo=jogo, numero=numero, fim=timezone.now() - timedelta(minutes=1)
        )

    def test_cada_rodada_fechada_vira_uma_execucao_com_a_turma(self):
        self._vencer(self.manha, 1)
        self._vencer(self.noite, 1)

        call_command("fechar_rodadas", stdout=StringIO())

        registros = {
            (job.jogo.nome, job.rodada, job.status)
            for job in ExecucaoJob.objects.select_related("jogo")
        }
        self.assertEqual(
            registros,
            {("Turma da manhã", 1, "sucesso"), ("Turma da noite", 1, "sucesso")},
        )

    def test_a_tela_filtra_as_execucoes_pela_turma(self):
        self._vencer(self.manha, 1)
        self._vencer(self.noite, 1)
        call_command("fechar_rodadas", stdout=StringIO())

        resposta = self.client.get(reverse("jobs"), {"jogo": self.manha.id})

        nomes = {job.jogo.nome for job in resposta.context["jobs"]}
        self.assertEqual(nomes, {"Turma da manhã"})

    def test_sem_filtro_a_tela_mostra_todas_as_turmas(self):
        self._vencer(self.manha, 1)
        self._vencer(self.noite, 1)
        call_command("fechar_rodadas", stdout=StringIO())

        resposta = self.client.get(reverse("jobs"))

        self.assertEqual(len(resposta.context["jobs"]), 2)
        self.assertContains(resposta, "Turma da noite")

    def test_a_execucao_registra_quanto_levou(self):
        self._vencer(self.manha, 1)
        call_command("fechar_rodadas", stdout=StringIO())

        job = ExecucaoJob.objects.get()

        self.assertIsNotNone(job.finalizado_em)
        self.assertGreaterEqual(job.duracao_segundos, 0)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class MenuPorPerfilTest(TestCase):
    """10.4: o menu do administrador nao e o do CEO.

    Eram o mesmo, com as telas de gestao penduradas num submenu ao lado das
    do aluno -- e o professor, que nao tem grupo, abria "Painel geral" para
    ver um painel vazio.
    """

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create()
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)

    def test_o_professor_ve_o_menu_de_gestao(self):
        professor = User.objects.create_user(
            email_usuario="prof-menu@example.com", nome_usuario="Professora",
            password="pass", tipo_usuario="gamemaster",
        )
        self.client.force_login(professor)

        resposta = self.client.get(reverse("gerenciamento_jogo"))

        self.assertContains(resposta, reverse("lista_grupos"))
        self.assertContains(resposta, reverse("game_config"))
        self.assertNotContains(resposta, reverse("painel_grupo"))
        self.assertNotContains(resposta, reverse("decisoes_rodada"))

    def test_o_ceo_ve_o_menu_do_grupo(self):
        ceo = User.objects.create_user(
            email_usuario="ceo-menu@example.com", nome_usuario="CEO",
            password="pass", tipo_usuario="lider_grupo",
        )
        self.grupo.membros.add(ceo)
        self.client.force_login(ceo)

        resposta = self.client.get(reverse("painel_grupo"))

        self.assertContains(resposta, reverse("decisoes_rodada"))
        self.assertContains(resposta, reverse("encerramento_rodada"))
        self.assertNotContains(resposta, reverse("game_config"))
