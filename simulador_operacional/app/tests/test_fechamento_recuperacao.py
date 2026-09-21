"""Recuperação do processador automático, DOCX 11 §11.3 e runbook local."""

from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TransactionTestCase
from django.utils import timezone

from app.models import (
    AplicacaoFinanceiraGrupo, ConsolidadoRodadaGrupo, Evento, EventoRodada,
    ExecucaoJob, GameConfig, Grupo, IndicadorRodadaGrupo, Jogo,
    ResultadoFinanceiro, Rodada,
)


class FechamentoRecuperacaoTest(TransactionTestCase):
    def setUp(self):
        self.jogo = Jogo.objects.create(nome="Turma", config=GameConfig.objects.create())
        self.rodada = Rodada.objects.create(jogo=self.jogo, numero=1, fim=timezone.now())
        self.grupos = [
            Grupo.objects.create(nome=nome, jogo=self.jogo, capital=capital)
            for nome, capital in (("Vega", 1000), ("Rigel", 2000))
        ]
        Evento.objects.create(nome="Estabilidade", tipo="demanda", impacto_percentual=0)
        self.aplicacao = AplicacaoFinanceiraGrupo.objects.create(
            grupo=self.grupos[0], saldo_aplicado=Decimal("100"),
        )

    def fechar(self):
        call_command("fechar_rodadas", stdout=StringIO())

    def test_falha_desfaz_rodada_inteira_e_permite_repetir_sem_cobrar_duas_vezes(self):
        gravar = ConsolidadoRodadaGrupo.objects.update_or_create
        chamadas = 0

        def falhar_no_segundo_grupo(*args, **kwargs):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 2:
                raise RuntimeError("Falha simulada ao consolidar segundo grupo")
            return gravar(*args, **kwargs)

        with patch.object(ConsolidadoRodadaGrupo.objects, "update_or_create", side_effect=falhar_no_segundo_grupo):
            with self.assertRaisesMessage(RuntimeError, "Falha simulada"):
                self.fechar()

        self.rodada.refresh_from_db()
        self.aplicacao.refresh_from_db()
        self.assertFalse(self.rodada.fechada)
        self.assertEqual(self.aplicacao.saldo_aplicado, Decimal("100"))
        self.assertEqual(list(Grupo.objects.order_by("pk").values_list("capital", flat=True)), [1000, 2000])
        for model in (ResultadoFinanceiro, IndicadorRodadaGrupo, ConsolidadoRodadaGrupo, EventoRodada):
            self.assertFalse(model.objects.exists(), model.__name__)
        job = ExecucaoJob.objects.get()
        self.assertEqual(job.status, "falha")
        self.assertIn("Falha simulada", job.detalhes)
        self.assertIsNotNone(job.finalizado_em)

        self.fechar()
        self.rodada.refresh_from_db()
        self.aplicacao.refresh_from_db()
        self.assertTrue(self.rodada.fechada)
        self.assertEqual(self.aplicacao.saldo_aplicado, Decimal("101.50"))
        self.assertEqual(list(Grupo.objects.order_by("pk").values_list("capital", flat=True)), [900, 1800])
        self.assertEqual(ConsolidadoRodadaGrupo.objects.count(), 2)
        self.assertEqual(EventoRodada.objects.filter(jogo=self.jogo).count(), 1)
        salvos = list(ResultadoFinanceiro.objects.order_by("pk").values())
        self.fechar()
        self.assertEqual(list(ResultadoFinanceiro.objects.order_by("pk").values()), salvos)
        self.aplicacao.refresh_from_db()
        self.assertEqual(self.aplicacao.saldo_aplicado, Decimal("101.50"))

    def test_falha_em_outra_rodada_preserva_a_ja_concluida(self):
        seguinte = Rodada.objects.create(jogo=self.jogo, numero=2, fim=timezone.now())
        gravar = ConsolidadoRodadaGrupo.objects.update_or_create

        def falhar_na_segunda_rodada(*args, **kwargs):
            if kwargs["rodada"] == 2:
                raise RuntimeError("Falha simulada na rodada 2")
            return gravar(*args, **kwargs)

        with patch.object(ConsolidadoRodadaGrupo.objects, "update_or_create", side_effect=falhar_na_segunda_rodada):
            with self.assertRaises(RuntimeError):
                self.fechar()

        self.rodada.refresh_from_db()
        seguinte.refresh_from_db()
        self.assertTrue(self.rodada.fechada)
        self.assertFalse(seguinte.fechada)
        self.assertEqual(list(Grupo.objects.order_by("pk").values_list("capital", flat=True)), [900, 1800])
        self.assertFalse(ResultadoFinanceiro.objects.filter(rodada=2).exists())
        self.assertEqual(ConsolidadoRodadaGrupo.objects.filter(rodada=1).count(), 2)
