from decimal import Decimal
from typing import Iterable, Optional

from ..models import Evento


def calcular_custo_total(quantidade: int, distancia_km: int, eventos: Optional[Iterable[Evento]] = None) -> Decimal:
    """Calcula o custo logístico total de um envio."""
    custo = Decimal(distancia_km) * Decimal(quantidade) * Decimal("0.1")
    for evento in eventos or []:
        if evento.tipo == "custo_transporte":
            custo *= Decimal(1 + evento.impacto_percentual / 100)
    return custo.quantize(Decimal("0.01"))


def calcular_demanda(demanda_base: int, fator_marketing: Decimal = Decimal("1"), eventos: Optional[Iterable[Evento]] = None) -> int:
    """Retorna a demanda ajustada por marketing e eventos."""
    demanda = int(demanda_base * fator_marketing)
    for evento in eventos or []:
        if evento.tipo == "demanda":
            demanda = int(demanda * (1 + evento.impacto_percentual / 100))
    return demanda


def calcular_preco_final(preco_unitario: Decimal, custo_logistico_unitario: Decimal = Decimal("0"), fator_marketing: Decimal = Decimal("1"), eventos: Optional[Iterable[Evento]] = None) -> Decimal:
    """Calcula o preço final de venda por unidade."""
    preco = (preco_unitario + custo_logistico_unitario) * fator_marketing
    for evento in eventos or []:
        if evento.tipo == "demanda":
            preco *= Decimal(1 + evento.impacto_percentual / 100)
    return preco.quantize(Decimal("0.01"))
