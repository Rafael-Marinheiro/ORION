from django.urls import reverse
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from app.models import Grupo


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RankingAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email_usuario="api@example.com",
            nome_usuario="API User",
            password="pass1234",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        Grupo.objects.create(nome="G1", capital=100)
        Grupo.objects.create(nome="G2", capital=200)

    def test_ranking_order(self):
        response = self.client.get(reverse("api_ranking"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
