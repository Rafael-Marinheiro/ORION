"""Fator de influencia de marketing -- 14.1.1.

Estava implementado duas vezes, em `views.calcular_fator_marketing` e em
`fechar_rodadas.fator_marketing`, com uma curva linear que nao esta em
documento nenhum: +2% a cada R$ 10.000, teto 1,30. Na pratica o investimento
do documento (R$ 10.000) rendia 1,02 -- dois por cento de demanda a mais por
todo o orcamento de marketing, decisao que nao valia a tela em que e tomada.

A curva do 14.1.1 e logaritmica: sobe rapido no inicio e satura. Os primeiros
mil reais ja entregam 3/4 do ganho maximo, o que e exatamente a licao --
campanha pequena tem retorno alto, campanha grande tem retorno marginal.
"""

import math
from decimal import Decimal

from django.db.models import Sum

from app.parametros import GANHO_MAXIMO_MARKETING, INVESTIMENTO_MARKETING_TETO

_LOG_TETO = math.log1p(float(INVESTIMENTO_MARKETING_TETO))


def fator_de_investimento(valor):
    """Mc = 1 + 0,20 x ln(1 + Ic) / ln(1 + 10000), com Ic limitado ao teto."""
    valor = Decimal(str(valor or 0))
    if valor <= 0:
        return Decimal("1")
    valor = min(valor, INVESTIMENTO_MARKETING_TETO)
    proporcao = Decimal(str(math.log1p(float(valor)) / _LOG_TETO))
    return (Decimal("1") + GANHO_MAXIMO_MARKETING * proporcao).quantize(Decimal("0.0001"))


def fator_marketing(grupo, cidade, rodada_numero):
    """Mc do grupo naquela cidade, somando as campanhas ja ativas."""
    from app.models import Investimento

    total = (
        Investimento.objects.filter(
            grupo=grupo,
            categoria="marketing",
            cidade=cidade,
            rodada_ativacao__lte=rodada_numero,
        )
        .aggregate(total=Sum("valor"))
        .get("total")
        or Decimal("0")
    )
    return fator_de_investimento(total)
