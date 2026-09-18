"""Frete por viagem de caminhao.

Por que nao por quilo
---------------------
O 7.2 manda cobrar "R$ 1,50 por quilometro rodado, multiplicado pela
quantidade adquirida (em kg)". O exemplo do proprio 7.2.1 mostra o problema:
500 kg de MP3, que valem R$ 4.000, geram R$ 750.000 de frete -- 188 vezes o
valor da carga. Nenhum grupo consegue comprar materia-prima com essa regra.
A unidade foi trocada: R$ 1,50 por quilometro por VIAGEM, nao por quilo.

O que o modelo ensina
---------------------
O caminhao e indivisivel. Mandar 12.001 kg custa duas viagens, o mesmo que
mandar 24.000 kg. Isso premia quem consolida pedido e pune quem compra em
migalhas, que e exatamente a licao de planejamento de suprimentos:

    1.000 kg de MP1 de Mossoro  -> 1 viagem, 8% da capacidade paga
    12.000 kg de MP1 de Mossoro -> 1 viagem, 100% da capacidade paga

O custo do frete e o mesmo nos dois casos. O segundo grupo pagou o mesmo
para trazer doze vezes mais. A conta nao e escondida: a taxa de ocupacao
volta no resultado para o aluno ver quanto de caminhao vazio ele pagou.

O desconto de retorno (7.2.1) segue a mesma logica fisica: se o grupo ja
mandou produto para aquela cidade, o caminhao volta carregado em vez de
voltar vazio, e a viagem de volta sai mais barata.
"""

from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from app.parametros import (
    CAPACIDADE_CAMINHAO_KG,
    CUSTO_VIAGEM_POR_KM,
    DESCONTO_RETORNO_POR_KM,
)

CENTAVO = Decimal("0.01")


def viagens_necessarias(peso_kg) -> int:
    """Viagens de caminhao para levar `peso_kg`. Caminhao nao se divide.

    O teto e explicito porque `//` em Decimal trunca em direcao ao zero, e
    nao faz floor como em int -- o truque `-(-a // b)` devolve zero aqui.
    """
    peso = Decimal(str(peso_kg or 0))
    if peso <= 0:
        return 0
    return int((peso / Decimal(CAPACIDADE_CAMINHAO_KG)).to_integral_value(ROUND_CEILING))


def calcular_frete(distancia_km, peso_kg, viagens_com_retorno: int = 0) -> dict:
    """Frete de um envio, com a conta aberta para a tela mostrar.

    `viagens_com_retorno` e quantas viagens podem aproveitar carga de volta,
    limitado pelas viagens que de fato existem.
    """
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

    custo_bruto = (distancia * CUSTO_VIAGEM_POR_KM * viagens).quantize(CENTAVO, ROUND_HALF_UP)

    com_retorno = max(0, min(int(viagens_com_retorno), viagens))
    desconto = (distancia * DESCONTO_RETORNO_POR_KM * com_retorno).quantize(CENTAVO, ROUND_HALF_UP)
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


def peso_do_envio(produto, quantidade) -> Decimal:
    """Peso de um lote de produto acabado, em kg.

    O 6.1 traz a coluna "Total (kg)" por unidade -- 300 para A, 630 para B,
    650 para C -- que e a soma da composicao. E dela que sai o peso.
    """
    if produto is None or not quantidade:
        return Decimal("0")
    return produto.peso_unitario_kg * Decimal(str(quantidade))
