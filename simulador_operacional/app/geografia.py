"""Posicao geografica das pracas do 9.1, para o mapa do painel.

O 9 fixa Natal-RN como sede da fabrica e lista dez cidades de venda. Aqui
ficam as coordenadas reais delas e a projecao usada para desenhar o mapa:
uma equiretangular simples, que serve porque o Brasil inteiro cabe em 40
graus de longitude e a distorcao na latitude media (-15 graus) fica em 3%.

As distancias do jogo continuam vindo de `Cidade.distancia_km`, como o 9.1
determina. Estas coordenadas so desenham -- nenhuma regra usa.

O contorno do Brasil e ESQUEMATICO: um poligono grosseiro, suficiente para
o aluno reconhecer o pais e localizar a praca. A posicao das cidades, essa
sim, e a real.
"""

# (latitude, longitude) das capitais -- Natal e a fabrica (9).
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

# Canto superior esquerdo da projecao e escala (pixels por grau).
LON_ORIGEM = -74.5
LAT_ORIGEM = 6.0
ESCALA = 10
LARGURA = 410
ALTURA = 405

_CONTORNO = [
    (4.4, -51.8), (1.8, -50.0), (-0.7, -48.5), (-2.5, -44.3), (-2.8, -41.5),
    (-3.7, -38.5), (-5.8, -35.2), (-8.05, -34.8), (-10.9, -37.0),
    (-13.0, -38.5), (-14.8, -39.0), (-18.0, -39.7), (-20.3, -40.3),
    (-23.0, -43.2), (-23.9, -46.3), (-25.5, -48.5), (-27.6, -48.5),
    (-30.0, -50.2), (-32.0, -52.1), (-33.7, -53.4), (-30.9, -56.0),
    (-30.2, -57.6), (-27.4, -55.6), (-25.6, -54.6), (-24.0, -54.3),
    (-22.1, -57.9), (-19.8, -58.2), (-16.3, -58.4), (-15.1, -60.4),
    (-12.5, -64.3), (-11.0, -65.3), (-10.9, -69.6), (-9.4, -72.9),
    (-7.3, -73.8), (-4.2, -70.0), (-2.2, -69.9), (0.7, -69.4), (1.9, -67.3),
    (3.9, -64.0), (5.2, -60.7), (4.5, -60.0), (1.9, -56.5), (2.2, -54.2),
]


def projetar(latitude, longitude):
    """Grau para pixel do viewBox `0 0 LARGURA ALTURA`."""
    x = (longitude - LON_ORIGEM) * ESCALA
    y = (LAT_ORIGEM - latitude) * ESCALA
    return round(x, 1), round(y, 1)


def contorno_do_brasil():
    pontos = [projetar(lat, lon) for lat, lon in _CONTORNO]
    return " ".join(f"{x},{y}" for x, y in pontos)


def ponto_da_praca(nome):
    """Coordenada da praca, ou None se o professor cadastrou outra cidade."""
    coordenada = COORDENADAS_PRACAS.get(nome)
    return projetar(*coordenada) if coordenada else None
