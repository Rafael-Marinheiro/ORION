# -*- coding: utf-8 -*-
"""2.1 -- operacao offline temporaria.

O documento: "os grupos poderao trabalhar em suas analises e decisoes sem a
necessidade de estarem constantemente conectados a internet. A conexao sera
exigida apenas nos momentos de envio das decisoes".

O 2.1.1 fecha o escopo: "o simulador nao podera ser operado inteiramente
offline, pois o envio das decisoes e a atualizacao dos dados exigem
conexao". Por isso nao ha fila de sincronizacao -- submissao entregue
depois do prazo porque estava enfileirada furaria o 11.1.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import CEOGrupoRodada, GameConfig, Grupo, Jogo, Rodada, User


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ServiceWorkerTest(TestCase):
    def test_e_servido_na_raiz(self):
        """Em /static/js/ o escopo cobriria so /static/js/."""
        resposta = self.client.get("/sw.js")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "application/javascript")

    def test_nao_enfileira_envio_de_decisao(self):
        """2.1.1 e 11.1: o envio exige conexao, e o prazo nao espera."""
        corpo = self.client.get("/sw.js").content.decode()

        self.assertIn('requisicao.method !== "GET"', corpo)
        self.assertNotIn("SyncManager", corpo)
        self.assertNotIn("backgroundSync", corpo)

    def test_nao_guarda_admin_nem_api(self):
        corpo = self.client.get("/sw.js").content.decode()

        self.assertIn('startsWith("/admin")', corpo)
        self.assertIn('startsWith("/api")', corpo)

    def test_a_tela_de_offline_existe_e_avisa_do_prazo(self):
        resposta = self.client.get(reverse("offline"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "precisa de conexão")
        self.assertContains(resposta, "rodada não para enquanto")


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RascunhoNoPainelTest(TestCase):
    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=3)
        )
        self.grupo = Grupo.objects.create(
            nome="Equipe Vega", jogo=self.jogo, capital=Decimal("1000000")
        )
        self.ceo = User.objects.create_user(
            email_usuario="ceo-offline@example.com", nome_usuario="CEO",
            password="senha12345", tipo_usuario="lider_grupo",
        )
        self.grupo.membros.add(self.ceo)
        self.grupo.lider = self.ceo
        self.grupo.save()
        Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() + timedelta(hours=2)
        )
        CEOGrupoRodada.objects.create(grupo=self.grupo, rodada=1, usuario=self.ceo)
        self.client.force_login(self.ceo)

    def test_o_painel_marca_a_area_de_rascunho_por_rodada(self):
        """Rascunho de uma rodada nao pode reaparecer na seguinte."""
        corpo = self.client.get(reverse("painel_grupo")).content.decode()

        self.assertIn('data-rascunho="painel-r1"', corpo)

    def test_o_painel_carrega_o_script_de_rascunho(self):
        corpo = self.client.get(reverse("painel_grupo")).content.decode()

        self.assertIn("js/rascunho.js", corpo)

    def test_o_aviso_de_conexao_nasce_escondido(self):
        """Ele so aparece quando o navegador avisa que caiu."""
        corpo = self.client.get(reverse("painel_grupo")).content.decode()

        self.assertIn("data-conexao", corpo)
        self.assertIn("O envio precisa de rede.", corpo)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RegistroDoServiceWorkerTest(TestCase):
    def test_o_registro_exige_contexto_seguro(self):
        """HTTP puro no laboratorio nao pode quebrar a aplicacao."""
        corpo = self.client.get(reverse("home")).content.decode()

        self.assertIn("window.isSecureContext", corpo)
        self.assertIn("/sw.js", corpo)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class SemDependenciaExternaTest(TestCase):
    """2.1 -- nenhum arquivo vem de fora.

    Quatro telas carregavam o Chart.js de `cdn.jsdelivr.net`. Sem internet
    nao ha grafico, e com o service worker o problema piora: a casca abre,
    a tela monta e o grafico fica faltando, sem explicacao. A biblioteca
    passou a ser servida pela propria aplicacao.
    """

    def test_nenhum_template_aponta_para_cdn(self):
        from pathlib import Path

        from django.conf import settings

        raiz = Path(settings.BASE_DIR) / "app" / "templates"
        externos = []
        for caminho in raiz.rglob("*.html"):
            texto = caminho.read_text(encoding="utf-8")
            for marca in ("cdn.jsdelivr.net", "cdnjs.cloudflare.com",
                          "unpkg.com", "fonts.googleapis.com"):
                if marca in texto:
                    externos.append(f"{caminho.name}: {marca}")

        self.assertEqual(externos, [])

    def test_a_biblioteca_de_graficos_e_servida_localmente(self):
        from pathlib import Path

        from django.conf import settings

        vendida = Path(settings.BASE_DIR).parent / "static" / "js" / "chart.umd.min.js"
        self.assertTrue(vendida.exists(), "chart.umd.min.js não foi versionado")
