"""Onde ficam as praças do §9.1, para o mapa do painel.

O §9 põe a fábrica em Natal-RN e lista dez cidades de venda. Aqui estão as
coordenadas reais delas e a projeção que desenha o mapa. Nenhuma regra usa
este módulo: as distâncias continuam vindo de `Cidade.distancia_km`, como o
§9.1 determina — isto aqui só desenha.

A projeção é equiretangular (o país inteiro cabe em 40 graus de longitude, e
a distorção na latitude média fica em 3%, invisível no tamanho exibido),
depois girada 22 graus no sentido horário e achatada em 0,55. O giro é o que
separa as cinco capitais do litoral nordestino, que sem ele se empilham numa
coluna de 10 px. O achatamento é a inclinação do plano: a métrica de cada
praça sobe como barra vertical a partir do ponto.

Os contornos dos estados estão em `partials/mapa_brasil.svg.html`, já
projetados por este mesmo referencial (malha estadual do IBGE, simplificada
por Douglas-Peucker a 0,7 px). Se qualquer constante daqui mudar, aquele
arquivo precisa ser gerado de novo.
"""

import math

# (latitude, longitude) das capitais.
COORDENADAS_PRACAS = {
    "Natal": (-5.79, -35.21),
    "São Paulo": (-23.55, -46.63),
    "Rio de Janeiro": (-22.91, -43.17),
    "Recife": (-8.05, -34.88),
    "João Pessoa": (-7.12, -34.86),
    "Aracaju": (-10.91, -37.07),
    "Fortaleza": (-3.73, -38.53),
    "Goiânia": (-16.68, -49.25),
    "Belém": (-1.46, -48.50),
    "Maceió": (-9.67, -35.74),
    "Porto Alegre": (-30.03, -51.23),
}

CIDADE_SEDE = "Natal"

LON_ORIGEM = -74.5
LAT_ORIGEM = 6.0
ESCALA = 10
GIRO_GRAUS = 22.0
INCLINACAO = 0.55
CENTRO = (205.0, 200.0)
ALTURA_MAXIMA = 72
LARGURA_BARRA = 7

_GIRO = math.radians(GIRO_GRAUS)


def projetar(latitude, longitude):
    """Grau para pixel do plano inclinado do mapa."""
    x = (longitude - LON_ORIGEM) * ESCALA
    y = (LAT_ORIGEM - latitude) * ESCALA
    dx, dy = x - CENTRO[0], y - CENTRO[1]
    girado_x = CENTRO[0] + dx * math.cos(_GIRO) - dy * math.sin(_GIRO)
    girado_y = CENTRO[1] + dx * math.sin(_GIRO) + dy * math.cos(_GIRO)
    return round(girado_x, 1), round(girado_y * INCLINACAO, 1)


def ponto_da_praca(nome):
    """Coordenada da praça, ou None se a cidade não é do §9.1.

    O professor pode cadastrar outras cidades; elas continuam na lista
    abaixo do mapa, só não ganham posição geográfica.
    """
    coordenada = COORDENADAS_PRACAS.get(nome)
    return projetar(*coordenada) if coordenada else None


def _nivel(percentual):
    if percentual >= 75:
        return "alto"
    if percentual >= 40:
        return "medio"
    return "baixo"


def _afastar_rotulos(barras):
    """Sobe o rótulo que colidiria com outro já colocado.

    Mesmo girado, o mapa junta Recife, João Pessoa e Maceió a poucos pixels
    um do outro. Um nome por cima do outro não se lê.
    """
    colocados = []
    for barra in sorted(barras, key=lambda b: b["x"]):
        largura = (len(barra["nome"]) + 5) * 4.4
        while any(
            abs(barra["rotulo_x"] - outro_x) < (largura + outra_largura) / 2
            and abs(barra["rotulo_y"] - outro_y) < 13
            for outro_x, outro_y, outra_largura in colocados
        ):
            barra["rotulo_y"] = round(barra["rotulo_y"] - 13, 1)
        colocados.append((barra["rotulo_x"], barra["rotulo_y"], largura))


def montar_mapa(linhas):
    """Barras do mapa a partir das linhas de `satisfacao_por_praca`.

    Devolve `(barras, fora_do_mapa)`: as praças com posição conhecida, de
    trás para a frente (a ordem em que precisam ser desenhadas para uma não
    tapar a outra), e os nomes das que ficaram sem coordenada.
    """
    barras = []
    fora_do_mapa = []
    for linha in linhas:
        nome = linha["cidade"].nome
        ponto = ponto_da_praca(nome)
        if not ponto:
            fora_do_mapa.append(nome)
            continue
        x, y = ponto
        percentual = float(linha["percentual"])
        altura = round(ALTURA_MAXIMA * percentual / 100, 1)
        barras.append(
            {
                "nome": nome,
                "x": x,
                "y": y,
                "esquerda": round(x - LARGURA_BARRA / 2, 1),
                "altura": altura,
                "topo": round(y - altura, 1),
                "percentual": percentual,
                "nivel": _nivel(percentual),
                "vendidas": linha["vendidas"],
                "demanda": linha["demanda"],
                "rotulo_x": x,
                "rotulo_y": round(y - altura - 7, 1),
            }
        )

    _afastar_rotulos(barras)
    for barra in barras:
        # Rotulo empurrado para cima perde a ligacao com a propria barra;
        # a linha-guia devolve.
        afastamento = barra["topo"] - 7 - barra["rotulo_y"]
        barra["guia"] = (
            f"M{barra['x']},{barra['topo'] - 3} L{barra['x']},{barra['rotulo_y'] + 2}"
            if afastamento > 1
            else ""
        )
    barras.sort(key=lambda barra: barra["y"])
    return barras, fora_do_mapa
