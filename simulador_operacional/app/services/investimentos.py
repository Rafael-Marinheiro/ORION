from ..models import Grupo, Investimento


def aplicar_retorno_investimentos(grupo: Grupo, rodada_atual: int) -> None:
    """Aplica os retornos dos investimentos cujo período de maturação terminou."""
    investimentos = grupo.investimentos.filter(retorno_aplicado=False)
    for investimento in investimentos:
        if investimento.rodada + investimento.tempo_maturacao <= rodada_atual:
            retorno = investimento.valor * investimento.roi
            grupo.capital += retorno
            investimento.retorno_aplicado = True
            investimento.save()
    grupo.save()
