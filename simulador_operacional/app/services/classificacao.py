from collections import defaultdict
from decimal import Decimal
from django.db.models import Sum

from app.models import Grupo, Distribuicao, ResultadoFinanceiro


def calcular_ranking():
    """Calcula o ranking dos grupos com base em múltiplos critérios.

    Critérios considerados:
        - Eficiência operacional (vendas realizadas / quantidade enviada)
        - Desempenho financeiro (lucro total)
        - Demanda atendida (market share médio)
        - Sustentabilidade (inverso das penalidades)

    Desempates:
        - Maior saldo de caixa final
        - Menor desperdício (quantidade não vendida)
    """
    grupos = Grupo.objects.annotate(
        desempenho_financeiro=Sum("resultados__lucro"),
        total_penalidades=Sum("resultados__penalidades"),
    )

    # Total de vendas por rodada para cálculo do market share
    totais_por_rodada = {
        d["rodada"]: d["total"]
        for d in Distribuicao.objects.values("rodada").annotate(
            total=Sum("vendas_realizadas")
        )
    }

    vendas_por_grupo = Distribuicao.objects.values("grupo_id", "rodada").annotate(
        total=Sum("vendas_realizadas"),
        quantidade=Sum("quantidade"),
    )

    shares = defaultdict(list)
    total_vendas = defaultdict(int)
    total_quantidade = defaultdict(int)
    desperdicio = defaultdict(int)

    for dado in vendas_por_grupo:
        gid = dado["grupo_id"]
        total_rodada = totais_por_rodada.get(dado["rodada"]) or 0
        share = dado["total"] / total_rodada if total_rodada else 0
        shares[gid].append(share)
        total_vendas[gid] += dado["total"]
        total_quantidade[gid] += dado["quantidade"]
        desperdicio[gid] += dado["quantidade"] - dado["total"]

    ranking = []
    for g in grupos:
        vendas = total_vendas[g.id]
        quantidade = total_quantidade[g.id]
        g.eficiencia_operacional = vendas / quantidade if quantidade else 0
        g.demanda_atendida = (
            sum(shares[g.id]) / len(shares[g.id]) if shares[g.id] else 0
        )
        ultimo_rf = g.resultados.order_by("-rodada").first()
        g.saldo_caixa_final = (
            ultimo_rf.saldo_caixa if ultimo_rf else g.capital
        )
        g.desempenho_financeiro = g.desempenho_financeiro or Decimal("0")
        penalidades = g.total_penalidades or Decimal("0")
        g.sustentabilidade = 1 / (1 + float(penalidades))
        g.desperdicio_total = desperdicio[g.id]
        ranking.append(g)

    return sorted(
        ranking,
        key=lambda g: (
            -float(g.eficiencia_operacional),
            -float(g.desempenho_financeiro),
            -float(g.demanda_atendida),
            -float(g.sustentabilidade),
            -float(g.saldo_caixa_final),
            float(g.desperdicio_total),
        ),
    )
