"""Entra em toda rota registrada e exige que nenhuma responda 5xx.

As tres telas quebradas encontradas neste projeto -- sortear_eventos_rodada,
o Decimal na sessao do wizard e os imports faltando em /grupos/novo/ --
quebravam na primeira execucao. Nenhuma precisava de teste elaborado para
ser flagrada: bastava alguem abrir a pagina.

As rotas sao descobertas do urlpatterns, nao listadas a mao. Uma rota nova
entra nesta suite sozinha, e uma rota nova com parametro falha ate alguem
registrar um exemplo em PARAMETROS -- que e o comportamento desejado, para
nenhuma tela escapar em silencio.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import URLPattern, URLResolver, reverse
from django.utils import timezone

from app.models import GameConfig, Grupo, Rodada, User
from app.urls import urlpatterns

# Rotas com parametro fora do comum. O `pk` e tentado sozinho, senao seria
# preciso registrar a mao as 28 rotas -detail que o router do DRF gera.
# Rota nova com parametro diferente de `pk` e sem exemplo aqui falha de
# proposito, para nenhuma tela escapar em silencio.
PARAMETROS = {
    "password_reset_confirm": {"uidb64": "MQ", "token": "set-password"},
}

# Rotas que nao respondem GET por natureza.
IGNORADAS = {"token_obtain_pair", "token_refresh"}


def nomes_das_rotas(patterns, prefixo=""):
    for p in patterns:
        if isinstance(p, URLResolver):
            yield from nomes_das_rotas(p.url_patterns, prefixo)
        elif isinstance(p, URLPattern) and p.name:
            yield p.name


class SmokeRotasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        GameConfig.objects.get_or_create(id=1)
        cls.grupo = Grupo.objects.create(
            id=1, nome="Equipe Vega", capital=Decimal("1000"), estoque=10
        )
        Rodada.objects.create(numero=1, fim=timezone.now() + timezone.timedelta(hours=2))

        cls.membro = User.objects.create_user(
            email_usuario="membro@teste.com", nome_usuario="Membro", password="senha123"
        )
        cls.grupo.membros.add(cls.membro)
        cls.staff = User.objects.create_user(
            email_usuario="prof@teste.com",
            nome_usuario="Professor",
            password="senha123",
            tipo_usuario="gamemaster",
        )

    @staticmethod
    def _montar(nome):
        """URL da rota: sem parametro, com `pk`, ou com o exemplo registrado."""
        for kwargs in (None, {"pk": 1}, PARAMETROS.get(nome)):
            if kwargs is None and nome in PARAMETROS:
                continue
            try:
                return reverse(nome, kwargs=kwargs)
            except Exception:
                continue
        return None

    def _varrer(self, rotulo):
        falhas = []
        for nome in sorted(set(nomes_das_rotas(urlpatterns))):
            if nome in IGNORADAS:
                continue
            url = self._montar(nome)
            if url is None:
                falhas.append(
                    "{}: nao foi possivel montar a URL. Se a rota tem parametro "
                    "alem de `pk`, registre um exemplo em PARAMETROS.".format(nome)
                )
                continue
            try:
                resposta = self.client.get(url)
            except Exception as erro:
                falhas.append("{} [{}] {}: estourou {}: {}".format(
                    rotulo, nome, url, type(erro).__name__, erro))
                continue
            if resposta.status_code >= 500:
                falhas.append("{} [{}] {}: HTTP {}".format(
                    rotulo, nome, url, resposta.status_code))
        return falhas

    def test_visitante_nao_recebe_5xx(self):
        falhas = self._varrer("visitante")
        self.assertEqual(falhas, [], "\n" + "\n".join(falhas))

    def test_membro_de_grupo_nao_recebe_5xx(self):
        self.client.force_login(self.membro)
        falhas = self._varrer("membro")
        self.assertEqual(falhas, [], "\n" + "\n".join(falhas))

    def test_professor_nao_recebe_5xx(self):
        self.client.force_login(self.staff)
        falhas = self._varrer("professor")
        self.assertEqual(falhas, [], "\n" + "\n".join(falhas))
