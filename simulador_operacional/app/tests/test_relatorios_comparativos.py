from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import ConsolidadoRodadaGrupo, GameConfig, Grupo, Jogo, Rodada, User


class RelatoriosComparativosViewTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            email_usuario="ceo@teste.com",
            nome_usuario="CEO",
            password="senha123",
            tipo_usuario="lider_grupo",
        )
        config = GameConfig.objects.create()
        self.jogo = Jogo.objects.create(nome="Turma A", config=config)
        outro_jogo = Jogo.objects.create(nome="Turma B", config=config)
        self.grupo = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.grupo.membros.add(self.usuario)
        rival = Grupo.objects.create(nome="Equipe Rigel", jogo=self.jogo)
        alheio = Grupo.objects.create(nome="Equipe Alheia", jogo=outro_jogo)
        Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() - timedelta(minutes=1), fechada=True
        )
        Rodada.objects.create(
            jogo=outro_jogo, numero=1, fim=timezone.now() - timedelta(minutes=1), fechada=True
        )
        for grupo, receita in ((self.grupo, 100), (rival, 200), (alheio, 999)):
            ConsolidadoRodadaGrupo.objects.create(
                grupo=grupo,
                rodada=1,
                receita_vendas=Decimal(receita),
                custos_totais=Decimal("50"),
                lucro_rodada=Decimal(receita - 50),
            )
        self.client.force_login(self.usuario)

    def test_exibe_comparativo_da_turma_sem_vazar_outro_jogo(self):
        response = self.client.get(reverse("relatorios_comparativos"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lucro acumulado por equipe")
        self.assertContains(response, "Equipe Vega")
        self.assertContains(response, "Equipe Rigel")
        self.assertNotContains(response, "Equipe Alheia")
