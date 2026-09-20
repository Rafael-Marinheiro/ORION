"""Cálculos de frete previstos na documentação do simulador."""

from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from app.parametros import (
    CAPACIDADE_CAMINHAO_KG,
    CUSTO_CARGA_DESCARGA_PRODUTO,
    CUSTO_MP_POR_KM_KG,
    CUSTO_VIAGEM_PRODUTO_POR_KM,
    DESCONTO_RETORNO_POR_KM,
)

CENTAVO = Decimal("0.01")


def calcular_frete_materia_prima(distancia_km, quantidade_kg, produtos_remetidos=0) -> dict:
    """Aplica literalmente os §§7.2 e 7.2.1.

    O frete é R$ 1,50 por quilômetro e por kg adquirido. A remessa para a
    mesma cidade reduz R$ 0,50 por quilômetro e por unidade de produto, até o
    limite da quantidade adquirida.
    """
    distancia = Decimal(str(distancia_km or 0))
    quantidade = max(Decimal("0"), Decimal(str(quantidade_kg or 0)))
    limite_desconto = min(quantidade, max(Decimal("0"), Decimal(str(produtos_remetidos or 0))))
    custo_bruto = (distancia * quantidade * CUSTO_MP_POR_KM_KG).quantize(CENTAVO)
    desconto = (distancia * limite_desconto * DESCONTO_RETORNO_POR_KM).quantize(CENTAVO)
    return {
        "custo_bruto": custo_bruto,
        "desconto_retorno": min(desconto, custo_bruto),
        "custo": custo_bruto - min(desconto, custo_bruto),
    }


def viagens_necessarias(peso_kg) -> int:
    """Viagens de caminhao para levar `peso_kg`. Caminhao nao se divide.

    O teto e explicito porque `//` em Decimal trunca em direcao ao zero, e
    nao faz floor como em int -- o truque `-(-a // b)` devolve zero aqui.
    """
    peso = Decimal(str(peso_kg or 0))
    if peso <= 0:
        return 0
    return int((peso / Decimal(CAPACIDADE_CAMINHAO_KG)).to_integral_value(ROUND_CEILING))


def calcular_frete(distancia_km, peso_kg) -> dict:
    """Frete de produtos acabados, aberto para exibição na tela."""
    distancia = Decimal(str(distancia_km or 0))
    peso = Decimal(str(peso_kg or 0))
    viagens = viagens_necessarias(peso)

    if viagens == 0 or distancia <= 0:
        return {
            "peso_kg": peso,
            "viagens": viagens,
            "capacidade_paga_kg": Decimal(CAPACIDADE_CAMINHAO_KG) * viagens,
            "ocupacao_percentual": Decimal("0"),
            "custo_bruto": Decimal("0"),
            "desconto_retorno": Decimal("0"),
            "custo": Decimal("0"),
        }

    capacidade_paga = Decimal(CAPACIDADE_CAMINHAO_KG) * viagens
    ocupacao = (peso / capacidade_paga * Decimal("100")).quantize(CENTAVO, ROUND_HALF_UP)

    custo_bruto = (
        (distancia * CUSTO_VIAGEM_PRODUTO_POR_KM + CUSTO_CARGA_DESCARGA_PRODUTO)
        * viagens
    ).quantize(CENTAVO, ROUND_HALF_UP)

    return {
        "peso_kg": peso,
        "viagens": viagens,
        "capacidade_paga_kg": capacidade_paga,
        "ocupacao_percentual": ocupacao,
        "custo_bruto": custo_bruto,
        "desconto_retorno": Decimal("0"),
        "custo": custo_bruto,
    }


def peso_do_envio(produto, quantidade) -> Decimal:
    """Peso de um lote de produto acabado, em kg.

    O 6.1 traz a coluna "Total (kg)" por unidade -- 300 para A, 630 para B,
    650 para C -- que e a soma da composicao. E dela que sai o peso.
    """
    if produto is None or not quantidade:
        return Decimal("0")
    return produto.peso_unitario_kg * Decimal(str(quantidade))
