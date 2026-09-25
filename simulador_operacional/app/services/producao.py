from __future__ import annotations

from ..models import LinhaProducao


def registrar_producao(linha: LinhaProducao, quantidade: int) -> None:
    """Registra a produção realizada em uma linha específica."""
    linha.producao += quantidade
    linha.save()


def calcular_eficiencia(linha: LinhaProducao) -> float:
    """Retorna a eficiência da linha de produção."""
    if linha.capacidade == 0:
        return 0.0
    return linha.producao / linha.capacidade


def garantir_capacidades_grupo(grupo):
    """Materializa o parque inicial do grupo, se ainda nao existir.

    13.4 da o parque de largada: 15 maquinas para A, 15 para B e 10 para C,
    cada uma com 400 minutos por rodada, e o 14.3 exige dois operadores por
    maquina. Isto so cria as linhas que faltam -- nunca mexe em quem ja tem.

    Vivia em `views.garantir_capacidades_grupo` e so rodava quando alguem
    abria o painel: um grupo cujo CEO nunca entrou fechava a rodada sem
    fabrica, e o primeiro termo do EO (12.3.1) saia zerado por falta de
    cadastro, nao por ma operacao.
    """
    from ..models import CapacidadeProdutoGrupo, Produto
    from ..parametros import (
        MAQUINAS_INICIAIS_POR_PRODUTO,
        MINUTOS_POR_MAQUINA_RODADA,
        OPERADORES_POR_MAQUINA,
    )

    for produto in Produto.objects.filter(ativo=True):
        maquinas = MAQUINAS_INICIAIS_POR_PRODUTO.get(produto.codigo, 0)
        CapacidadeProdutoGrupo.objects.get_or_create(
            grupo=grupo,
            produto=produto,
            defaults={
                "maquinas": maquinas,
                "operadores": maquinas * OPERADORES_POR_MAQUINA,
                "minutos_por_maquina": MINUTOS_POR_MAQUINA_RODADA,
            },
        )


def executar_producao(*, grupo, rodada, evento=None, eventos=None):
    """13.7 -- a ordem de producao vira producao, no fechamento da rodada.

    O 11.3.b poe "Producao" entre as acoes executadas no fechamento, e o
    13.12 lista "Quantidade produzida por tipo de produto" entre os
    indicadores GERADOS pela Producao: quantidade produzida e apuracao do
    sistema, nao numero digitado pelo aluno. Por isso o painel registra
    `quantidade_planejada` (a ordem) e quem preenche `quantidade_produzida`
    e esta funcao.

    A sequencia e a do 13.7, na ordem em que ele escreve:

    1. recebimento da ordem de producao por produto;
    2. verificacao da capacidade de tempo por linha (A, B e C separadas,
       como manda o 13.11: "cada produto so pode ser produzido em sua linha");
    3. calculo da quantidade produzivel por tempo disponivel e insumos;
    4. producao parcial, se necessario, limitada pelo tempo ou insumos;
    5. transferencia dos produtos para o estoque de acabados.

    Custo: 13.9 -- "o custo corresponde ao valor das materias-primas
    consumidas" e "o tempo de maquina nao gera custo operacional adicional".
    Cobra-se o que SAIU, nunca o que foi planejado.

    Devolve (custo_total, ajustes), com `ajustes` descrevendo cada linha que
    produziu menos que o pedido -- o RN-05 exige "alerta ao CEO".
    """
    from decimal import Decimal

    from ..models import CapacidadeProdutoGrupo, Producao
    from .estoque import (
        adicionar_estoque_produto,
        consumir_materia_prima_para_producao,
        maximo_produzivel_por_insumo,
    )
    from .eventos import efeito_absoluto, fator_percentual, lista_de_eventos

    ativos = lista_de_eventos(eventos, evento)
    custo_total = Decimal("0")
    ajustes = []

    capacidades = {
        linha.produto_id: linha
        for linha in CapacidadeProdutoGrupo.objects.filter(grupo=grupo)
    }
    ordens = Producao.objects.filter(grupo=grupo, rodada=rodada).select_related("produto")

    for ordem in ordens:
        produto = ordem.produto
        if not produto or ordem.quantidade_planejada <= 0:
            continue

        # 2 e 3: teto por tempo da linha e teto por insumo em estoque.
        linha = capacidades.get(produto.id)
        if linha is None or produto.tempo_producao_min <= 0:
            teto_tempo = 0
        else:
            teto_tempo = linha.capacidade_unidades_rodada
        teto_insumo = maximo_produzivel_por_insumo(grupo, produto)

        # 4: producao parcial, limitada pelo menor dos tres.
        produzida = min(int(ordem.quantidade_planejada), teto_tempo, teto_insumo)

        if produzida < ordem.quantidade_planejada:
            limitador = "tempo de linha" if teto_tempo <= teto_insumo else "matéria-prima"
            ajustes.append(
                {
                    "produto": produto,
                    "planejada": int(ordem.quantidade_planejada),
                    "produzida": produzida,
                    "limitador": limitador,
                }
            )

        if produzida > 0:
            consumir_materia_prima_para_producao(
                grupo=grupo, produto=produto, quantidade_planejada=produzida
            )
            # 13.9: custo e o valor da MP consumida, sobre o que saiu.
            custo_unitario = produto.custo_unitario_estimado
            custo_linha = custo_unitario * Decimal(produzida)
            # A rodada pode ter mais de um evento (o sorteado e o do
            # professor): os efeitos se compoem, nao se substituem.
            custo_linha *= fator_percentual(ativos, "custo_producao")
            custo_linha += efeito_absoluto(ativos, "custo_producao")
            ordem.custo_unitario = custo_unitario
            custo_total += custo_linha
            # 5: transferencia para o estoque de acabados.
            adicionar_estoque_produto(
                grupo=grupo, produto=produto, rodada_numero=rodada, quantidade=produzida
            )
        else:
            ordem.custo_unitario = Decimal("0")
            custo_linha = Decimal("0")

        ordem.quantidade_produzida = produzida
        ordem.custo_total = custo_linha
        ordem.save(
            update_fields=["quantidade_produzida", "custo_unitario", "custo_total"]
        )

    return custo_total, ajustes
