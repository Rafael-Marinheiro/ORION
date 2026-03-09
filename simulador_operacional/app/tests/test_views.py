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
        self.user = User.objects.create_user(
            email_usuario="view@example.com",
            nome_usuario="Viewer",
            password="secret",
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 302)

    def test_get_logged_in(self):
        self.client.login(username="view@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 200)

    def test_ranking_and_relatorios_access_for_authenticated_user(self):
        self.client.login(username="view@example.com", password="secret")
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
        )
        self.assertRedirects(response, reverse("painel_grupo"))

    def test_member_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "membro@example.com", "password": "pass"},
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
        self.cidade = Cidade.objects.create(nome="Fortaleza", distancia_km=527, demanda=1000)
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

    def test_producao_bloqueia_quando_excede_capacidade_da_linha(self):
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
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Producao.objects.filter(grupo=self.grupo, produto=self.produto, rodada=1).exists()
        )

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

        rodada1.fim = timezone.now() - timedelta(minutes=1)
        rodada1.save(update_fields=["fim"])
        Rodada.objects.create(numero=2, fim=timezone.now() + timedelta(hours=1))
        self.client.get(reverse("painel_grupo"))

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
        self.assertEqual(self.grupo.capital, Decimal("934.00"))
        rf = ResultadoFinanceiro.objects.get(grupo=self.grupo, rodada=2)
        self.assertEqual(rf.custos, Decimal("66.00"))
        consolidado = ConsolidadoRodadaGrupo.objects.get(grupo=self.grupo, rodada=2)
        self.assertEqual(consolidado.receita_vendas, Decimal("0.00"))
        self.assertEqual(consolidado.custos_operacionais, Decimal("0.00"))
        self.assertEqual(consolidado.penalidade_sem_submissao, Decimal("0.00"))
        self.assertEqual(consolidado.perda_pereciveis, Decimal("60.00"))
        self.assertEqual(consolidado.custo_armazenagem_mp, Decimal("6.00"))
        self.assertEqual(consolidado.custo_armazenagem_produtos, Decimal("0.00"))
        self.assertEqual(consolidado.custos_totais, Decimal("66.00"))
        self.assertEqual(consolidado.lucro_rodada, Decimal("-66.00"))

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
        self.assertEqual(self.grupo.capital, Decimal("500670.00"))
        self.assertEqual(grupo2.capital, Decimal("396.00"))

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
        self.assertGreater(ind1.score_multicriterio, ind2.score_multicriterio)
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
    def test_evento_nao_repete_ultimas_duas_rodadas(self):
        e1 = Evento.objects.create(
            nome="E1",
            tipo="demanda",
            impacto_percentual=5,
            probabilidade=0.25,
        )
        e2 = Evento.objects.create(
            nome="E2",
            tipo="demanda",
            impacto_percentual=5,
            probabilidade=0.25,
        )
        e3 = Evento.objects.create(
            nome="E3",
            tipo="demanda",
            impacto_percentual=5,
            probabilidade=0.25,
        )
        e4 = Evento.objects.create(
            nome="E4",
            tipo="demanda",
            impacto_percentual=5,
            probabilidade=0.25,
        )

        EventoRodada.objects.create(rodada=1, evento=e1)
        EventoRodada.objects.create(rodada=2, evento=e2)

        def escolher_candidato(candidatos):
            ids = {c.id for c in candidatos}
            self.assertNotIn(e1.id, ids)
            self.assertNotIn(e2.id, ids)
            self.assertIn(e3.id, ids)
            self.assertIn(e4.id, ids)
            return candidatos[0]

        with patch("app.views.random.choice", side_effect=escolher_candidato):
            evento = sortear_evento(3)

        self.assertIn(evento.id, {e3.id, e4.id})

    def test_fallback_quando_pool_menor_que_cooldown(self):
        e1 = Evento.objects.create(
            nome="EF1",
            tipo="demanda",
            impacto_percentual=5,
            probabilidade=0.5,
        )
        e2 = Evento.objects.create(
            nome="EF2",
            tipo="demanda",
            impacto_percentual=5,
            probabilidade=0.5,
        )
        EventoRodada.objects.create(rodada=1, evento=e1)
        EventoRodada.objects.create(rodada=2, evento=e2)

        evento = sortear_evento(3)
        self.assertIn(evento.id, {e1.id, e2.id})
