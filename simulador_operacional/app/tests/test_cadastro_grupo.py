from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from app.models import GameConfig, Grupo, Jogo, User


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

    def test_senha_de_membro_exige_letras_numeros_e_oito_caracteres(self):
        resposta = self.client.post(self.url, self._payload(**{"form-0-senha": "somenteletras"}))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "A senha deve conter ao menos uma letra e um dígito.")
        self.assertFalse(Grupo.objects.filter(nome="Equipe Vega").exists())

    def test_cadastro_invalido_nao_deixa_usuarios_orfaos(self):
        for extra in [
            {"form-0-lider": ""},
            {"form-1-lider": "on"},
            {"form-1-email": "ANA@teste.com"},
            {"form-1-email": "PROF@teste.com"},
        ]:
            with self.subTest(extra=extra):
                resposta = self.client.post(self.url, self._payload(**extra))
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(User.objects.count(), 1)
                self.assertFalse(Grupo.objects.exists())

    def test_conflito_durante_gravacao_desfaz_grupo_e_usuarios(self):
        criar = User.objects.create_user
        def segundo_falha(**kwargs):
            if kwargs["email_usuario"] == "bruno@teste.com":
                raise IntegrityError("cadastro concorrente")
            return criar(**kwargs)
        with patch.object(User.objects, "create_user", side_effect=segundo_falha):
            resposta = self.client.post(self.url, self._payload())
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(Grupo.objects.exists())

    def test_recursos_iniciais_do_jogo_selecionado(self):
        config = GameConfig.objects.create(capital_inicial=750000)
        jogo = Jogo.objects.create(nome="Outra turma", config=config)
        resposta = self.client.post(self.url, self._payload(jogo=jogo.pk))
        self.assertEqual(resposta.status_code, 302)
        grupo = Grupo.objects.get(nome="Equipe Vega")
        self.assertEqual(grupo.capital, Decimal("750000"))
        self.assertEqual((grupo.maquinas_a, grupo.maquinas_b, grupo.maquinas_c), (15, 15, 10))
        self.assertEqual(grupo.maquinas, 40)
        self.assertEqual(grupo.trabalhadores, 80)

    def test_limites_de_integrantes(self):
        for total in (2, 6, 7):
            dados = self._payload(**{"form-TOTAL_FORMS": str(total)})
            for i in range(3, total):
                dados.update({f"form-{i}-nome": f"Aluno {i}",
                              f"form-{i}-email": f"aluno{i}@teste.com",
                              f"form-{i}-senha": "senha12345"})
            with self.subTest(total=total):
                resposta = self.client.post(self.url, dados)
                self.assertEqual(resposta.status_code, 302 if total == 6 else 200)
                if total == 6:
                    self.assertEqual(Grupo.objects.get().membros.count(), 6)


class EquipeDeQuatroASeisTest(TestCase):
    """5: "no minimo 3 e no maximo 6 participantes".

    O POST aceitava seis integrantes, mas a tela abria com tres campos fixos
    (`extra=0`) e nenhum botao de adicionar: uma equipe de quatro, cinco ou
    seis alunos nao tinha como ser cadastrada pelo professor.
    """

    def setUp(self):
        self.staff = User.objects.create_user(
            email_usuario="prof-equipe@teste.com",
            nome_usuario="Professor",
            password="senha123",
            tipo_usuario="gamemaster",
        )
        self.client.force_login(self.staff)
        self.url = reverse("criar_grupo")
        GameConfig.objects.get_or_create(id=1)

    def _payload(self, quantos):
        dados = {
            "nome": "Equipe Vega",
            "form-TOTAL_FORMS": "6",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "3",
            "form-MAX_NUM_FORMS": "6",
        }
        for i in range(quantos):
            dados[f"form-{i}-nome"] = f"Aluno {i}"
            dados[f"form-{i}-email"] = f"aluno{i}@teste.com"
            dados[f"form-{i}-senha"] = "senha12345"
        dados["form-0-lider"] = "on"
        return dados

    def test_a_tela_abre_com_seis_campos_de_integrante(self):
        resposta = self.client.get(self.url)

        self.assertEqual(len(resposta.context["membro_formset"].forms), 6)
        self.assertContains(resposta, "Integrante 6")
        self.assertContains(resposta, "opcional")

    def test_equipe_de_cinco_e_cadastrada(self):
        resposta = self.client.post(self.url, self._payload(5))

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Grupo.objects.get(nome="Equipe Vega").membros.count(), 5)

    def test_os_campos_extras_em_branco_nao_viram_integrante(self):
        resposta = self.client.post(self.url, self._payload(3))

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Grupo.objects.get(nome="Equipe Vega").membros.count(), 3)
        self.assertEqual(User.objects.count(), 4)

    def test_menos_de_tres_continua_recusado(self):
        resposta = self.client.post(self.url, self._payload(2))

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Grupo.objects.exists())


class EdicaoDeGrupoTest(TestCase):
    """A edicao listava todos os usuarios do sistema.

    O CEO sai de `membros.filter(tipo_usuario="lider_grupo")`, entao marcar
    na lista o lider de outra equipe trocava o CEO deste grupo. A lista
    agora traz os integrantes da propria equipe e os alunos sem equipe.
    """

    def setUp(self):
        self.staff = User.objects.create_user(
            email_usuario="prof-edicao@teste.com", nome_usuario="Professor",
            password="senha123", tipo_usuario="gamemaster",
        )
        self.client.force_login(self.staff)
        self.grupo = Grupo.objects.create(nome="Equipe Vega")
        self.dentro = User.objects.create_user(
            email_usuario="dentro@teste.com", nome_usuario="Aluno de dentro",
            password="senha12345", tipo_usuario="lider_grupo",
        )
        self.grupo.membros.add(self.dentro)
        self.sem_equipe = User.objects.create_user(
            email_usuario="livre@teste.com", nome_usuario="Aluno sem equipe",
            password="senha12345", tipo_usuario="membro_grupo",
        )
        outro = Grupo.objects.create(nome="Equipe Lira")
        self.de_outra_equipe = User.objects.create_user(
            email_usuario="outra@teste.com", nome_usuario="CEO da outra equipe",
            password="senha12345", tipo_usuario="lider_grupo",
        )
        outro.membros.add(self.de_outra_equipe)

    def test_a_lista_de_membros_nao_traz_aluno_de_outra_equipe_nem_o_professor(self):
        resposta = self.client.get(reverse("editar_grupo", args=[self.grupo.pk]))

        oferecidos = list(resposta.context["form"].fields["membros"].queryset)
        self.assertIn(self.dentro, oferecidos)
        self.assertIn(self.sem_equipe, oferecidos)
        self.assertNotIn(self.de_outra_equipe, oferecidos)
        self.assertNotIn(self.staff, oferecidos)
