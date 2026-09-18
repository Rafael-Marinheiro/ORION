"""Parametros economicos da simulacao, rastreaveis a especificacao.

Cada constante aqui aponta para o trecho de `_documentacao/TXT/` que a define.
Quem mudar um valor deve mudar a referencia junto -- ou registrar a divergencia
em `docs/GUIA_IMPLEMENTACAO.md`.

Estavam duplicadas em `views.py` e em `management/commands/fechar_rodadas.py`,
com risco de divergirem em silencio.
"""

from decimal import Decimal

# 14.2.4 e 14.3: "Salario por funcionario: R$ 1.800,00/mes".
SALARIO_OPERADOR_MENSAL = Decimal("1800")

# A rodada e o periodo de competencia da folha, e nao um numero de semanas.
#
# O RN-06 diz que a rodada "representa uma semana", mas quem define a data de
# encerramento e o professor, livremente: uma rodada pode durar uma aula, um
# dia ou uma semana de calendario. Converter o salario por tempo decorrido
# amarraria a economia do jogo ao relogio de parede, e o custo da mesma
# decisao mudaria conforme o professor mexesse no prazo. Entao cada rodada
# fecha uma folha, e o valor e o do documento, sem conversao.
CUSTO_OPERADOR_POR_RODADA = SALARIO_OPERADOR_MENSAL

# 11.2 e RN-04: "multado em 10% sobre o valor disponivel em caixa ao final da
# rodada anterior".
PERCENTUAL_PENALIDADE_SEM_SUBMISSAO = Decimal("0.10")

# 14.4.1: "rendimento fixo de 1,5% por rodada".
TAXA_APLICACAO_FINANCEIRA_RODADA = Decimal("0.015")

# 13.4: "Cada maquina opera 400 minutos por rodada". Decisao B3 do guia.
MINUTOS_POR_MAQUINA_RODADA = 400

# 14.3: "Cada maquina em operacao exige dois funcionarios".
OPERADORES_POR_MAQUINA = 2

# 9.1 nao da uma formula, da uma tabela. Dividindo demanda por populacao nas
# 10 cidades listadas, a razao fica em 0,207% em media (min 0,148%, max
# 0,241%). E esse o fator usado para derivar a demanda das pracas a partir
# da populacao, em vez de digitar numero por cidade.
FATOR_DEMANDA_POR_HABITANTE = 0.00207

# Piso de demanda por praca. Sem ele, cidade pequena arredonda para zero e
# vira um destino onde o grupo envia e nao vende nada -- mercado quebrado,
# nao mercado pequeno.
DEMANDA_MINIMA_POR_PRACA = 50
