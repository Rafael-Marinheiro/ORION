from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Group, Decision, InventoryItem, ProductionSetting

User = get_user_model()


class InventorySignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email_usuario="test@example.com",
            nome_usuario="Test",
            senha_usuario="pass",
        )
        self.group = Group.objects.create(nome="G1")
        self.group.membros.add(self.user)

    def test_group_creation_creates_config_and_stock(self):
        prod = ProductionSetting.objects.get(grupo=self.group)
        estoque = InventoryItem.objects.get(grupo=self.group)
        self.assertEqual(prod.maquinas, 1)
        self.assertEqual(estoque.quantidade, 0)

    def test_decision_updates_inventory(self):
        Decision.objects.create(grupo=self.group, descricao="d", producao=10, venda=3)
        estoque = InventoryItem.objects.get(grupo=self.group)
        self.assertEqual(estoque.quantidade, 7)
