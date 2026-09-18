import re
from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Decisao, Evento, EventoRodada, Grupo, Rodada, User


class TrilhoRodadaContextTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email_usuario="membro@teste.com", nome_usuario="Membro", password="senha123"
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100"))
        self.grupo.membros.add(self.user)
        self.rodada = Rodada.objects.create(
            numero=1, fim=timezone.now() + timezone.timedelta(hours=2)
        )

    def test_visitante_nao_recebe_trilho(self):
        resposta = self.client.get(reverse("ajuda"))

        self.assertNotIn("mostrar_trilho", resposta.context)

    def test_usuario_logado_recebe_rodada_e_evento(self):
        evento = Evento.objects.create(
            nome="Greve nos transportes", tipo="greve", impacto_percentual=-12
        )
        EventoRodada.objects.create(rodada=self.rodada.numero, jogo=None, evento=evento)
        self.client.force_login(self.user)

        resposta = self.client.get(reverse("ajuda"))

        self.assertTrue(resposta.context["mostrar_trilho"])
        self.assertEqual(resposta.context["rodada_corrente"], self.rodada)
        self.assertEqual(resposta.context["evento_corrente"], evento)
        self.assertFalse(resposta.context["submissao_realizada"])

    def test_submissao_existente_marca_o_trilho(self):
        Decisao.objects.create(grupo=self.grupo, rodada=self.rodada.numero)
        self.client.force_login(self.user)

        resposta = self.client.get(reverse("ajuda"))

        self.assertTrue(resposta.context["submissao_realizada"])

    def test_sem_rodada_aberta_nao_quebra(self):
        self.rodada.fechada = True
        self.rodada.save()
        self.client.force_login(self.user)

        resposta = self.client.get(reverse("ajuda"))

        self.assertTrue(resposta.context["mostrar_trilho"])
        self.assertIsNone(resposta.context["rodada_corrente"])


class TrilhoFusoHorarioTest(TestCase):
    """O relogio do trilho e lido por JS via new Date(data-deadline).

    O banco grava em UTC e TIME_ZONE e America/Fortaleza, entao o atributo
    precisa sair com o deslocamento local -- e apontar para o mesmo instante
    que foi gravado, senao a contagem regressiva erra por 3 horas.
    """

    def test_prazo_sai_em_iso_com_deslocamento_e_no_mesmo_instante(self):
        user = User.objects.create_user(
            email_usuario="membro@teste.com", nome_usuario="Membro", password="senha123"
        )
        grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100"))
        grupo.membros.add(user)
        fim = timezone.now() + timezone.timedelta(hours=3)
        Rodada.objects.create(numero=1, fim=fim)
        self.client.force_login(user)

        html = self.client.get(reverse("ajuda")).content.decode()

        marcado = re.search(r'data-deadline="([^"]+)"', html).group(1)
        self.assertTrue(
            marcado.endswith("-03:00"),
            "esperado deslocamento de Fortaleza, veio {}".format(marcado),
        )
        # mesmo instante, so que expresso no fuso local
        self.assertEqual(
            datetime.fromisoformat(marcado).timestamp(),
            fim.timestamp(),
        )
