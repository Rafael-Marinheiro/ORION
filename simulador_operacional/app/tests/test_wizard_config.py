from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from app.models import GameConfig, User


class GameConfigWizardTest(TestCase):
    """O wizard guarda cleaned_data na sessao, que serializa em JSON.

    Antes da correcao, o Decimal de capital_inicial estourava
    `Object of type Decimal is not JSON serializable` ao sair da etapa 1,
    entao o assistente nunca chegava na etapa 2.
    """

    def setUp(self):
        self.staff = User.objects.create_user(
            email_usuario="prof@teste.com",
            nome_usuario="Professor",
            password="senha123",
            tipo_usuario="gamemaster",
        )
        self.client.force_login(self.staff)
        self.url = reverse("game_config_wizard")

    def test_etapa_1_avanca_com_valor_decimal(self):
        resposta = self.client.post(
            self.url,
            {
                "step": "1",
                "capital_inicial": "1000000.00",
                "estoque_inicial": "0",
                "maquinas_iniciais": "40",
                "capacidade_maquina": "100",
            },
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertIn("step=2", resposta["Location"])
        self.assertIn("game_config_wizard", self.client.session)

    def test_fluxo_completo_salva_a_configuracao(self):
        self.client.post(
            self.url,
            {
                "step": "1",
                "capital_inicial": "750000.50",
                "estoque_inicial": "12",
                "maquinas_iniciais": "8",
                "capacidade_maquina": "120",
            },
        )
        self.client.post(
            self.url,
            {
                "step": "2",
                "produtos_habilitados": "P1,P2",
                "modulo_producao": "on",
                "modulo_distribuicao": "on",
            },
        )

        resposta = self.client.post(self.url, {"step": "3", "confirmar": "1"})

        self.assertEqual(resposta.status_code, 302)
        config = GameConfig.objects.get(id=1)
        self.assertEqual(config.capital_inicial, Decimal("750000.50"))
        self.assertEqual(config.maquinas_iniciais, 8)
        self.assertEqual(config.produtos_habilitados, "P1,P2")
        # a sessao e limpa depois de confirmar
        self.assertNotIn("game_config_wizard", self.client.session)

    def test_confirmar_sem_etapas_anteriores_volta_para_o_inicio(self):
        resposta = self.client.post(self.url, {"step": "3", "confirmar": "1"})

        self.assertEqual(resposta.status_code, 302)
        self.assertIn("step=1", resposta["Location"])
