"""Cálculos de frete previstos na documentação do simulador."""

from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from app.parametros import (
    CAPACIDADE_CAMINHAO_KG,
    CUSTO_CARGA_DESCARGA_PRODUTO,
    CUSTO_VIAGEM_MP_POR_KM,
    CUSTO_VIAGEM_PRODUTO_POR_KM,
    DESCONTO_RETORNO_POR_KM,
)

CENTAVO = Decimal("0.01")


def calcular_frete_materia_prima(distancia_km, quantidade_kg, peso_remetido_kg=0) -> dict:
    """Frete de matéria-prima, por VIAGEM de caminhão -- §7.2 e §7.2.1.

    Os valores são os do documento: R$ 1,50 por quilômetro rodado e R$ 0,50
    de desconto por quilômetro quando o caminhão volta carregado. O que mudou
    em 24/09/2026 foi a unidade que eles multiplicam.

    Por que não por quilo
    ---------------------
    O §7.2 diz "R$ 1,50 por quilômetro rodado, multiplicado pela quantidade
    adquirida (em kg)", e o exemplo do §7.2.1 mostra aonde isso leva: 500 kg
    de MP3, que valem R$ 4.000, geram R$ 750.000 de frete -- 188 vezes a
    carga. Uma unidade do produto A pagava R$ 204.360 só de frete de insumo,
    contra o caixa inicial de R$ 1.000.000 que o §5 fixa: o capital do grupo
    comprava quatro unidades. E a mesma carga na mesma estrada custava 2.677
    vezes mais como MP do que como produto acabado, porque o §9.2a é omisso em
    valores e ali o ORION já cobrava por viagem.

    O que o modelo ensina
    ---------------------
    O caminhão é indivisível. Levar 12.001 kg custa duas viagens, o mesmo que
    levar 24.000 kg. Isso premia quem consolida pedido e pune quem compra em
    migalhas, que é a lição de planejamento de suprimentos. A ocupação volta
    no resultado para o aluno ver quanto de caminhão vazio pagou.

    O desconto do §7.2.1 é frete de retorno, que é o que ele sempre foi
    fisicamente: as viagens que levaram produto àquela cidade voltam
    carregadas com a MP em vez de voltarem vazias, limitado pelas viagens de
    produto que de fato existiram.
    """
    distancia = Decimal(str(distancia_km or 0))
    peso = max(Decimal("0"), Decimal(str(quantidade_kg or 0)))
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
    custo_bruto = (distancia * CUSTO_VIAGEM_MP_POR_KM * viagens).quantize(
        CENTAVO, ROUND_HALF_UP
    )

    com_retorno = min(viagens_necessarias(peso_remetido_kg), viagens)
    desconto = (distancia * DESCONTO_RETORNO_POR_KM * com_retorno).quantize(
        CENTAVO, ROUND_HALF_UP
    )
    desconto = min(desconto, custo_bruto)

    return {
        "peso_kg": peso,
        "viagens": viagens,
        "capacidade_paga_kg": capacidade_paga,
        "ocupacao_percentual": ocupacao,
        "custo_bruto": custo_bruto,
        "desconto_retorno": desconto,
        "custo": custo_bruto - desconto,
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
