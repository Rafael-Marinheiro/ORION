"""Entrada de materia-prima no estoque -- 7.2, 7.3 e 11.3.c.

O recebimento estava sendo materializado quando alguem ABRIA o painel:
um F5 disparava entrada de estoque, sorteio de evento e reagendamento de
entrega. O 11.3 nao deixa margem -- a "Atualizacao de Estoques (entradas e
saidas de materias-primas)" e etapa do fechamento da rodada, executada pelo
Sistema, e o quadro-resumo repete no item 7. Aqui fica a regra, chamada
pelo fechamento.
"""

from decimal import Decimal

from ..models import CompraMateriaPrima, EstoqueMateriaPrima
from .eventos import evento_estado_ativo, sortear_evento
from .retencao import aplicar_retencao_de_materia_prima


def processar_recebimentos_materia_prima(grupo, rodada_numero, rodada_evento=None):
    """Materializa as compras cujo prazo de recebimento chegou.

    `rodada_numero` e a rodada em que a MP fica disponivel: o 7.3 diz que a
    MP pedida na rodada N serve a producao de N+1, entao quem fecha a N
    libera o estoque da N+1.

    `rodada_evento` e a rodada cujo evento governa a entrega -- a que esta
    fechando. Sem ela, olhar o evento da rodada seguinte anteciparia o
    sorteio dela, que so acontece quando o professor a abre.
    """
    if rodada_evento is None:
        rodada_evento = rodada_numero

    evento_atraso = evento_estado_ativo(
        rodada_numero=rodada_evento,
        efeito_estado="atraso_mp",
        jogo_id=grupo.jogo_id,
    )
    pendentes = CompraMateriaPrima.objects.filter(
        grupo=grupo,
        recebida=False,
        rodada_recebimento__lte=rodada_numero,
    ).select_related("materia_prima")
    # 8.4: greve e enchentes retem "entregas de MP e produtos". A parcela
    # retida chega na rodada seguinte -- e quem planejou a producao contando
    # com ela descobre o buraco agora.
    evento_rodada = sortear_evento(rodada_evento, grupo.jogo_id)
    percentual_retido = int(getattr(evento_rodada, "retencao_entregas_percent", 0) or 0)

    for compra in pendentes:
        if evento_atraso:
            compra.rodada_recebimento = rodada_numero + 1
            compra.save(update_fields=["rodada_recebimento"])
            continue
        recebido = aplicar_retencao_de_materia_prima(compra, percentual_retido, rodada_numero)
        estoque, _ = EstoqueMateriaPrima.objects.get_or_create(
            grupo=grupo,
            materia_prima=compra.materia_prima,
            defaults={"quantidade_kg": Decimal("0")},
        )
        estoque.quantidade_kg += recebido
        estoque.save(update_fields=["quantidade_kg"])
        compra.recebida = True
        compra.save(update_fields=["recebida"])


def consumo_de_capacidade(grupo, materia_prima):
    """Quanto desta MP a planta consome numa rodada a plena capacidade.

    Soma, sobre as linhas do grupo, a capacidade em unidades (13.5) vezes o
    que cada unidade leva desta materia-prima (6.1). Maquina sem os dois
    operadores do 14.2.3 nao entra, porque nao produz.
    """
    from decimal import Decimal

    from ..models import CapacidadeProdutoGrupo, ComposicaoProduto

    por_unidade = {
        item.produto_id: item.quantidade_por_unidade
        for item in ComposicaoProduto.objects.filter(materia_prima=materia_prima)
    }
    if not por_unidade:
        return Decimal("0")

    total = Decimal("0")
    for linha in CapacidadeProdutoGrupo.objects.filter(
        grupo=grupo, produto_id__in=por_unidade
    ).select_related("produto"):
        total += Decimal(linha.capacidade_unidades_rodada) * por_unidade[linha.produto_id]
    return total


def limite_de_compra(grupo, materia_prima, rodada):
    """Quanto desta MP ainda cabe comprar nesta rodada (RN-05).

    O teto e por RODADA, nao por pedido: somar as compras ja feitas impede
    que tres pedidos de metade do limite furem a regra, do mesmo jeito que o
    teto de expansao do 14.2.1 conta o parque inteiro.
    """
    from decimal import Decimal

    from django.db.models import Sum

    from ..models import CompraMateriaPrima
    from ..parametros import LIMITE_COMPRA_MP

    teto = (consumo_de_capacidade(grupo, materia_prima) * LIMITE_COMPRA_MP).quantize(
        Decimal("0.01")
    )
    ja_comprado = CompraMateriaPrima.objects.filter(
        grupo=grupo, materia_prima=materia_prima, rodada_pedido=rodada
    ).aggregate(total=Sum("quantidade_kg")).get("total") or Decimal("0")
    return {
        "teto": teto,
        "comprado": ja_comprado,
        "restante": max(teto - ja_comprado, Decimal("0")),
    }
