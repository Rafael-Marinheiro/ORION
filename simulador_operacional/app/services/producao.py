from __future__ import annotations

from ..models import LinhaProducao


def registrar_producao(linha: LinhaProducao, quantidade: int) -> None:
    """Registra a produção realizada em uma linha específica."""
    linha.producao += quantidade
    linha.save()


def calcular_eficiencia(linha: LinhaProducao) -> float:
    """Retorna a eficiência da linha de produção."""
    if linha.capacidade == 0:
        return 0.0
    return linha.producao / linha.capacidade
