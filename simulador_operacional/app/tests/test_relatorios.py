from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Grupo, ResultadoFinanceiro


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ExportacoesRelatoriosTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email_usuario="gm@example.com",
            nome_usuario="GM",
            password="pass",
        )
        self.grupo1 = Grupo.objects.create(nome="G1")
        self.grupo1.membros.add(self.user)
        self.grupo2 = Grupo.objects.create(nome="G2")
        ResultadoFinanceiro.objects.create(
            grupo=self.grupo1,
            rodada=1,
            receita=100,
            custos=50,
            lucro=50,
            saldo_caixa=150,
        )
        ResultadoFinanceiro.objects.create(
            grupo=self.grupo2,
            rodada=2,
            receita=200,
            custos=100,
            lucro=100,
            saldo_caixa=300,
        )
        self.client.login(username="gm@example.com", password="pass")

    def test_export_csv_filtered(self):
        url = reverse("export_resultados_csv")
        response = self.client.get(url, {"rodada": 1, "grupo": self.grupo1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("G1", content)
        self.assertNotIn("G2", content)

    def test_export_json_filtered(self):
        url = reverse("export_resultados_json")
        response = self.client.get(url, {"rodada": 1, "grupo": self.grupo1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["grupo"], "G1")
