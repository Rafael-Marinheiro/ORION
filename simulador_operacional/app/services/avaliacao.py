# -*- coding: utf-8 -*-
"""15.4 -- Avaliacao do Simulador.

O 15.4 pede tres coisas distintas, e o sistema nao tinha nenhuma delas: o
que existia era uma caixa de sugestao livre, que nao e questionario nem
produz dado comparavel.

a) Questionario dos alunos ao fim do ciclo, "com itens em escala Likert e
   campos abertos", sobre clareza e usabilidade, relevancia do conteudo,
   aprendizados percebidos e engajamento, e sugestoes de melhoria.
b) Questionario dos docentes/moderadores: integracao com a ementa,
   efetividade no desenvolvimento de competencias, facilidade de uso e
   gestao, e observacoes sobre os grupos.
c) Relatorios de uso: numero de rodadas realizadas, nivel de participacao
   dos grupos, submissoes em tempo, consistencia nas decisoes e variacao
   entre desempenhos.

Os enunciados ficam aqui, e nao no template, porque a view, o relatorio e
os testes precisam da MESMA lista -- um item que exista so no HTML nao
entra na consolidacao, e a resposta vira dado orfao.
"""

import statistics
from decimal import Decimal

# Escala do 15.4: "itens em escala Likert". Cinco pontos, simetrica e com
# ponto neutro, que e a forma classica (Likert, 1932).
ESCALA_LIKERT = [
    (1, "Discordo totalmente"),
    (2, "Discordo"),
    (3, "Nem concordo nem discordo"),
    (4, "Concordo"),
    (5, "Concordo totalmente"),
]

# 15.4.a -- os quatro temas que o documento lista, nesta ordem.
ITENS_ALUNO = [
    ("usabilidade", "Clareza e usabilidade", [
        ("u1", "As telas do simulador são claras e fáceis de usar."),
        ("u2", "Encontrei as informações de que precisei para decidir."),
        ("u3", "O prazo e a situação da rodada ficam evidentes na tela."),
    ]),
    ("relevancia", "Relevância do conteúdo simulado", [
        ("r1", "As decisões do simulador têm relação com problemas reais de gestão."),
        ("r2", "As regras do jogo são coerentes com o conteúdo da disciplina."),
    ]),
    ("aprendizado", "Aprendizados percebidos e engajamento", [
        ("a1", "O simulador me ajudou a compreender o impacto das decisões "
               "sobre o resultado."),
        ("a2", "Passei a enxergar a relação entre produção, estoque, logística "
               "e finanças."),
        ("a3", "Mantive-me engajado ao longo das rodadas."),
        ("a4", "O trabalho em equipe foi necessário para decidir."),
    ]),
]

ABERTAS_ALUNO = [
    ("aprendeu", "O que você aprendeu que não esperava aprender?"),
    ("melhoria", "Sugestões de melhoria"),
]

# 15.4.b
ITENS_DOCENTE = [
    ("ementa", "Integração com a ementa", [
        ("e1", "O simulador se integrou à ementa da disciplina."),
        ("e2", "Consegui alinhar as rodadas ao cronograma das aulas."),
    ]),
    ("competencias", "Desenvolvimento de competências", [
        ("c1", "O simulador foi efetivo no desenvolvimento das competências "
               "pretendidas."),
        ("c2", "Os indicadores do ranking refletiram o desempenho real dos "
               "grupos."),
    ]),
    ("gestao", "Facilidade de uso e gestão", [
        ("g1", "A abertura, o acompanhamento e o fechamento das rodadas "
               "foram simples de operar."),
        ("g2", "A configuração de parâmetros e pesos atendeu ao que eu "
               "precisava ajustar."),
    ]),
]

ABERTAS_DOCENTE = [
    ("grupos", "Observações sobre o comportamento e o desempenho dos grupos"),
    ("melhoria", "Sugestões de melhoria"),
]


def blocos_do_papel(papel):
    return ITENS_DOCENTE if papel == "docente" else ITENS_ALUNO


def abertas_do_papel(papel):
    return ABERTAS_DOCENTE if papel == "docente" else ABERTAS_ALUNO


def chaves_do_papel(papel):
    return [
        chave
        for _, _, itens in blocos_do_papel(papel)
        for chave, _ in itens
    ]


def ciclo_encerrado(jogo):
    """Todas as rodadas do 5 ja fecharam?

    Mesma condicao que libera a classificacao final: o 15.4 aplica o
    questionario "ao final do ciclo do jogo".
    """
    from app.models import GameConfig, Rodada

    if jogo:
        rodadas = Rodada.objects.filter(jogo=jogo)
        numero_rodadas = jogo.config.numero_rodadas if jogo.config else 0
    else:
        rodadas = Rodada.objects.filter(jogo__isnull=True)
        config = GameConfig.objects.order_by("id").first()
        numero_rodadas = config.numero_rodadas if config else 0

    if not numero_rodadas:
        return False
    fechadas = set(rodadas.filter(fechada=True).values_list("numero", flat=True))
    return set(range(1, numero_rodadas + 1)).issubset(fechadas)


