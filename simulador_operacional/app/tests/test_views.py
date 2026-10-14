from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db.models import Sum
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    AplicacaoFinanceiraGrupo,
    AuditoriaSubmissaoRodada,
    CapacidadeProdutoGrupo,
    CEOGrupoRodada,
    ComposicaoProduto,
    ConsolidadoRodadaGrupo,
    DemandaCidadeProduto,
    CompraMateriaPrima,
    Decisao,
    Distribuicao,
    Evento,
    EventoRodada,
    EstoqueMateriaPrima,
    EstoqueProduto,
    GameConfig,
    Grupo,
    IndicadorRodadaGrupo,
    Investimento,
    Jogo,
    MateriaPrima,
    MarketShareCidadeProduto,
    Produto,
    Producao,
    ResultadoFinanceiro,
    Rodada,
    Cidade,
)
from app.views import sortear_evento


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class PainelGrupoViewTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.users = [
            User.objects.create_user(
                email_usuario=f"view{i}@example.com",
                nome_usuario=f"Viewer{i}",
                password="secret",
            )
            for i in range(7)
        ]
        self.user = self.users[0]

    def _create_group(self, count):
        grupo = Grupo.objects.create(nome="G1")
        for u in self.users[:count]:
            grupo.membros.add(u)
        return grupo

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 302)

    def test_redirect_if_no_group(self):
        self.client.login(username="view0@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 200)

    def test_get_logged_in_with_group(self):
        self._create_group(3)
        self.client.login(username="view0@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 200)

    def test_painel_expoe_dados_reais_para_grafico_de_desempenho(self):
        grupo = self._create_group(3)
        ResultadoFinanceiro.objects.create(
            grupo=grupo,
            rodada=1,
            receita=Decimal("1200.50"),
            custos=Decimal("800.00"),
            lucro=Decimal("400.50"),
        )
        self.client.login(username="view0@example.com", password="secret")

        response = self.client.get(reverse("painel_grupo"))

        self.assertEqual(response.context["grafico_desempenho"], {
            "labels": ["R1"], "receita": [1200.5], "lucro": [400.5],
        })
        self.assertContains(response, 'id="painel-desempenho"')

    def test_painel_exibe_indicadores_comparados_com_a_rodada_anterior(self):
        grupo = self._create_group(3)
        ConsolidadoRodadaGrupo.objects.create(
            grupo=grupo, rodada=1, receita_vendas=Decimal("100"),
            custos_totais=Decimal("60"), lucro_rodada=Decimal("40"),
            market_share_percent=Decimal("35"),
        )
        ConsolidadoRodadaGrupo.objects.create(
            grupo=grupo, rodada=2, receita_vendas=Decimal("150"),
            custos_totais=Decimal("75"), lucro_rodada=Decimal("75"),
            market_share_percent=Decimal("45"),
        )
        self.client.login(username="view0@example.com", password="secret")

        response = self.client.get(reverse("painel_grupo"))

        self.assertContains(response, "Indicadores da rodada 2")
        self.assertContains(response, "comparados com a rodada 1")
        self.assertContains(response, "Market share")
        self.assertContains(response, "10,0 p.p.")

    def test_filtro_de_rodadas_lista_apenas_rodadas_do_jogo(self):
        jogo = Jogo.objects.create(nome="Jogo do painel", config=GameConfig.objects.create())
        grupo = self._create_group(3)
        grupo.jogo = jogo
        grupo.save(update_fields=["jogo"])
        Rodada.objects.create(jogo=jogo, numero=1, fechada=True, fim=timezone.now())
        Rodada.objects.create(
            jogo=jogo, numero=2, fechada=False, fim=timezone.now() + timedelta(days=1)
        )
        outro_jogo = Jogo.objects.create(nome="Outro jogo", config=GameConfig.objects.create())
        Rodada.objects.create(jogo=outro_jogo, numero=3, fechada=True, fim=timezone.now())
        self.client.login(username="view0@example.com", password="secret")

        response = self.client.get(reverse("painel_grupo"))

        self.assertContains(response, '<select id="rodada" name="rodada">', html=False)
        self.assertContains(response, "Rodada 1 · fechada")
        self.assertContains(response, "Rodada 2")
        self.assertNotContains(response, "Rodada 3")

    def test_painel_exibe_evento_da_rodada_ativa(self):
        jogo = Jogo.objects.create(nome="Jogo com evento", config=GameConfig.objects.create())
        grupo = self._create_group(3)
        grupo.jogo = jogo
        grupo.save(update_fields=["jogo"])
        Rodada.objects.create(
            jogo=jogo, numero=1, fechada=False, fim=timezone.now() + timedelta(days=1)
        )
        evento = Evento.objects.create(
            nome="Demanda aquecida",
            frase_indicativa="As praças registram procura acima do esperado.",
            descricao="A demanda cresce nesta rodada.",
            tipo="demanda",
            impacto_percentual=10,
            probabilidade=100,
        )
        EventoRodada.objects.create(jogo=jogo, rodada=1, evento=evento)
        self.client.login(username="view0@example.com", password="secret")

        response = self.client.get(reverse("painel_grupo"))

        # O 8.4 quer o evento chegando como noticia: a frase indicativa e a
        # manchete, o nome vem junto do efeito.
        self.assertContains(response, "As praças registram procura acima do esperado.")
        self.assertContains(response, "A demanda cresce nesta rodada.")
        # Uma vez so: o boletim do cabecalho anuncia, a pagina nao repete.
        self.assertContains(response, "Demanda aquecida", count=1)

    def test_ranking_and_relatorios_access_for_authenticated_user(self):
        self.client.login(username="view0@example.com", password="secret")
        response_ranking = self.client.get(reverse("ranking"))
        response_relatorios = self.client.get(reverse("relatorios"))
        self.assertEqual(response_ranking.status_code, 200)
        self.assertEqual(response_relatorios.status_code, 200)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class LoginRedirectTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            email_usuario="admin@example.com",
            nome_usuario="Admin",
            password="pass",
            tipo_usuario="gamemaster",
        )
        self.ceo = User.objects.create_user(
            email_usuario="ceo@example.com",
            nome_usuario="CEO",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.member = User.objects.create_user(
            email_usuario="membro@example.com",
            nome_usuario="Membro",
            password="pass",
            tipo_usuario="membro_grupo",
        )

    def test_admin_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "admin@example.com", "password": "pass"},
        )
        self.assertRedirects(response, reverse("game_config"))

    def test_ceo_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "ceo@example.com", "password": "pass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("painel_grupo"))

    def test_member_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "membro@example.com", "password": "pass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("painel_grupo"))


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RegisterViewAccessTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.gm = User.objects.create_user(
            email_usuario="gm@example.com",
            nome_usuario="GM",
            password="pass",
            tipo_usuario="gamemaster",
        )
        self.ceo = User.objects.create_user(
            email_usuario="ceo2@example.com",
            nome_usuario="CEO",
            password="pass",
            tipo_usuario="lider_grupo",
        )

    def test_gamemaster_can_access(self):
        self.client.login(username="gm@example.com", password="pass")
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_non_gamemaster_forbidden(self):
        self.client.login(username="ceo2@example.com", password="pass")
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 403)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ProducaoMateriaPrimaTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.ceo = User.objects.create_user(
            email_usuario="ceo@example.com",
            nome_usuario="CEO",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.members = [
            User.objects.create_user(
                email_usuario=f"m{i}@example.com",
                nome_usuario=f"M{i}",
                password="pass",
            )
            for i in range(2)
        ]

    def _create_group(self, materia_prima):
        grupo = Grupo.objects.create(nome="G1", capital=1000, materia_prima=materia_prima)
        grupo.membros.add(self.ceo, *self.members)
        return grupo

    def test_producao_sem_materia_prima(self):
        grupo = self._create_group(0)
        self.client.login(username="ceo@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "rodada": 1,
                "descricao": "Prod",
                "quantidade": 10,
                "enviar_decisao": "",
            },
        )
        self.assertRedirects(response, reverse("painel_grupo"))


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RodadaSubmissionRulesTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.ceo = User.objects.create_user(
            email_usuario="ceo2@example.com",
            nome_usuario="CEO2",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.member = User.objects.create_user(
            email_usuario="membro2@example.com",
            nome_usuario="Membro2",
            password="pass",
            tipo_usuario="membro_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe X", capital=10000, estoque=100)
        self.grupo.membros.add(self.ceo, self.member)
        self.rodada = Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))

    def test_ceo_can_submit_once_per_round(self):
        self.client.login(username="ceo2@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_decisao": "1",
                "descricao": "Plano da rodada",
                "quantidade": 5,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decisao.objects.filter(grupo=self.grupo, rodada=1).count(), 1)

        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_decisao": "1",
                "descricao": "Tentativa duplicada",
                "quantidade": 3,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decisao.objects.filter(grupo=self.grupo, rodada=1).count(), 1)

    def test_member_cannot_submit(self):
        self.client.login(username="membro2@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_decisao": "1",
                "descricao": "Tentativa membro",
                "quantidade": 2,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Decisao.objects.filter(grupo=self.grupo, rodada=1).exists())

    def test_submission_requires_active_round(self):
        self.rodada.fim = timezone.now() - timedelta(minutes=1)
        self.rodada.save(update_fields=["fim"])

        self.client.login(username="ceo2@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_decisao": "1",
                "descricao": "Sem rodada ativa",
                "quantidade": 1,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Decisao.objects.filter(grupo=self.grupo).exists())

    def test_ceo_da_rodada_controla_submissao_e_auditoria(self):
        CEOGrupoRodada.objects.create(grupo=self.grupo, rodada=1, usuario=self.member)

        self.client.login(username="ceo2@example.com", password="pass")
        response_ceo = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_decisao": "1",
                "descricao": "Tentativa CEO antigo",
                "quantidade": 1,
            },
            follow=True,
        )
        self.assertEqual(response_ceo.status_code, 200)
        self.assertFalse(Decisao.objects.filter(grupo=self.grupo, rodada=1).exists())

        self.client.logout()
        self.client.login(username="membro2@example.com", password="pass")
        response_member = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_decisao": "1",
                "descricao": "CEO da rodada",
                "quantidade": 2,
            },
            follow=True,
        )
        self.assertEqual(response_member.status_code, 200)
        decisao = Decisao.objects.get(grupo=self.grupo, rodada=1)
        auditoria = AuditoriaSubmissaoRodada.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(auditoria.usuario, self.member)
        self.assertEqual(auditoria.decisao, decisao)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class MateriaPrimaFlowTest(TestCase):
    @staticmethod
    def estocar(grupo, produto, quantidade, rodada=1):
        """Acabado em estoque. A expedicao acontece no fechamento (11.3.b) e
        so tira do que existe -- o 13.10 admite "a venda de produtos validos
        e DISPONIVEIS"."""
        EstoqueProduto.objects.create(
            grupo=grupo, produto=produto, rodada_entrada=rodada, quantidade=quantidade
        )
        grupo.estoque = quantidade
        grupo.save(update_fields=["estoque"])

    @staticmethod
    def produzir_no_fechamento(grupo, rodada=1):
        from app.services.producao import executar_producao

        return executar_producao(grupo=grupo, rodada=rodada)

    @staticmethod
    def expedir_no_fechamento(grupo, rodada=1):
        from app.services.distribuicao_service import executar_expedicao

        return executar_expedicao(grupo=grupo, rodada=rodada)

    @staticmethod
    def folha(grupo):
        """Folha de pagamento da rodada, em reais.

        RN-02: todo grupo comeca o jogo com 40 maquinas e 80 funcionarios.
        14.3: cada funcionario custa R$ 1.800, "registrado como custo fixo
        operacional". Logo a folha e cobrada desde a rodada 1, independente
        de o CEO ter aberto o painel ou nao.
        """
        from app.parametros import CUSTO_OPERADOR_POR_RODADA

        operadores = sum(linha.operadores for linha in grupo.capacidades_produto.all())
        return Decimal(operadores) * CUSTO_OPERADOR_POR_RODADA

    def setUp(self):
        User = get_user_model()
        self.ceo = User.objects.create_user(
            email_usuario="ceomp@example.com",
            nome_usuario="CEO MP",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe MP", capital=500000, estoque=0)
        self.grupo.membros.add(self.ceo)
        # 7.1: Fortaleza fornece MP1. A fabrica fica em Natal (9) e a
        # distancia vem da tabela do 9.1.
        self.cidade = Cidade.objects.create(nome="Fortaleza", distancia_km=527, demanda=6000)
        self.mp1 = MateriaPrima.objects.create(codigo="MP1", nome="MP1", preco_unitario=3)
        self.mp2 = MateriaPrima.objects.create(codigo="MP2", nome="MP2", preco_unitario=5.5)
        self.produto = Produto.objects.create(codigo="A", nome="Produto A", ativo=True)
        ComposicaoProduto.objects.create(
            produto=self.produto,
            materia_prima=self.mp1,
            quantidade_por_unidade=2,
        )
        ComposicaoProduto.objects.create(
            produto=self.produto,
            materia_prima=self.mp2,
            quantidade_por_unidade=1,
        )

    def test_capacidade_por_produto_e_criada_automaticamente(self):
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.client.login(username="ceomp@example.com", password="pass")
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            CapacidadeProdutoGrupo.objects.filter(grupo=self.grupo, produto=self.produto).exists()
        )

    def test_producao_acima_da_linha_e_aparada_no_fechamento(self):
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.produto.tempo_producao_min = 100
        self.produto.save(update_fields=["tempo_producao_min"])
        CapacidadeProdutoGrupo.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            maquinas=1,
            operadores=2,
            minutos_por_maquina=400,
        )
        EstoqueMateriaPrima.objects.create(grupo=self.grupo, materia_prima=self.mp1, quantidade_kg=500)
        EstoqueMateriaPrima.objects.create(grupo=self.grupo, materia_prima=self.mp2, quantidade_kg=500)

        self.client.login(username="ceomp@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_producao": "1",
                "produto": self.produto.id,
                "quantidade_planejada": 5,
            },
            follow=True,
        )
        # RN-05: acima do limite o sistema "ajusta automaticamente, com alerta
        # ao CEO"; o 13.11 manda produzir o que o tempo permitir. A linha tem
        # 400 min e o produto leva 100, entao saem 4 das 5 pedidas.
        self.assertEqual(response.status_code, 200)
        self.assertIn("comporta 4 de 4 un", response.content.decode())
        self.produzir_no_fechamento(self.grupo)
        ordem = Producao.objects.get(grupo=self.grupo, produto=self.produto, rodada=1)
        self.assertEqual(ordem.quantidade_planejada, 5)
        self.assertEqual(ordem.quantidade_produzida, 4)

    def test_capacidade_de_a_nao_consume_linha_de_b(self):
        produto_b = Produto.objects.create(
            codigo="B",
            nome="Produto B",
            ativo=True,
            tempo_producao_min=200,
        )
        ComposicaoProduto.objects.create(
            produto=produto_b,
            materia_prima=self.mp1,
            quantidade_por_unidade=1,
        )
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.produto.tempo_producao_min = 100
        self.produto.save(update_fields=["tempo_producao_min"])
        CapacidadeProdutoGrupo.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            maquinas=1,
            operadores=2,
            minutos_por_maquina=400,
        )
        CapacidadeProdutoGrupo.objects.create(
            grupo=self.grupo,
            produto=produto_b,
            maquinas=1,
            operadores=2,
            minutos_por_maquina=400,
        )
        EstoqueMateriaPrima.objects.create(grupo=self.grupo, materia_prima=self.mp1, quantidade_kg=500)
        EstoqueMateriaPrima.objects.create(grupo=self.grupo, materia_prima=self.mp2, quantidade_kg=500)

        self.client.login(username="ceomp@example.com", password="pass")
        response_a = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_producao": "1",
                "produto": self.produto.id,
                "quantidade_planejada": 4,
            },
            follow=True,
        )
        response_b = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_producao": "1",
                "produto": produto_b.id,
                "quantidade_planejada": 2,
            },
            follow=True,
        )

        self.assertEqual(response_a.status_code, 200)
        self.assertEqual(response_b.status_code, 200)
        # 13.11: "cada produto so pode ser produzido em sua linha" -- as duas
        # ordens cabem porque cada linha tem os seus 400 minutos.
        self.produzir_no_fechamento(self.grupo)
        self.assertTrue(
            Producao.objects.filter(grupo=self.grupo, produto=self.produto, rodada=1, quantidade_produzida=4).exists()
        )
        self.assertTrue(
            Producao.objects.filter(grupo=self.grupo, produto=produto_b, rodada=1, quantidade_produzida=2).exists()
        )

    def test_compra_mp_recebe_na_rodada_seguinte(self):
        rodada1 = Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.client.login(username="ceomp@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_compra_mp": "1",
                "materia_prima": self.mp1.id,
                "cidade_fornecedora": self.cidade.id,
                "quantidade_kg": "100",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        compra = CompraMateriaPrima.objects.get(grupo=self.grupo)
        self.assertEqual(compra.rodada_pedido, 1)
        self.assertEqual(compra.rodada_recebimento, 2)
        self.assertFalse(compra.recebida)
        self.assertFalse(
            EstoqueMateriaPrima.objects.filter(grupo=self.grupo, materia_prima=self.mp1).exists()
        )

        # 11.3.c: a entrada de MP no estoque e etapa do fechamento da rodada,
        # nao efeito colateral de abrir o painel.
        rodada1.fim = timezone.now() - timedelta(minutes=1)
        rodada1.save(update_fields=["fim"])
        Rodada.objects.create(numero=2, fim=timezone.now() + timedelta(hours=1))
        call_command("fechar_rodadas")

        compra.refresh_from_db()
        self.assertTrue(compra.recebida)
        saldo = EstoqueMateriaPrima.objects.get(grupo=self.grupo, materia_prima=self.mp1)
        self.assertEqual(float(saldo.quantidade_kg), 100.0)

    def test_producao_consume_materias_primas(self):
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        EstoqueMateriaPrima.objects.create(grupo=self.grupo, materia_prima=self.mp1, quantidade_kg=50)
        EstoqueMateriaPrima.objects.create(grupo=self.grupo, materia_prima=self.mp2, quantidade_kg=30)

        self.client.login(username="ceomp@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_producao": "1",
                "produto": self.produto.id,
                "quantidade_planejada": 10,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        # 11.3.b: quem consome a MP e o fechamento, nao a submissao.
        self.produzir_no_fechamento(self.grupo)

        saldo_mp1 = EstoqueMateriaPrima.objects.get(grupo=self.grupo, materia_prima=self.mp1)
        saldo_mp2 = EstoqueMateriaPrima.objects.get(grupo=self.grupo, materia_prima=self.mp2)
        self.assertEqual(float(saldo_mp1.quantidade_kg), 30.0)
        self.assertEqual(float(saldo_mp2.quantidade_kg), 20.0)

    def test_distribuicao_consume_estoque_produto(self):
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        EstoqueProduto.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            rodada_entrada=1,
            quantidade=20,
        )
        self.grupo.estoque = 20
        self.grupo.save(update_fields=["estoque"])

        self.client.login(username="ceomp@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_envio": "1",
                "produto": self.produto.id,
                "cidade": self.cidade.id,
                "quantidade": 5,
                "preco_unitario": "10",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        # 11.3.b: a baixa do acabado sai na expedicao, no fechamento.
        self.expedir_no_fechamento(self.grupo)
        lote = EstoqueProduto.objects.get(grupo=self.grupo, produto=self.produto, rodada_entrada=1)
        self.assertEqual(lote.quantidade, 15)

    def test_fechamento_aplica_perecibilidade_e_armazenagem(self):
        rodada = Rodada.objects.create(numero=2, fim=timezone.now() - timedelta(minutes=1))
        Decisao.objects.create(grupo=self.grupo, rodada=2, descricao="Submissao", quantidade=0)
        self.grupo.capital = 1000
        self.grupo.save(update_fields=["capital"])

        # Estoque MP para custo de armazenagem: 100 kg * 3 = 300 -> 2% = 6
        EstoqueMateriaPrima.objects.create(grupo=self.grupo, materia_prima=self.mp1, quantidade_kg=100)

        # Estoque perecivel de rodada anterior: 10 un * custo 6 = perda 60 em R2
        produto_perecivel = Produto.objects.create(
            codigo="B",
            nome="Produto B",
            perecivel=True,
            validade_rodadas=1,
            ativo=True,
        )
        ComposicaoProduto.objects.create(
            produto=produto_perecivel,
            materia_prima=self.mp1,
            quantidade_por_unidade=2,
        )
        EstoqueProduto.objects.create(
            grupo=self.grupo,
            produto=produto_perecivel,
            rodada_entrada=1,
            quantidade=10,
        )

        call_command("fechar_rodadas")

        self.grupo.refresh_from_db()
        rodada.refresh_from_db()
        self.assertTrue(rodada.fechada)
        folha = self.folha(self.grupo)
        self.assertEqual(self.grupo.capital, Decimal("934.00") - folha)
        rf = ResultadoFinanceiro.objects.get(grupo=self.grupo, rodada=2)
        self.assertEqual(rf.custos, Decimal("66.00") + folha)
        consolidado = ConsolidadoRodadaGrupo.objects.get(grupo=self.grupo, rodada=2)
        self.assertEqual(consolidado.receita_vendas, Decimal("0.00"))
        self.assertEqual(consolidado.custos_operacionais, Decimal("0.00"))
        self.assertEqual(consolidado.penalidade_sem_submissao, Decimal("0.00"))
        self.assertEqual(consolidado.perda_pereciveis, Decimal("60.00"))
        self.assertEqual(consolidado.custo_armazenagem_mp, Decimal("6.00"))
        # A folha entra na mesma linha da armazenagem de produtos -- o DRE a
        # rotula "Armazenagem de produtos e mao de obra".
        self.assertEqual(consolidado.custo_armazenagem_produtos, folha)
        self.assertEqual(consolidado.custos_totais, Decimal("66.00") + folha)
        self.assertEqual(consolidado.lucro_rodada, Decimal("-66.00") - folha)

    def test_fechamento_distribui_demanda_por_preco(self):
        grupo2 = Grupo.objects.create(nome="Equipe MP 2", capital=0, estoque=0)
        user2 = get_user_model().objects.create_user(
            email_usuario="ceomp2@example.com",
            nome_usuario="CEO MP2",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        grupo2.membros.add(user2)

        cidade = Cidade.objects.create(nome="Cidade Teste", distancia_km=100, demanda=100)
        rodada = Rodada.objects.create(numero=3, fim=timezone.now() - timedelta(minutes=1))
        Decisao.objects.create(grupo=self.grupo, rodada=3, descricao="ok", quantidade=0)
        Decisao.objects.create(grupo=grupo2, rodada=3, descricao="ok", quantidade=0)

        self.estocar(self.grupo, self.produto, 100, rodada=3)
        self.estocar(grupo2, self.produto, 100, rodada=3)
        Distribuicao.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            cidade=cidade,
            rodada=3,
            quantidade=100,
            preco_unitario=Decimal("10.00"),
            custo_transporte=Decimal("0.00"),
        )
        Distribuicao.objects.create(
            grupo=grupo2,
            produto=self.produto,
            cidade=cidade,
            rodada=3,
            quantidade=100,
            preco_unitario=Decimal("12.00"),
            custo_transporte=Decimal("0.00"),
        )

        call_command("fechar_rodadas")

        envio1 = Distribuicao.objects.get(grupo=self.grupo, rodada=3)
        envio2 = Distribuicao.objects.get(grupo=grupo2, rodada=3)
        self.assertEqual(envio1.quantidade_vendida, 67)
        self.assertEqual(envio2.quantidade_vendida, 33)
        self.assertEqual(envio1.quantidade_sobra, 33)
        self.assertEqual(envio2.quantidade_sobra, 67)
        self.assertTrue(envio1.processada)
        self.assertTrue(envio2.processada)

        self.grupo.refresh_from_db()
        grupo2.refresh_from_db()
        # 11.3.b: alem da folha, o frete tambem sai no fechamento agora --
        # antes o cenario gravava custo_transporte=0 e nada era cobrado.
        self.assertEqual(
            self.grupo.capital,
            Decimal("500670.00") - self.folha(self.grupo) - envio1.custo_transporte,
        )
        self.assertEqual(
            grupo2.capital,
            Decimal("396.00") - self.folha(grupo2) - envio2.custo_transporte,
        )

        rf1 = ResultadoFinanceiro.objects.get(grupo=self.grupo, rodada=3)
        rf2 = ResultadoFinanceiro.objects.get(grupo=grupo2, rodada=3)
        self.assertEqual(rf1.receita, Decimal("670.00"))
        self.assertEqual(rf2.receita, Decimal("396.00"))
        rodada.refresh_from_db()
        self.assertTrue(rodada.fechada)

        ms1 = MarketShareCidadeProduto.objects.get(grupo=self.grupo, cidade=cidade, produto=self.produto, rodada=3)
        ms2 = MarketShareCidadeProduto.objects.get(grupo=grupo2, cidade=cidade, produto=self.produto, rodada=3)
        self.assertEqual(ms1.quantidade_vendida, 67)
        self.assertEqual(ms2.quantidade_vendida, 33)
        self.assertEqual(ms1.market_share_percent, Decimal("67.00"))
        self.assertEqual(ms2.market_share_percent, Decimal("33.00"))

        ind1 = IndicadorRodadaGrupo.objects.get(grupo=self.grupo, rodada=3)
        ind2 = IndicadorRodadaGrupo.objects.get(grupo=grupo2, rodada=3)
        # Quem vendeu mais atende mais demanda: o eixo SD tem que refletir isso.
        # A pontuacao TOTAL nao e comparada de proposito -- o 12.1 diz que a
        # classificacao "nao se limita ao lucro ou a producao", e aqui o grupo 2
        # ganha no DF porque tem R$ 396 de ativos contra meio milhao de caixa
        # parado do grupo 1, o que dispara o ROA do 12.3.2.
        con1 = ConsolidadoRodadaGrupo.objects.get(grupo=self.grupo, rodada=3)
        con2 = ConsolidadoRodadaGrupo.objects.get(grupo=grupo2, rodada=3)
        self.assertGreater(con1.sd_percent, con2.sd_percent)
        self.assertGreater(con1.eo_percent, con2.eo_percent)
        self.assertEqual(ind1.market_share_percent, Decimal("67.00"))
        self.assertEqual(ind2.market_share_percent, Decimal("33.00"))

        cons1 = ConsolidadoRodadaGrupo.objects.get(grupo=self.grupo, rodada=3)
        cons2 = ConsolidadoRodadaGrupo.objects.get(grupo=grupo2, rodada=3)
        self.assertEqual(cons1.receita_vendas, Decimal("670.00"))
        self.assertEqual(cons2.receita_vendas, Decimal("396.00"))
        self.assertEqual(cons1.total_vendido, 67)
        self.assertEqual(cons2.total_vendido, 33)
        self.assertEqual(cons1.market_share_percent, Decimal("67.00"))
        self.assertEqual(cons2.market_share_percent, Decimal("33.00"))

    def test_demanda_cidade_produto_aplica_teto_por_produto(self):
        grupo2 = Grupo.objects.create(nome="Equipe MP 3", capital=0, estoque=0)
        user2 = get_user_model().objects.create_user(
            email_usuario="ceomp3@example.com",
            nome_usuario="CEO MP3",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        grupo2.membros.add(user2)

        cidade = Cidade.objects.create(nome="Cidade Teto", distancia_km=100, demanda=1000)
        DemandaCidadeProduto.objects.create(cidade=cidade, produto=self.produto, demanda_maxima=40)
        rodada = Rodada.objects.create(numero=4, fim=timezone.now() - timedelta(minutes=1))
        Decisao.objects.create(grupo=self.grupo, rodada=4, descricao="ok", quantidade=0)
        Decisao.objects.create(grupo=grupo2, rodada=4, descricao="ok", quantidade=0)

        self.estocar(self.grupo, self.produto, 100, rodada=4)
        self.estocar(grupo2, self.produto, 100, rodada=4)
        Distribuicao.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            cidade=cidade,
            rodada=4,
            quantidade=100,
            preco_unitario=Decimal("10.00"),
            custo_transporte=Decimal("0.00"),
        )
        Distribuicao.objects.create(
            grupo=grupo2,
            produto=self.produto,
            cidade=cidade,
            rodada=4,
            quantidade=100,
            preco_unitario=Decimal("10.00"),
            custo_transporte=Decimal("0.00"),
        )

        call_command("fechar_rodadas")

        total_vendido = (
            Distribuicao.objects.filter(cidade=cidade, rodada=4).aggregate(total=Sum("quantidade_vendida")).get("total")
            or 0
        )
        self.assertEqual(total_vendido, 40)
        rodada.refresh_from_db()
        self.assertTrue(rodada.fechada)

    def test_marketing_por_cidade_melhora_market_share(self):
        grupo2 = Grupo.objects.create(nome="Equipe MK", capital=100000, estoque=0)
        user2 = get_user_model().objects.create_user(
            email_usuario="ceomk@example.com",
            nome_usuario="CEO MK",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        grupo2.membros.add(user2)

        cidade = Cidade.objects.create(nome="Cidade Marketing", distancia_km=100, demanda=100)
        DemandaCidadeProduto.objects.create(cidade=cidade, produto=self.produto, demanda_maxima=100)
        rodada = Rodada.objects.create(numero=5, fim=timezone.now() - timedelta(minutes=1))
        Decisao.objects.create(grupo=self.grupo, rodada=5, descricao="ok", quantidade=0)
        Decisao.objects.create(grupo=grupo2, rodada=5, descricao="ok", quantidade=0)
        Investimento.objects.create(
            grupo=grupo2,
            rodada=5,
            categoria="marketing",
            cidade=cidade,
            valor=Decimal("50000.00"),
            rodada_ativacao=5,
            processado=True,
        )

        self.estocar(self.grupo, self.produto, 100, rodada=5)
        self.estocar(grupo2, self.produto, 100, rodada=5)
        Distribuicao.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            cidade=cidade,
            rodada=5,
            quantidade=100,
            preco_unitario=Decimal("10.00"),
            custo_transporte=Decimal("0.00"),
        )
        Distribuicao.objects.create(
            grupo=grupo2,
            produto=self.produto,
            cidade=cidade,
            rodada=5,
            quantidade=100,
            preco_unitario=Decimal("10.00"),
            custo_transporte=Decimal("0.00"),
        )

        call_command("fechar_rodadas")

        ms_base = MarketShareCidadeProduto.objects.get(grupo=self.grupo, cidade=cidade, produto=self.produto, rodada=5)
        ms_mk = MarketShareCidadeProduto.objects.get(grupo=grupo2, cidade=cidade, produto=self.produto, rodada=5)
        self.assertGreater(ms_mk.quantidade_vendida, ms_base.quantidade_vendida)

    def test_investimento_maquinas_e_rh_ativa_na_rodada_seguinte(self):
        produto_b = Produto.objects.create(codigo="B2", nome="Produto B2", ativo=True, tempo_producao_min=10)
        rodada = Rodada.objects.create(numero=6, fim=timezone.now() - timedelta(minutes=1))
        Decisao.objects.create(grupo=self.grupo, rodada=6, descricao="ok", quantidade=0)
        Investimento.objects.create(
            grupo=self.grupo,
            rodada=5,
            categoria="maquinas",
            produto=produto_b,
            quantidade=2,
            valor=Decimal("10000.00"),
            rodada_ativacao=6,
            processado=False,
        )
        Investimento.objects.create(
            grupo=self.grupo,
            rodada=5,
            categoria="rh",
            produto=produto_b,
            quantidade=4,
            valor=Decimal("4000.00"),
            rodada_ativacao=6,
            processado=False,
        )

        call_command("fechar_rodadas")

        capacidade = CapacidadeProdutoGrupo.objects.get(grupo=self.grupo, produto=produto_b)
        self.assertEqual(capacidade.maquinas, 2)
        self.assertEqual(capacidade.operadores, 4)
        self.assertTrue(
            Investimento.objects.filter(
                grupo=self.grupo,
                produto=produto_b,
                processado=True,
            ).count()
            >= 2
        )
        rodada.refresh_from_db()
        self.assertTrue(rodada.fechada)

    def test_aplicacao_financeira_rende_automaticamente_por_rodada(self):
        rodada = Rodada.objects.create(numero=7, fim=timezone.now() - timedelta(minutes=1))
        Decisao.objects.create(grupo=self.grupo, rodada=7, descricao="ok", quantidade=0)
        AplicacaoFinanceiraGrupo.objects.create(
            grupo=self.grupo,
            saldo_aplicado=Decimal("1000.00"),
            taxa_juros_rodada=Decimal("0.0150"),
        )

        call_command("fechar_rodadas")

        aplicacao = AplicacaoFinanceiraGrupo.objects.get(grupo=self.grupo)
        self.assertEqual(aplicacao.saldo_aplicado, Decimal("1015.00"))
        rf = ResultadoFinanceiro.objects.get(grupo=self.grupo, rodada=7)
        self.assertEqual(rf.receita, Decimal("15.00"))

    def test_compra_mp_aplica_desconto_logistico_cruzado(self):
        Rodada.objects.create(numero=8, fim=timezone.now() + timedelta(hours=1))
        EstoqueProduto.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            rodada_entrada=8,
            quantidade=50,
        )
        self.grupo.estoque = 50
        self.grupo.save(update_fields=["estoque"])
        self.client.login(username="ceomp@example.com", password="pass")

        self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_envio": "1",
                "produto": self.produto.id,
                "cidade": self.cidade.id,
                "quantidade": 10,
                "preco_unitario": "10",
            },
            follow=True,
        )
        self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_compra_mp": "1",
                "materia_prima": self.mp1.id,
                "cidade_fornecedora": self.cidade.id,
                "quantidade_kg": "10",
            },
            follow=True,
        )
        compra = CompraMateriaPrima.objects.filter(grupo=self.grupo).order_by("-id").first()
        self.assertIsNotNone(compra)
        self.assertGreater(compra.desconto_logistico, Decimal("0"))

    def test_evento_estado_bloqueia_producao(self):
        Rodada.objects.create(numero=9, fim=timezone.now() + timedelta(hours=1))
        evento = Evento.objects.create(
            nome="Bloqueio",
            tipo="custo_producao",
            modo_aplicacao="estado",
            efeito_estado="bloqueio_producao",
            duracao_rodadas=1,
            impacto_percentual=100,
            probabilidade=0.1,
        )
        EventoRodada.objects.create(rodada=9, evento=evento)
        EstoqueMateriaPrima.objects.create(grupo=self.grupo, materia_prima=self.mp1, quantidade_kg=50)
        EstoqueMateriaPrima.objects.create(grupo=self.grupo, materia_prima=self.mp2, quantidade_kg=30)
        self.client.login(username="ceomp@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_producao": "1",
                "produto": self.produto.id,
                "quantidade_planejada": 5,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Producao.objects.filter(grupo=self.grupo, rodada=9).exists())


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class EventSelectionPolicyTest(TestCase):
    """Politica de sorteio: chances iguais e cooldown (14/10/2026).

    Historico desta classe, porque ela ja mudou de lado duas vezes:

    - ate 2026-09-18 havia cooldown duro, retirado porque sobrepunha os
      pesos do 8.4 -- com ele ativo, um evento de 15% saia tanto quanto um
      de 20%, ja que excluir o concorrente pesava mais que o peso;
    - de 2026-09-18 a 14/10/2026 o evento recente so perdia peso;
    - desde 14/10/2026 os pesos sao iguais por decisao do dono do produto,
      e o cooldown voltou -- agora sem nada para distorcer, porque nao ha
      mais peso diferente a preservar.
    """

    def test_o_evento_recente_nao_se_repete(self):
        from unittest.mock import patch

        Evento.objects.all().delete()
        recente = Evento.objects.create(
            nome="Recente", tipo="demanda", impacto_percentual=5, probabilidade=100
        )
        outro = Evento.objects.create(
            nome="Outro", tipo="demanda", impacto_percentual=5, probabilidade=0
        )
        EventoRodada.objects.create(rodada=1, evento=recente)
        EventoRodada.objects.create(rodada=2, evento=recente)

        with patch("app.services.eventos.CHANCE_EVENTO_DUPLO", 0):
            escolhido = sortear_evento(3)

        # a probabilidade gravada nao salva o que esta em cooldown
        self.assertEqual(escolhido.id, outro.id)

    def test_evento_ja_sorteado_na_rodada_nao_e_re_sorteado(self):
        """A rodada tem um evento so, e ele nao muda a cada consulta."""
        e1 = Evento.objects.create(
            nome="E1", tipo="demanda", impacto_percentual=5, probabilidade=50
        )
        Evento.objects.create(
            nome="E2", tipo="demanda", impacto_percentual=5, probabilidade=50
        )
        EventoRodada.objects.create(rodada=4, evento=e1)

        for _ in range(5):
            self.assertEqual(sortear_evento(4).id, e1.id)
        self.assertEqual(EventoRodada.objects.filter(rodada=4).count(), 1)

    def test_base_sem_eventos_devolve_none(self):
        self.assertIsNone(sortear_evento(1))
