"""Resultado de rodada aberta nao pode aparecer em tela.

Regra do dono do projeto: e um jogo de competicao, e saber o desempenho
alheio antes de submeter muda a decisao de quem ainda nao decidiu.

Hoje indicadores e consolidados so sao gravados no fechamento, entao o
vazamento nao acontece por acidente. Estes testes gravam a regra na tela,
para ela continuar valendo se algum codigo futuro passar a gravar antes.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import (
    ConsolidadoRodadaGrupo,
    Grupo,
    IndicadorRodadaGrupo,
    ResultadoFinanceiro,
    Rodada,
    User,
)


class SigiloDaRodadaAbertaTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email_usuario="membro@teste.com", nome_usuario="Membro", password="senha123"
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000"))
        self.grupo.membros.add(self.user)
        self.rival = Grupo.objects.create(nome="Equipe Rigel", capital=Decimal("1000"))
        self.client.force_login(self.user)

        # rodada 1 fechada, rodada 2 ainda correndo
        Rodada.objects.create(numero=1, fim=timezone.now(), fechada=True)
        Rodada.objects.create(
            numero=2, fim=timezone.now() + timezone.timedelta(hours=2), fechada=False
        )

        for rodada in (1, 2):
            for grupo in (self.grupo, self.rival):
                IndicadorRodadaGrupo.objects.create(
                    grupo=grupo, rodada=rodada, score_multicriterio=Decimal(10 * rodada)
                )
                ConsolidadoRodadaGrupo.objects.create(
                    grupo=grupo,
                    rodada=rodada,
                    receita_vendas=Decimal(1000 * rodada),
                    custos_totais=Decimal(400 * rodada),
                    lucro_rodada=Decimal(600 * rodada),
                )
                ResultadoFinanceiro.objects.create(
                    grupo=grupo,
                    rodada=rodada,
                    receita=Decimal(1000 * rodada),
                    custos=Decimal(400 * rodada),
                    lucro=Decimal(600 * rodada),
                )

    def test_ranking_usa_a_ultima_rodada_fechada_e_nao_a_aberta(self):
        resposta = self.client.get(reverse("ranking"))

        self.assertEqual(resposta.context["rodada_referencia"], 1)

    def test_relatorios_nao_trazem_a_rodada_aberta(self):
        resposta = self.client.get(reverse("relatorios"))

        rodadas = {c.rodada for c in resposta.context["consolidados"]}
        self.assertEqual(rodadas, {1}, "a rodada 2 ainda esta aberta")
        self.assertEqual({r.rodada for r in resposta.context["resultados"]}, {1})

    def test_painel_financeiro_ignora_a_rodada_aberta(self):
        resposta = self.client.get(reverse("relatorios"))

        painel = resposta.context["painel"]
        self.assertTrue(painel["tem_dados"])
        self.assertEqual(painel["kpis"]["rodada"], 1)

    def test_ao_fechar_a_rodada_os_dados_aparecem(self):
        Rodada.objects.filter(numero=2).update(fechada=True)

        resposta = self.client.get(reverse("relatorios"))

        rodadas = {c.rodada for c in resposta.context["consolidados"]}
        self.assertEqual(rodadas, {1, 2})
