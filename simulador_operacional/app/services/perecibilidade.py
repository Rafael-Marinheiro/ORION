"""Aviso de perecibilidade: o que vence no fechamento desta rodada.

O 6.2 manda descartar o produto perecivel nao comercializado, sem
compensacao. O descarte ja acontecia no fechamento, mas em silencio: o aluno
so descobria a perda depois de consumada, quando nao havia mais o que fazer.

Aqui o mesmo criterio do fechamento e aplicado antes, para o grupo poder
reagir enquanto a rodada esta aberta -- que e onde a decisao ainda existe.
"""

from decimal import Decimal

from app.models import EstoqueProduto


def lote_vencido(lote, rodada):
    """Regra unica de vencimento -- 6.2, ratificada pelo Dr. Pio em 24/09/2026.

    `validade_rodadas` conta A PROPRIA rodada de producao. O produto B tem
    validade 1: "produzido e enviado na mesma rodada", e o que ficou para
    ser enviado depois ja e perda. O 6.2 diz o mesmo por escrito --
    "unidades nao comercializadas ate o encerramento da rodada sao
    descartadas automaticamente" -- e e o que da identidade ao B, que o 6.2
    descreve como producao sob demanda, em oposicao ao A, de "producao
    antecipada e venda futura".

    Ate 24/09/2026 a condicao era `rodada >= rodada_entrada + validade`, que
    dava ao B uma rodada de sobrevida: produzido em N, ainda vendavel em
    N+1. Duas rodadas de vida e exatamente o 13.8, que a decisao B2 tinha
    descartado em favor do 6.2 -- a decisao estava registrada e o codigo
    entregava o numero do outro documento.

    Esta funcao e o unico lugar onde a regra mora. O fechamento e o aviso
    de tela chamam daqui; enquanto eram duas copias, uma podia mudar sem a
    outra.
    """
    validade = lote.produto.validade_rodadas or 1
    return rodada >= lote.rodada_entrada + validade - 1


def lotes_a_vencer(grupo, rodada):
    """Lotes do grupo que serao descartados no fechamento de `rodada`."""
    if grupo is None or rodada is None:
        return []

    lotes = (
        EstoqueProduto.objects.filter(grupo=grupo, produto__perecivel=True, quantidade__gt=0)
        .select_related("produto")
        .order_by("produto__codigo", "rodada_entrada")
    )
    return [lote for lote in lotes if lote_vencido(lote, rodada)]


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
