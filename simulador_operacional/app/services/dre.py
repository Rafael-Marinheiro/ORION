"""DRE e Fluxo de Caixa por grupo e rodada -- 10.3.

O documento pede, na Tela de Relatorios Financeiros, "Demonstrativo de
Resultados (DRE)" e "Fluxo de Caixa por rodada". Os numeros ja existem no
consolidado da rodada; o que faltava era apresenta-los na forma contabil, em
que cada linha e uma deducao explicita ate o resultado.

Regra que os dois relatorios respeitam: **tudo fecha**. O DRE soma exatamente
o lucro gravado e o fluxo de caixa soma exatamente o saldo gravado. Um
relatorio didatico que nao bate nao ensina contabilidade nenhuma -- ensina a
desconfiar do relatorio.
"""

from decimal import Decimal


def montar_dre(consolidado):
    """Linhas do DRE de uma rodada, da receita ao lucro liquido."""
    deducoes = [
        ("Custos operacionais (produção e frete)", consolidado.custos_operacionais),
        ("Armazenagem de matéria-prima", consolidado.custo_armazenagem_mp),
        ("Armazenagem de produtos e mão de obra", consolidado.custo_armazenagem_produtos),
        ("Perdas de estoque (perecibilidade e quebra)", consolidado.perda_pereciveis),
        ("Penalidade por não submissão", consolidado.penalidade_sem_submissao),
    ]

    linhas = [{"rotulo": "Receita da rodada", "valor": consolidado.receita_vendas, "tipo": "receita"}]
    linhas += [
        {"rotulo": rotulo, "valor": -valor, "tipo": "deducao"}
        for rotulo, valor in deducoes
        if valor
    ]
    linhas.append(
        {"rotulo": "Lucro da rodada", "valor": consolidado.lucro_rodada, "tipo": "total"}
    )
    return linhas


def conferir_dre(consolidado):
    """Diferenca entre o que o DRE soma e o lucro gravado. Zero e o esperado."""
    soma = sum(linha["valor"] for linha in montar_dre(consolidado) if linha["tipo"] != "total")
    return soma - consolidado.lucro_rodada


def montar_fluxo_de_caixa(consolidados):
    """Movimento de caixa rodada a rodada, do saldo anterior ao saldo final.

    `outras_movimentacoes` e o residuo: compra de materia-prima, investimentos
    e aplicacoes saem do caixa durante a rodada, nao no fechamento dela. Em
    vez de sumir com essa diferenca, ela vira linha -- e justamente ela que
    mostra ao aluno para onde o dinheiro foi antes de virar receita.
    """
    fluxo = []
    saldo_anterior = None
    for consolidado in sorted(consolidados, key=lambda c: c.rodada):
        entradas = consolidado.receita_vendas
        saidas = consolidado.custos_totais
        saldo_final = consolidado.saldo_caixa
        if saldo_anterior is None:
            # primeira rodada conhecida: nao ha de onde tirar o saldo inicial
            saldo_inicial = saldo_final - entradas + saidas
        else:
            saldo_inicial = saldo_anterior
        fluxo.append(
            {
                "rodada": consolidado.rodada,
                "saldo_inicial": saldo_inicial,
                "entradas": entradas,
                "saidas": saidas,
                "outras_movimentacoes": saldo_final - saldo_inicial - entradas + saidas,
                "saldo_final": saldo_final,
            }
        )
        saldo_anterior = saldo_final
    return fluxo


def resumo_do_fluxo(fluxo):
    """Totais da serie, para o rodape da tabela."""
    if not fluxo:
        return None
    return {
        "entradas": sum((linha["entradas"] for linha in fluxo), Decimal("0")),
        "saidas": sum((linha["saidas"] for linha in fluxo), Decimal("0")),
        "outras_movimentacoes": sum(
            (linha["outras_movimentacoes"] for linha in fluxo), Decimal("0")
        ),
        "saldo_final": fluxo[-1]["saldo_final"],
    }
