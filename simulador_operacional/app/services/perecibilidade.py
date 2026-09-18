"""Aviso de perecibilidade: o que vence no fechamento desta rodada.

O 6.2 manda descartar o produto perecivel nao comercializado, sem
compensacao. O descarte ja acontecia no fechamento, mas em silencio: o aluno
so descobria a perda depois de consumada, quando nao havia mais o que fazer.

Aqui o mesmo criterio do fechamento e aplicado antes, para o grupo poder
reagir enquanto a rodada esta aberta -- que e onde a decisao ainda existe.
"""

from decimal import Decimal

from app.models import EstoqueProduto


def lotes_a_vencer(grupo, rodada):
    """Lotes do grupo que serao descartados no fechamento de `rodada`.

    Espelha a condicao usada em `fechar_rodadas.processar_perecibilidade`:
    um lote vence quando `rodada >= rodada_entrada + validade`.
    """
    if grupo is None or rodada is None:
        return []

    lotes = (
        EstoqueProduto.objects.filter(grupo=grupo, produto__perecivel=True, quantidade__gt=0)
        .select_related("produto")
        .order_by("produto__codigo", "rodada_entrada")
    )
    return [
        lote
        for lote in lotes
        if rodada >= lote.rodada_entrada + (lote.produto.validade_rodadas or 1)
    ]


def resumo_vencimento(grupo, rodada):
    """Resumo pronto para a tela, ou None quando nao ha nada a vencer."""
    lotes = lotes_a_vencer(grupo, rodada)
    if not lotes:
        return None

    quantidade = sum(lote.quantidade for lote in lotes)
    valor = sum(
        Decimal(lote.quantidade) * lote.produto.custo_unitario_estimado for lote in lotes
    )
    return {
        "lotes": lotes,
        "quantidade": quantidade,
        "valor": valor,
        "produtos": sorted({lote.produto.codigo for lote in lotes}),
    }
