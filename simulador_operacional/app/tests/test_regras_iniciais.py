"""RN-01/RN-02 no original DOCX 5 e RF.01 no original DOCX 3."""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from app.forms import MembroForm, RodadaForm
from app.models import GameConfig, Jogo, Rodada, User
from app.serializers import GameConfigSerializer


class RegrasIniciaisTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prof = User.objects.create_user("prof@escola.edu", "Professor", "SenhaTurma42", tipo_usuario="gamemaster")
        cls.ceo = User.objects.create_user("ceo@escola.edu", "CEO", "SenhaTurma42", tipo_usuario="lider_grupo")
        cls.membro = User.objects.create_user("membro@escola.edu", "Membro", "SenhaTurma42")
        cls.config = GameConfig.objects.create(id=1, numero_rodadas=3)
        cls.jogo = Jogo.objects.create(nome="Turma", config=cls.config)

    def test_limites_de_rodadas_api(self):
        for numero in (2, 3, 12, 13):
            with self.subTest(numero=numero):
                form = GameConfigSerializer(data={"numero_rodadas": numero})
                self.assertEqual(form.is_valid(), numero in (3, 12))

    def test_rodada_usa_limite_do_jogo_escolhido(self):
        outra = Jogo.objects.create(nome="Outra", config=GameConfig.objects.create(numero_rodadas=12))
        for jogo, numero, valido in [(outra, 12, True), (self.jogo, 4, False)]:
            form = RodadaForm(data={"jogo": jogo.pk, "numero": numero, "fim": timezone.now() + timedelta(hours=1)})
            self.assertEqual(form.is_valid(), valido, form.errors)

    def test_professor_define_prazo_futuro(self):
        self.client.force_login(self.prof)
        resposta = self.client.post(reverse("abrir_rodada"), {
            "jogo": self.jogo.pk, "numero": 1,
            "fim": timezone.now() - timedelta(minutes=1),
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Rodada.objects.exists())

    def test_senha_minima_com_letras_e_numeros(self):
        for senha in ("Abc12", "abcdefghijkl", "12345678910", "SenhaTurma42"):
            form = MembroForm(data={"nome": "Aluno", "email": "novo@escola.edu", "senha": senha})
            self.assertEqual(form.is_valid(), senha == "SenhaTurma42", form.errors)

    def test_conta_desativada_e_desconhecida_nao_autenticam(self):
        self.membro.status_usuario = False
        self.membro.save()
        for email in (self.membro.email_usuario, "desconhecido@escola.edu"):
            self.assertFalse(self.client.login(username=email, password="SenhaTurma42"))

    def test_alunos_nao_administram_pelas_telas_ou_api(self):
        api = APIClient()
        for aluno in (self.ceo, self.membro):
            self.client.force_login(aluno)
            for nome in ("register", "criar_grupo", "game_config", "game_config_wizard", "abrir_rodada"):
                with self.subTest(aluno=aluno.email_usuario, tela=nome):
                    self.assertEqual(self.client.get(reverse(nome)).status_code, 403)
                    self.assertEqual(self.client.post(reverse(nome), {}).status_code, 403)
            api.force_authenticate(aluno)
            for metodo, url, dados in [
                ("patch", f"/api/config/{self.config.pk}/", {"capital_inicial": 1}),
                ("post", "/api/rodadas/", {"numero": 1, "fim": timezone.now().isoformat()}),
                ("post", "/api/ceos-rodada/", {}),
                ("delete", f"/api/jogos/{self.jogo.pk}/", {}),
            ]:
                with self.subTest(metodo=metodo, url=url):
                    self.assertEqual(getattr(api, metodo)(url, dados, format="json").status_code, 403)
        self.config.refresh_from_db()
        self.assertEqual(self.config.capital_inicial, 1000000)
        self.assertTrue(Jogo.objects.filter(pk=self.jogo.pk).exists())

    def test_professor_pode_configurar_pela_api(self):
        api = APIClient()
        api.force_authenticate(self.prof)
        resposta = api.patch(f"/api/config/{self.config.pk}/", {"numero_rodadas": 12}, format="json")
        self.assertEqual(resposta.status_code, 200)
        self.config.refresh_from_db()
        self.assertEqual(self.config.numero_rodadas, 12)
