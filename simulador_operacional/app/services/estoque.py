"""Movimentacao de estoque de materia-prima e de produto acabado.

Vivia solta em `views.py`. Saiu para ca porque o fechamento passou a
precisar das mesmas operacoes: o 11.3.b poe producao e distribuicao entre
as acoes executadas no fechamento, e o 13.7 descreve a producao terminando
em "transferencia dos produtos para o estoque de acabados".
"""

from decimal import Decimal

from django.db.models import Sum

from ..models import ComposicaoProduto, EstoqueMateriaPrima, EstoqueProduto


def atualizar_estoque_total_grupo(grupo):
    total = (
        EstoqueProduto.objects.filter(grupo=grupo)
        .aggregate(total=Sum("quantidade"))
        .get("total")
        or 0
    )
    grupo.estoque = int(total)
    grupo.save(update_fields=["estoque"])


def adicionar_estoque_produto(grupo, produto, rodada_numero, quantidade):
    lote, _ = EstoqueProduto.objects.get_or_create(
        grupo=grupo,
        produto=produto,
        rodada_entrada=rodada_numero,
        defaults={"quantidade": 0},
    )
    lote.quantidade += int(quantidade)
    lote.save(update_fields=["quantidade"])
    atualizar_estoque_total_grupo(grupo)


def estoque_disponivel_produto(grupo, produto):
    return int(
        EstoqueProduto.objects.filter(grupo=grupo, produto=produto, quantidade__gt=0)
        .aggregate(total=Sum("quantidade"))
        .get("total")
        or 0
    )


def consumir_estoque_produto(grupo, produto, quantidade):
    """Baixa `quantidade` do acabado, do lote mais antigo para o mais novo."""
    quantidade_restante = int(quantidade)
    lotes = EstoqueProduto.objects.filter(
        grupo=grupo,
        produto=produto,
        quantidade__gt=0,
    ).order_by("rodada_entrada", "id")
    disponivel = lotes.aggregate(total=Sum("quantidade")).get("total") or 0
    if disponivel < quantidade_restante:
        return False, disponivel

    for lote in lotes:
        if quantidade_restante <= 0:
            break
        retirada = min(lote.quantidade, quantidade_restante)
        lote.quantidade -= retirada
        lote.save(update_fields=["quantidade"])
        quantidade_restante -= retirada

    atualizar_estoque_total_grupo(grupo)
    return True, disponivel


def consumir_materia_prima_para_producao(grupo, produto, quantidade_planejada, aplicar_consumo=True):
    composicoes = list(
        ComposicaoProduto.objects.filter(produto=produto).select_related("materia_prima")
    )
    if not composicoes:
        return False, "Produto sem composicao cadastrada."

    faltas = []
    consumos = []

    for item in composicoes:
        necessidade = item.quantidade_por_unidade * Decimal(quantidade_planejada)
        estoque, _ = EstoqueMateriaPrima.objects.get_or_create(
            grupo=grupo,
            materia_prima=item.materia_prima,
            defaults={"quantidade_kg": Decimal("0")},
        )
        if estoque.quantidade_kg < necessidade:
            faltas.append(
                f"{item.materia_prima.codigo}: precisa {necessidade} kg, saldo {estoque.quantidade_kg} kg"
            )
        consumos.append((estoque, necessidade))

    if faltas:
        return False, "Materia-prima insuficiente: " + "; ".join(faltas)

    if aplicar_consumo:
        for estoque, necessidade in consumos:
            estoque.quantidade_kg -= necessidade
            estoque.save(update_fields=["quantidade_kg"])

    return True, None


def maximo_produzivel_por_insumo(grupo, produto):
    """Quantas unidades o estoque de MP sustenta (13.7, 13.11).

    O 13.11 manda produzir parcialmente quando falta insumo, entao o que
    importa nao e "da ou nao da", e sim quanto da: o limite e a menor razao
    entre saldo e necessidade, sobre todas as MPs da composicao.
    """
    composicoes = list(
        ComposicaoProduto.objects.filter(produto=produto).select_related("materia_prima")
    )
    if not composicoes:
        return 0

    saldos = {
        estoque.materia_prima_id: estoque.quantidade_kg
        for estoque in EstoqueMateriaPrima.objects.filter(grupo=grupo)
    }
    limites = []
    for item in composicoes:
        por_unidade = item.quantidade_por_unidade
        if por_unidade <= 0:
            continue
        saldo = saldos.get(item.materia_prima_id, Decimal("0"))
        limites.append(int(saldo // por_unidade))
    return min(limites) if limites else 0
