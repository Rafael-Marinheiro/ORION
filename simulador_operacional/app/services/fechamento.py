from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import csv

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from django.db.models import Sum

from ..models import (
    Grupo,
    Decisao,
    Distribuicao,
    EventoRodada,
    ResultadoFinanceiro,
    Rodada,
    Produto,
)
from .penalidade_service import aplicar_penalidade


def _consolidar_decisoes(grupo: Grupo, rodada: int, greve: bool) -> None:
    """Garante que o grupo possua uma decisão para a rodada.

    Se o grupo não enviar decisão e não houver greve, aplica penalidade
    automática de 10% sobre o capital disponível.
    """
    if grupo.decisoes.filter(rodada=rodada).exists():
        return
    if greve:
        ultima = grupo.decisoes.order_by("-rodada").first()
        if ultima:
            ultima.pk = None
            ultima.rodada = rodada
            ultima.quantidade = 0
            ultima.resultado = "Decisão replicada automaticamente (greve)"
            ultima.save()
        return
    # Sem greve aplica multa e replica decisão
    penalidade = grupo.capital * Decimal("0.10")
    aplicar_penalidade(grupo, rodada, penalidade)
    ultima = grupo.decisoes.order_by("-rodada").first()
    if ultima:
        ultima.pk = None
        ultima.rodada = rodada
        ultima.resultado = "Decisão replicada automaticamente"
        ultima.save()


def _aplicar_eventos(grupo: Grupo, rodada: int, perdas: list) -> None:
    """Aplica eventos de perda de estoque e custos de armazenagem."""
    for evento in perdas:
        perda = int(grupo.estoque * evento.impacto_percentual / 100)
        if perda:
            grupo.estoque -= perda
    if perdas:
        grupo.save(update_fields=["estoque"])

    produtos = Produto.objects.filter(grupo=grupo)
    removidos = 0
    for prod in produtos:
        if prod.esta_vencido():
            removidos += prod.quantidade
            prod.quantidade = 0
            prod.save()
    if removidos:
        grupo.estoque = max(grupo.estoque - removidos, 0)
        grupo.save(update_fields=["estoque"])

    custo_armazenagem = Decimal("0")
    for prod in produtos:
        custo_armazenagem += prod.custo_armazenagem()
    if custo_armazenagem:
        grupo.capital -= custo_armazenagem
        grupo.save(update_fields=["capital"])
        rf, _ = ResultadoFinanceiro.objects.get_or_create(grupo=grupo, rodada=rodada)
        rf.custos += custo_armazenagem
        rf.saldo_caixa = grupo.capital
        rf.lucro = rf.receita - rf.custos
        rf.save(update_fields=["custos", "saldo_caixa", "lucro"])


def _calcular_resumo(grupo: Grupo, rodada: int) -> dict:
    """Retorna resumo de produção, vendas e finanças para o grupo."""
    envios = Distribuicao.objects.filter(grupo=grupo, rodada=rodada)
    producao = envios.aggregate(total=Sum("quantidade"))["total"] or 0
    vendas = envios.aggregate(total=Sum("vendas_realizadas"))["total"] or 0
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
    c.drawString(50, 800, f"Relatório Grupo {grupo.nome} - Rodada {rodada}")
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
        _aplicar_eventos(grupo, rodada, perdas)
        dados = _calcular_resumo(grupo, rodada)
        _gerar_relatorios(grupo, rodada, dados, pasta)

    rodada_obj = Rodada.objects.filter(numero=rodada).first()
    if rodada_obj:
        rodada_obj.fechada = True
        rodada_obj.save(update_fields=["fechada"])
