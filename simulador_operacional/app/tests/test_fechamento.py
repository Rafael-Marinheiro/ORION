import csv
from decimal import Decimal
from pathlib import Path

import pytest
from django.utils import timezone

from app.models import Grupo, Rodada, ResultadoFinanceiro
from app.services.fechamento import fechar_rodada


@pytest.mark.django_db
def test_fechamento_aplica_penalidade_e_gera_relatorio(tmp_path: Path):
    grupo = Grupo.objects.create(nome="G1", capital=Decimal("100"))
    Rodada.objects.create(numero=1, fim=timezone.now())

    fechar_rodada(1, pasta_relatorios=tmp_path)

    rf = ResultadoFinanceiro.objects.get(grupo=grupo, rodada=1)
    assert rf.penalidades == Decimal("10")

    csv_path = tmp_path / f"grupo_{grupo.id}_rodada_1.csv"
    assert csv_path.exists()
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert rows and rows[0]["penalidades"] == "10.0"
