"""Parametros economicos da simulacao, rastreaveis a especificacao.

Cada constante aqui aponta para o trecho de `_documentacao/TXT/` que a define.
Quem mudar um valor deve mudar a referencia junto -- ou registrar a divergencia
em `docs/GUIA_IMPLEMENTACAO.md`.

Estavam duplicadas em `views.py` e em `management/commands/fechar_rodadas.py`,
com risco de divergirem em silencio.
"""

from decimal import Decimal, ROUND_HALF_UP

# RN-06: "Cada rodada representa uma semana de producao".
SEMANAS_POR_ANO = Decimal("52")
MESES_POR_ANO = Decimal("12")

# 14.2.4 e 14.3: "Salario por funcionario: R$ 1.800,00/mes".
SALARIO_OPERADOR_MENSAL = Decimal("1800")

# O jogo cobra por rodada, entao o salario mensal vai a pro-rata semanal.
CUSTO_OPERADOR_POR_RODADA = (
    SALARIO_OPERADOR_MENSAL * MESES_POR_ANO / SEMANAS_POR_ANO
).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# 11.2 e RN-04: "multado em 10% sobre o valor disponivel em caixa ao final da
# rodada anterior".
PERCENTUAL_PENALIDADE_SEM_SUBMISSAO = Decimal("0.10")

# 14.4.1: "rendimento fixo de 1,5% por rodada".
TAXA_APLICACAO_FINANCEIRA_RODADA = Decimal("0.015")

# 13.4: "Cada maquina opera 400 minutos por rodada". Decisao B3 do guia.
MINUTOS_POR_MAQUINA_RODADA = 400

# 14.3: "Cada maquina em operacao exige dois funcionarios".
OPERADORES_POR_MAQUINA = 2
