"""Validade do produto perecivel e o risco que ela cria -- 6.2.

Duas coisas moram aqui: a regra de vencimento que o fechamento aplica, e o
estado de risco que o painel mostra ao grupo enquanto a rodada corre.

O aviso diz que existe risco, e so. Nao calcula a perda, nao sugere a
correcao, nao aponta o produto. Rafael, 24/09/2026: "O que nao acontece na
vida real, eles como gestores devem conhecer os produtos, suas
caracteristicas, e efeitos das escolhas." As caracteristicas ficam no manual
(tela de Ajuda); a leitura do proprio estoque e do aluno.
"""

from django.db.models import Sum


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


def risco_de_perda_de_estoque(grupo, rodada):
    """True quando o grupo termina a rodada com perecivel sobrando.

    Compara, por produto perecivel, o que existira no fim da rodada --
    estoque atual mais producao planejada -- com o que foi destinado a
    envio. O que sobrar e descartado no fechamento, pelo 6.2.

    A producao planejada conta porque ela ainda nao aconteceu: o 11.3.b
    executa producao e expedicao no fechamento, entao durante a rodada o
    lote existe so como decisao. Se so olhasse o estoque, o aviso nunca
    acenderia -- o perecivel nao atravessa rodada.
    """
    from app.models import Distribuicao, EstoqueProduto, Producao

    if grupo is None or rodada is None:
        return False

    perecivel = {"produto__perecivel": True}
    planejado = _por_produto(
        Producao.objects.filter(grupo=grupo, rodada=rodada, **perecivel),
        "quantidade_planejada",
    )
    estocado = _por_produto(
        EstoqueProduto.objects.filter(grupo=grupo, quantidade__gt=0, **perecivel),
        "quantidade",
    )
    destinado = _por_produto(
        Distribuicao.objects.filter(
            grupo=grupo, rodada=rodada, expedida=False, **perecivel
        ),
        "quantidade",
    )

    for produto_id in set(planejado) | set(estocado):
        disponivel = planejado.get(produto_id, 0) + estocado.get(produto_id, 0)
        if disponivel > destinado.get(produto_id, 0):
            return True
    return False


def _por_produto(queryset, campo):
    return {
        linha["produto"]: linha["total"] or 0
        for linha in queryset.values("produto").annotate(total=Sum(campo))
    }
