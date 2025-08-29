from decimal import Decimal

from ..models import Cidade


def calcular_demanda(cidade: Cidade, preco: Decimal, fator_marketing: Decimal, disponibilidade: int) -> int:
    """Calcula a demanda considerando preço, marketing e disponibilidade.

    A demanda base da cidade é ajustada pelo fator de marketing e reduzida
    proporcionalmente ao preço. O resultado é limitado pela disponibilidade
    informada e pelo campo ``limite_demanda`` da cidade, quando definido.
    """
    demanda = int(cidade.demanda * float(fator_marketing))
    if preco > 0:
        demanda = int(demanda * (Decimal("1") / preco))
    if cidade.limite_demanda:
        demanda = min(demanda, cidade.limite_demanda)
    demanda = min(demanda, disponibilidade)
    return max(demanda, 0)
