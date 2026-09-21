"""Regras de investimento -- 14.2 e RN-09.

Duas restricoes da especificacao nao existiam no codigo: o teto de expansao
do parque de maquinas e o bloqueio de investimento para quem esta com o caixa
negativo ha duas rodadas. Sem elas o jogo permite dois movimentos que a aula
justamente quer punir -- crescer sem limite fisico e investir insolvente.
"""

from decimal import Decimal

from ..models import ConsolidadoRodadaGrupo, GameConfig, Grupo, Investimento
from ..parametros import (
    LIMITE_EXPANSAO_MAQUINAS,
    RODADAS_CAIXA_NEGATIVO_PARA_RESTRICAO,
)

MAQUINAS_INICIAIS_PADRAO = 40


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


def maquinas_iniciais(grupo=None):
    if grupo and grupo.jogo_id and grupo.jogo.config_id:
        return int(grupo.jogo.config.maquinas_iniciais)
    config = GameConfig.objects.order_by("id").first()
    if config and config.maquinas_iniciais:
        return int(config.maquinas_iniciais)
    return MAQUINAS_INICIAIS_PADRAO


def limite_de_expansao(grupo):
    """Quantas maquinas o grupo ainda pode comprar (14.2.1)."""
    teto = int(Decimal(maquinas_iniciais(grupo)) * LIMITE_EXPANSAO_MAQUINAS)
    ja_compradas = sum(
        investimento.quantidade
        for investimento in Investimento.objects.filter(grupo=grupo, categoria="maquinas")
    )
    return {"teto": teto, "compradas": ja_compradas, "restante": max(teto - ja_compradas, 0)}


def caixa_negativo_consecutivo(grupo):
    """Quantas das ultimas rodadas fechadas terminaram com caixa negativo."""
    saldos = (
        ConsolidadoRodadaGrupo.objects.filter(grupo=grupo)
        .order_by("-rodada")
        .values_list("saldo_caixa", flat=True)[:RODADAS_CAIXA_NEGATIVO_PARA_RESTRICAO]
    )
    consecutivas = 0
    for saldo in saldos:
        if saldo >= 0:
            break
        consecutivas += 1
    return consecutivas


def impedimento_para_investir(grupo, investimento):
    """Mensagem de bloqueio, ou None quando o investimento pode seguir.

    Resgate de aplicacao financeira nunca e bloqueado: e justamente o caminho
    de quem precisa de caixa, e RN-09 restringe investir, nao desinvestir.
    """
    if investimento.categoria == "financeiro" and investimento.operacao_financeira == "resgatar":
        return None

    rodadas = caixa_negativo_consecutivo(grupo)
    if rodadas >= RODADAS_CAIXA_NEGATIVO_PARA_RESTRICAO:
        return (
            f"Investimento bloqueado: o caixa fechou negativo nas últimas "
            f"{rodadas} rodadas (RN-09). Recupere o saldo antes de investir."
        )

    if investimento.categoria == "maquinas":
        limite = limite_de_expansao(grupo)
        if investimento.quantidade > limite["restante"]:
            return (
                f"Limite de expansão atingido: o espaço industrial comporta no "
                f"máximo {limite['teto']} máquinas adicionais (+50% sobre as "
                f"{maquinas_iniciais(grupo)} iniciais). Já foram adquiridas "
                f"{limite['compradas']}; restam {limite['restante']}."
            )

    return None