def consolidar_respostas(avaliacoes, papel):
    """Media por item e por bloco, mais a distribuicao da escala.

    Devolve o que um relatorio de pesquisa precisa: n, media e quantas
    respostas caíram em cada ponto da escala.
    """
    blocos = []
    for chave_bloco, titulo, itens in blocos_do_papel(papel):
        linhas = []
        for chave, enunciado in itens:
            notas = [
                int(a.respostas[chave])
                for a in avaliacoes
                if str(a.respostas.get(chave, "")).isdigit()
            ]
            distribuicao = [notas.count(valor) for valor, _ in ESCALA_LIKERT]
            linhas.append({
                "chave": chave,
                "enunciado": enunciado,
                "n": len(notas),
                "media": round(statistics.fmean(notas), 2) if notas else None,
                "distribuicao": distribuicao,
            })
        medias = [linha["media"] for linha in linhas if linha["media"] is not None]
        blocos.append({
            "chave": chave_bloco,
            "titulo": titulo,
            "linhas": linhas,
            "media": round(statistics.fmean(medias), 2) if medias else None,
        })
    return blocos


def comentarios(avaliacoes, papel):
    """Os campos abertos, agrupados por pergunta."""
    resultado = []
    for chave, pergunta in abertas_do_papel(papel):
        textos = [
            a.comentarios.get(chave, "").strip()
            for a in avaliacoes
            if a.comentarios.get(chave, "").strip()
        ]
        resultado.append({"chave": chave, "pergunta": pergunta, "textos": textos})
    return resultado


def indicadores_de_uso(jogo):
    """15.4.c -- os indicadores que o documento lista, nome por nome."""
    from app.models import (
        ConsolidadoRodadaGrupo,
        Decisao,
        GameConfig,
        Grupo,
        Rodada,
    )

    if jogo:
        grupos = list(Grupo.objects.filter(jogo=jogo).order_by("nome"))
        rodadas = Rodada.objects.filter(jogo=jogo)
        previstas = jogo.config.numero_rodadas if jogo.config else 0
    else:
        grupos = list(Grupo.objects.filter(jogo__isnull=True).order_by("nome"))
        rodadas = Rodada.objects.filter(jogo__isnull=True)
        config = GameConfig.objects.order_by("id").first()
        previstas = config.numero_rodadas if config else 0

    fechadas = sorted(
        rodadas.filter(fechada=True).values_list("numero", flat=True)
    )
    realizadas = len(fechadas)

    participacao = []
    for grupo in grupos:
        submetidas = set(
            Decisao.objects.filter(grupo=grupo, rodada__in=fechadas)
            .values_list("rodada", flat=True)
        )
        # "Consistencia nas decisoes": rodada submetida em que a equipe de
        # fato registrou operacao. Submeter sem decidir deixa o 11.2 repetir
        # a rodada anterior, e e o que este numero expoe.
        com_operacao = {
            numero
            for numero in submetidas
            if ConsolidadoRodadaGrupo.objects.filter(
                grupo=grupo, rodada=numero, total_ofertado__gt=0
            ).exists()
        }
        participacao.append({
            "grupo": grupo,
            "submissoes": len(submetidas),
            "rodadas": realizadas,
            "participacao_percent": (
                round(100 * len(submetidas) / realizadas, 1) if realizadas else 0
            ),
            "consistencia_percent": (
                round(100 * len(com_operacao) / len(submetidas), 1)
                if submetidas else 0
            ),
        })

    # "Variacao entre desempenhos": dispersao da pontuacao final do 12.
    finais = []
    for grupo in grupos:
        pontos = [
            float(c.score_multicriterio or 0)
            for c in ConsolidadoRodadaGrupo.objects.filter(
                grupo=grupo, rodada__in=fechadas
            )
        ]
        if pontos:
            finais.append(statistics.fmean(pontos))

    return {
        "rodadas_previstas": previstas,
        "rodadas_realizadas": realizadas,
        "grupos": len(grupos),
        "participacao": participacao,
        "submissoes_em_tempo": sum(p["submissoes"] for p in participacao),
        "submissoes_possiveis": realizadas * len(grupos),
        "desempenho_medio": round(statistics.fmean(finais), 2) if finais else None,
        "desempenho_menor": round(min(finais), 2) if finais else None,
        "desempenho_maior": round(max(finais), 2) if finais else None,
        "desempenho_desvio": (
            round(statistics.pstdev(finais), 2) if len(finais) > 1 else 0
        ),
    }
