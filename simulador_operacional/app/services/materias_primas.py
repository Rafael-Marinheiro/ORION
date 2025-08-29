from decimal import Decimal


def calcular_frete(distancia_km: int, remessa_simultanea: bool = False) -> Decimal:
    custo_km = Decimal("1.50")
    if remessa_simultanea:
        custo_km -= Decimal("0.50")
    return (Decimal(distancia_km) * custo_km).quantize(Decimal("0.01"))


def calcular_armazenagem(valor_pedido: Decimal, rodadas: int = 1) -> Decimal:
    return (valor_pedido * Decimal("0.02") * rodadas).quantize(Decimal("0.01"))


def calcular_custo_logistico(
    distancia_km: int,
    valor_pedido: Decimal,
    rodadas: int = 1,
    remessa_simultanea: bool = False,
) -> Decimal:
    frete = calcular_frete(distancia_km, remessa_simultanea)
    armazenagem = calcular_armazenagem(valor_pedido, rodadas)
    return (frete + armazenagem).quantize(Decimal("0.01"))
