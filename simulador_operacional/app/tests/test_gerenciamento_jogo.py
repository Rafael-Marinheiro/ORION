from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import AuditoriaSubmissaoRodada, CEOGrupoRodada, Decisao, GameConfig, Grupo, Jogo, Rodada, User


class GerenciamentoJogoViewTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email_usuario="professor@teste.com", nome_usuario="Professor",
            password="senha123", tipo_usuario="gamemaster",
        )
        self.usuario = User.objects.create_user(
            email_usuario="ceo@teste.com", nome_usuario="CEO Vega", password="senha123"
        )
        self.jogo = Jogo.objects.create(nome="Turma A", config=GameConfig.objects.create())
        self.vega = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.rigel = Grupo.objects.create(nome="Equipe Rigel", jogo=self.jogo)
        self.outro_jogo = Jogo.objects.create(nome="Turma B", config=GameConfig.objects.create())
        self.outra_equipe = Grupo.objects.create(nome="Equipe Oculta", jogo=self.outro_jogo)

    def test_exibe_status_de_submissao_por_grupo_na_rodada_aberta(self):
        rodada = Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() + timedelta(hours=1)
        )
        CEOGrupoRodada.objects.create(grupo=self.vega, rodada=1, usuario=self.usuario)
        decisao = Decisao.objects.create(grupo=self.vega, rodada=1, descricao="Decisão", quantidade=1)
        AuditoriaSubmissaoRodada.objects.create(
            grupo=self.vega, rodada=1, usuario=self.usuario, decisao=decisao
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("gerenciamento_jogo"))

        self.assertContains(response, "Turma A · Rodada 1")
        self.assertContains(response, "1 de 2 grupos submeteram")
        self.assertContains(response, "Equipe Vega")
        self.assertContains(response, "CEO Vega")
        self.assertContains(response, "Enviado")
        self.assertContains(response, "Equipe Rigel")
        self.assertContains(response, "Pendente")
        self.assertNotContains(response, "Equipe Oculta")

    def test_restringe_a_tela_ao_administrador(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("gerenciamento_jogo"))

        self.assertEqual(response.status_code, 403)
