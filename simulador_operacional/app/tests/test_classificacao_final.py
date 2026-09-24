from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import ConsolidadoRodadaGrupo, GameConfig, Grupo, Jogo, Rodada, User


class ClassificacaoFinalViewTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            email_usuario="ceo@teste.com", nome_usuario="CEO", password="senha123"
        )
        config = GameConfig.objects.create(numero_rodadas=2)
        self.jogo = Jogo.objects.create(nome="Turma A", config=config)
        self.vega = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.rigel = Grupo.objects.create(nome="Equipe Rigel", jogo=self.jogo)
        self.vega.membros.add(self.usuario)
        self.client.force_login(self.usuario)

    def _consolidar(self, grupo, rodada, score, eo=0, receita=0):
        return ConsolidadoRodadaGrupo.objects.create(
            grupo=grupo, rodada=rodada, score_multicriterio=Decimal(score),
            eo_percent=Decimal(eo), receita_vendas=Decimal(receita),
        )

    def test_so_exibe_resultado_apos_o_fechamento_de_todo_o_ciclo(self):
        Rodada.objects.create(jogo=self.jogo, numero=1, fim=timezone.now() - timedelta(minutes=1), fechada=True)
        Rodada.objects.create(jogo=self.jogo, numero=2, fim=timezone.now() + timedelta(minutes=1), fechada=False)
        self._consolidar(self.vega, 1, "70")

        response = self.client.get(reverse("classificacao_final"))

        self.assertContains(response, "A classificação final sai quando a simulação for encerrada.")
        self.assertNotContains(response, "Equipe Vega")

    def test_soma_as_rodadas_e_aplica_o_desempate_normativo(self):
        for numero in (1, 2):
            Rodada.objects.create(jogo=self.jogo, numero=numero, fim=timezone.now() - timedelta(minutes=1), fechada=True)
        self._consolidar(self.vega, 1, "70", eo="10", receita="100")
        self._consolidar(self.vega, 2, "70", eo="10", receita="100")
        self._consolidar(self.rigel, 1, "70", eo="11", receita="100")
        self._consolidar(self.rigel, 2, "70", eo="11", receita="100")

        response = self.client.get(reverse("classificacao_final"))

        self.assertEqual(response.context["grupos"][0]["grupo"], self.rigel)
        self.assertEqual(response.context["grupos"][0]["pontuacao"], Decimal("140"))


class AcessoAClassificacaoFinalTest(TestCase):
    """A tela existia sem link: so se chegava nela digitando a URL.

    RN-12: "Ao fim de cada rodada, o sistema gera um ranking provisorio [...]
    Ao termino do jogo, e apresentado um ranking final". O 10.4 poe "Ranking"
    no menu do CEO e "Ranking Geral" no do administrador -- as duas telas sao
    da mesma familia, entao o caminho para a final sai do ranking por rodada.
    """

    def setUp(self):
        config = GameConfig.objects.create(numero_rodadas=1)
        self.jogo = Jogo.objects.create(nome="Turma A", config=config)
        self.grupo = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() - timedelta(minutes=1), fechada=True
        )
        ConsolidadoRodadaGrupo.objects.create(
            grupo=self.grupo, rodada=1, score_multicriterio=Decimal("70")
        )

    def _logar(self, email, **extra):
        usuario = User.objects.create_user(
            email_usuario=email, nome_usuario="Usuario", password="senha123", **extra
        )
        self.client.force_login(usuario)
        return usuario

    def test_o_ranking_por_rodada_leva_a_classificacao_final(self):
        usuario = self._logar("ceo-link@teste.com")
        self.grupo.membros.add(usuario)

        resposta = self.client.get(reverse("ranking"))

        self.assertContains(resposta, reverse("classificacao_final"))

    def test_o_administrador_ve_a_classificacao_sem_pertencer_a_grupo(self):
        """10.3: "Visualizacao de Ranking Geral" e tela do perfil administrador."""
        self._logar("admin-final@teste.com", tipo_usuario="gamemaster")

        resposta = self.client.get(reverse("classificacao_final"))

        self.assertContains(resposta, "Equipe Vega")

    def test_a_classificacao_mantem_o_ranking_marcado_no_menu(self):
        usuario = self._logar("ceo-nav@teste.com")
        self.grupo.membros.add(usuario)

        resposta = self.client.get(reverse("classificacao_final"))

        self.assertEqual(resposta.context["nav"], "ranking")
