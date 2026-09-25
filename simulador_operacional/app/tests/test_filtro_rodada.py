"""O filtro de rodada so aceita rodada que existe.

Era um `IntegerField` livre na tela e `request.GET.get("rodada")` cru nas
exportacoes. Dava para pedir a rodada -5 ou a 99 e receber tela vazia sem
explicacao, e `?rodada=abc` chegava ao ORM: "Field 'rodada' expected a
number but got 'abc'" -- ValueError, HTTP 500, nas quatro exportacoes.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.forms import ResultadoFilterForm
from app.models import ConsolidadoRodadaGrupo, Grupo, Rodada, User


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class FiltroDeRodadaTest(TestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(
            email_usuario="ceo-filtro@example.com", nome_usuario="CEO",
            password="pass", tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000"))
        self.grupo.membros.add(self.ceo)
        for numero in (1, 2):
            Rodada.objects.create(
                numero=numero, fim=timezone.now() - timedelta(minutes=1), fechada=True
            )
            ConsolidadoRodadaGrupo.objects.create(
                grupo=self.grupo, rodada=numero, score_multicriterio=Decimal("50")
            )
        # a 3 esta aberta: resultado de rodada aberta nao se mostra
        Rodada.objects.create(numero=3, fim=timezone.now() + timedelta(hours=1))
        self.client.login(username="ceo-filtro@example.com", password="pass")

    def test_o_campo_oferece_so_as_rodadas_fechadas(self):
        form = ResultadoFilterForm(rodadas=[1, 2])

        self.assertEqual(
            form.fields["rodada"].choices,
            [("", "Todas as rodadas"), (1, "Rodada 1"), (2, "Rodada 2")],
        )

    def test_rodada_inexistente_e_recusada_pelo_formulario(self):
        form = ResultadoFilterForm({"rodada": "99"}, rodadas=[1, 2])

        self.assertFalse(form.is_valid())
        self.assertIn("rodada", form.errors)

    def test_rodada_negativa_e_recusada(self):
        form = ResultadoFilterForm({"rodada": "-5"}, rodadas=[1, 2])

        self.assertFalse(form.is_valid())

    def test_texto_no_lugar_do_numero_e_recusado(self):
        form = ResultadoFilterForm({"rodada": "abc"}, rodadas=[1, 2])

        self.assertFalse(form.is_valid())

    def test_sem_rodada_e_valido_e_nao_filtra(self):
        form = ResultadoFilterForm({"rodada": ""}, rodadas=[1, 2])

        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["rodada"])

    def test_a_tela_lista_as_rodadas_fechadas_e_nao_a_aberta(self):
        corpo = self.client.get(reverse("relatorios")).content.decode()

        self.assertIn("Rodada 1", corpo)
        self.assertIn("Rodada 2", corpo)
        self.assertNotIn('value="3"', corpo)

    def test_a_tela_recusa_rodada_que_nao_existe(self):
        resposta = self.client.get(reverse("relatorios"), {"rodada": "99"})

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.context["form"].is_valid())


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ExportacaoComRodadaInvalidaTest(TestCase):
    """As quatro exportacoes liam a querystring crua e quebravam com texto."""

    EXPORTACOES = (
        "export_resultados_pdf",
        "export_resultados_excel",
        "export_resultados_csv",
        "export_resultados_json",
    )

    def setUp(self):
        self.ceo = User.objects.create_user(
            email_usuario="ceo-export@example.com", nome_usuario="CEO",
            password="pass", tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000"))
        self.grupo.membros.add(self.ceo)
        Rodada.objects.create(
            numero=1, fim=timezone.now() - timedelta(minutes=1), fechada=True
        )
        ConsolidadoRodadaGrupo.objects.create(
            grupo=self.grupo, rodada=1, score_multicriterio=Decimal("50")
        )
        self.client.login(username="ceo-export@example.com", password="pass")

    def test_texto_no_lugar_do_numero_nao_derruba_a_exportacao(self):
        for nome in self.EXPORTACOES:
            with self.subTest(exportacao=nome):
                resposta = self.client.get(reverse(nome), {"rodada": "abc"})

                self.assertEqual(resposta.status_code, 200)

    def test_rodada_negativa_nao_derruba_a_exportacao(self):
        for nome in self.EXPORTACOES:
            with self.subTest(exportacao=nome):
                resposta = self.client.get(reverse(nome), {"rodada": "-5"})

                self.assertEqual(resposta.status_code, 200)

    def test_rodada_valida_continua_filtrando(self):
        resposta = self.client.get(reverse("export_resultados_json"), {"rodada": "1"})

        self.assertEqual(resposta.status_code, 200)
