from django.test import TestCase
from django.urls import reverse

from app.models import GameConfig, Grupo, User


class CadastroGrupoTest(TestCase):
    """GrupoCadastroForm e MembroFormSet eram usados sem estar importados.

    A tela de novo grupo respondia 500 em toda requisicao, o que impedia
    criar qualquer equipe no simulador.
    """

    def setUp(self):
        self.staff = User.objects.create_user(
            email_usuario="prof@teste.com",
            nome_usuario="Professor",
            password="senha123",
            tipo_usuario="gamemaster",
        )
        self.client.force_login(self.staff)
        self.url = reverse("criar_grupo")
        GameConfig.objects.get_or_create(id=1)

    def _payload(self, **extra):
        dados = {
            "nome": "Equipe Vega",
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "3",
            "form-MAX_NUM_FORMS": "6",
        }
        for i, (nome, email, lider) in enumerate([
            ("Ana", "ana@teste.com", True),
            ("Bruno", "bruno@teste.com", False),
            ("Carla", "carla@teste.com", False),
        ]):
            dados["form-{}-nome".format(i)] = nome
            dados["form-{}-email".format(i)] = email
            dados["form-{}-senha".format(i)] = "senha12345"
            if lider:
                dados["form-{}-lider".format(i)] = "on"
        dados.update(extra)
        return dados

    def test_tela_de_novo_grupo_abre(self):
        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("membro_formset", resposta.context)

    def test_cria_grupo_com_tres_integrantes_e_um_lider(self):
        resposta = self.client.post(self.url, self._payload())

        self.assertEqual(resposta.status_code, 302)
        grupo = Grupo.objects.get(nome="Equipe Vega")
        self.assertEqual(grupo.membros.count(), 3)
        self.assertEqual(grupo.lider.email_usuario, "ana@teste.com")
        self.assertEqual(grupo.lider.tipo_usuario, "lider_grupo")

    def test_grupo_sem_lider_nao_e_criado(self):
        dados = self._payload()
        del dados["form-0-lider"]

        resposta = self.client.post(self.url, dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Grupo.objects.filter(nome="Equipe Vega").exists())
