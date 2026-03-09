from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import csv

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from django.db.models import Sum

from ..models import Grupo, Decisao, Distribuicao, EventoRodada, ResultadoFinanceiro, Rodada
from .penalidade_service import aplicar_penalidade


def _consolidar_decisoes(grupo: Grupo, rodada: int, greve: bool) -> None:
    """Garante que o grupo possua uma decisao para a rodada."""
    if grupo.decisoes.filter(rodada=rodada).exists():
        return
    if greve:
        ultima = grupo.decisoes.order_by("-rodada").first()
        if ultima:
            ultima.pk = None
            ultima.rodada = rodada
            ultima.quantidade = 0
            ultima.resultado = "Decisao replicada automaticamente (greve)"
            ultima.save()
        return

    penalidade = grupo.capital * Decimal("0.10")
    aplicar_penalidade(grupo, rodada, penalidade)
    ultima = grupo.decisoes.order_by("-rodada").first()
    if ultima:
        ultima.pk = None
        ultima.rodada = rodada
        ultima.resultado = "Decisao replicada automaticamente"
        ultima.save()


def _aplicar_eventos(grupo: Grupo, perdas: list) -> None:
    """Aplica apenas perdas diretas de estoque ao grupo."""
    alterado = False
    for evento in perdas:
        perda = int(grupo.estoque * evento.impacto_percentual / 100)
        if perda:
            grupo.estoque = max(grupo.estoque - perda, 0)
            alterado = True
    if alterado:
        grupo.save(update_fields=["estoque"])


def _calcular_resumo(grupo: Grupo, rodada: int) -> dict:
    """Retorna resumo de producao, vendas e financas para o grupo."""
    envios = Distribuicao.objects.filter(grupo=grupo, rodada=rodada)
    producao = envios.aggregate(total=Sum("quantidade"))["total"] or 0
    vendas = envios.aggregate(total=Sum("quantidade_vendida"))["total"] or 0
    rf, _ = ResultadoFinanceiro.objects.get_or_create(grupo=grupo, rodada=rodada)
    return {
        "producao": producao,
        "vendas": vendas,
        "receita": float(rf.receita),
        "custos": float(rf.custos),
        "lucro": float(rf.lucro),
        "penalidades": float(rf.penalidades),
    }


def _gerar_relatorios(grupo: Grupo, rodada: int, dados: dict, pasta: Path) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    csv_path = pasta / f"grupo_{grupo.id}_rodada_{rodada}.csv"
    with csv_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=dados.keys())
        writer.writeheader()
        writer.writerow(dados)

    pdf_path = pasta / f"grupo_{grupo.id}_rodada_{rodada}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(50, 800, f"Relatorio Grupo {grupo.nome} - Rodada {rodada}")
    y = 760
    for campo, valor in dados.items():
        c.drawString(50, y, f"{campo.capitalize()}: {valor}")
        y -= 20
    c.save()


def fechar_rodada(rodada: int, pasta_relatorios: str | Path = "relatorios") -> None:
    """Processa o fechamento da rodada especificada."""
    eventos = [er.evento for er in EventoRodada.objects.filter(rodada=rodada)]
    greve_ativa = any(e.tipo == "greve" for e in eventos)
    perdas = [e for e in eventos if e.tipo == "perda_estoque"]

    pasta = Path(pasta_relatorios)
    for grupo in Grupo.objects.all():
        _consolidar_decisoes(grupo, rodada, greve_ativa)
        _aplicar_eventos(grupo, perdas)
        dados = _calcular_resumo(grupo, rodada)
        _gerar_relatorios(grupo, rodada, dados, pasta)

    rodada_obj = Rodada.objects.filter(numero=rodada).first()
    if rodada_obj:
        rodada_obj.fechada = True
        rodada_obj.save(update_fields=["fechada"])
