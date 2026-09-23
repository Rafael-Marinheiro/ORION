"""Sorteio do evento da rodada.

Estava implementado duas vezes -- em `views.sortear_evento` e dentro de
`fechar_rodadas` -- com comportamentos que ja divergiam. Fica um so.

O 8.2 define o mecanismo: um evento por rodada, sorteado pelos pesos do 8.4,
que somam 100%.

Variedade sem mentir sobre os pesos
-----------------------------------
Rodar o mesmo evento em sequencia empobrece a aula, mas bloquear o evento
recente achata as probabilidades: medido com 3 eventos de pesos 60/30/10,
um cooldown duro de 2 rodadas os transforma em 33/33/33 -- a configuracao do
professor e destruida em silencio.

Por isso o evento recente tem o peso REDUZIDO, nunca zerado. Ele continua
possivel, so fica improvavel. Com os 6 eventos do 8.4, isso da 1,2% de
repeticao consecutiva contra 16,9% sem nenhum ajuste, e no maximo 1,3 p.p.
de desvio das probabilidades do documento.
"""

import random

from app.models import Evento, EventoRodada
from app.parametros import PENALIDADE_EVENTO_RECENTE


def _filtro_do_jogo(queryset, jogo_id):
    if jogo_id:
        return queryset.filter(jogo_id=jogo_id)
    return queryset.filter(jogo__isnull=True)


def _eventos_recentes(rodada, jogo_id):
    """Evento de cada uma das rodadas anteriores que ainda penalizam."""
    alcance = max(PENALIDADE_EVENTO_RECENTE) if PENALIDADE_EVENTO_RECENTE else 0
    if alcance <= 0:
        return {}

    anteriores = _filtro_do_jogo(
        EventoRodada.objects.filter(rodada__lt=rodada, rodada__gte=rodada - alcance),
        jogo_id,
    )
    return {er.rodada: er.evento_id for er in anteriores}


def _fator_de_repeticao(evento_id, recentes, rodada):
    """Multiplicador do peso. 1 quando o evento nao saiu recentemente.

    A distancia sai da rodada corrente, nao da ultima rodada com evento:
    se houver lacuna -- rodada sem sorteio -- medir pela ultima registrada
    encurtaria a distancia e penalizaria um evento que ja e antigo.
    """
    fator = 1.0
    for rodada_passada, evento_da_rodada in recentes.items():
        if evento_da_rodada != evento_id:
            continue
        distancia = rodada - rodada_passada
        fator = min(fator, PENALIDADE_EVENTO_RECENTE.get(distancia, 1.0))
    return fator


def sortear_evento(rodada, jogo_id=None):
    """Evento da rodada, sorteado uma unica vez e reaproveitado depois.

    Devolve o evento ja sorteado se a rodada tiver um, para o sorteio nao
    mudar a cada consulta da tela.
    """
    existente = (
        _filtro_do_jogo(EventoRodada.objects.filter(rodada=rodada), jogo_id)
        .select_related("evento")
        .first()
    )
    if existente:
        return existente.evento

    candidatos = list(Evento.objects.all())
    if not candidatos:
        return None

    recentes = _eventos_recentes(rodada, jogo_id)
    pesos = [
        float(evento.probabilidade or 0) * _fator_de_repeticao(evento.id, recentes, rodada)
        for evento in candidatos
    ]
    if sum(pesos) > 0:
        escolhido = random.choices(candidatos, weights=pesos, k=1)[0]
    else:
        # base sem probabilidade configurada: nao trava o jogo
        escolhido = random.choice(candidatos)

    EventoRodada.objects.create(rodada=rodada, jogo_id=jogo_id, evento=escolhido)
    return escolhido


def evento_estado_ativo(rodada_numero, efeito_estado, jogo_id=None):
    """Evento de estado ainda vigente na rodada, se houver.

    Estava escrito duas vezes -- em `views.evento_estado_ativo` e em
    `fechar_rodadas.obter_evento_estado_ativo` -- com o mesmo corpo. Fica um
    so, pelo mesmo motivo que o sorteio ficou.
    """
    eventos_rodada = _filtro_do_jogo(
        EventoRodada.objects.filter(rodada__lte=rodada_numero), jogo_id
    ).select_related("evento")

    for evento_rodada in eventos_rodada.order_by("-rodada"):
        evento = evento_rodada.evento
        if evento.modo_aplicacao != "estado" or evento.efeito_estado != efeito_estado:
            continue
        fim_vigencia = evento_rodada.rodada + max(evento.duracao_rodadas, 1) - 1
        if rodada_numero <= fim_vigencia:
            return evento
    return None
