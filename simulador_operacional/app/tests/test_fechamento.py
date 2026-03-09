import csv
import tempfile
from decimal import Decimal
from pathlib import Path

from django.test import TestCase
from django.utils import timezone

from app.models import Grupo, Rodada, ResultadoFinanceiro
from app.services.fechamento import fechar_rodada


class FechamentoServiceTest(TestCase):
    def test_fechamento_aplica_penalidade_e_gera_relatorio(self):
        grupo = Grupo.objects.create(nome="G1", capital=Decimal("100"))
        Rodada.objects.create(numero=1, fim=timezone.now())

        with tempfile.TemporaryDirectory() as temp_dir:
            fechar_rodada(1, pasta_relatorios=Path(temp_dir))

            rf = ResultadoFinanceiro.objects.get(grupo=grupo, rodada=1)
            self.assertEqual(rf.penalidades, Decimal("10"))

            csv_path = Path(temp_dir) / f"grupo_{grupo.id}_rodada_1.csv"
            self.assertTrue(csv_path.exists())
            with csv_path.open() as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertTrue(rows)
            self.assertEqual(rows[0]["penalidades"], "10.0")
