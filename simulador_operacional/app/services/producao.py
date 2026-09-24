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
