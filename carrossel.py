# -*- coding: utf-8 -*-
"""Carrossel do LinkedIn sobre o ORION. 1080x1080, ficha tecnica do produto.

Registro impessoal: descreve o sistema, nao a experiencia de constru-lo.
Cores e marca sao as do proprio produto (static/css/styles.css e
static/img/).
"""

import os
import re
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

LADO = 1080
MARGEM = 88

VOID = HexColor("#080A12")
PANEL = HexColor("#121728")
PANEL_2 = HexColor("#1A2137")
LINHA = HexColor("#283150")
INK = HexColor("#E8ECF7")
DIM = HexColor("#97A1BD")
STAR = HexColor("#8FD0FF")
GOLD = HexColor("#D9A441")
OK = HexColor("#5BE49B")
TERRA = HexColor("#1E273F")
PAREDE = HexColor("#070C17")

NEGRITO = "Helvetica-Bold"
NORMAL = "Helvetica"
MONO = "Courier-Bold"

IMG = "static/img"
SVG_MAPA = "simulador_operacional/app/templates/partials/mapa_brasil.svg.html"


# ------------------------------------------------------------- primitivas

def bloco(c, texto, x, y, fonte, tamanho, cor, entrelinha=1.34, largura=None):
    largura = largura or (LADO - 2 * MARGEM)
    c.setFillColor(cor)
    c.setFont(fonte, tamanho)
    for linha in simpleSplit(texto, fonte, tamanho, largura):
        c.drawString(x, y, linha)
        y -= tamanho * entrelinha
    return y


def moldura(c, numero, total, etiqueta):
    c.setFillColor(VOID)
    c.rect(0, 0, LADO, LADO, stroke=0, fill=1)
    c.setFillColor(STAR)
    c.rect(0, LADO - 7, LADO, 7, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.rect(0, LADO - 7, 190, 7, stroke=0, fill=1)

    c.setFillColor(STAR)
    c.setFont(NEGRITO, 19)
    c.drawString(MARGEM, LADO - 84, etiqueta.upper())

    c.setFillColor(LINHA)
    c.rect(MARGEM, 96, LADO - 2 * MARGEM, 1, stroke=0, fill=1)
    emblema = os.path.join(IMG, "orion-emblem.png")
    if os.path.exists(emblema):
        c.drawImage(ImageReader(emblema), MARGEM, 44, width=40, height=40,
                    mask="auto")
    c.setFillColor(DIM)
    c.setFont(NORMAL, 18)
    c.drawString(MARGEM + 54, 58, "ORION  ·  Simulador Gerencial Acadêmico")
    c.setFont(NEGRITO, 18)
    c.drawRightString(LADO - MARGEM, 58, "%02d / %02d" % (numero, total))


def cartao(c, x, y, largura, altura, fundo=PANEL):
    c.setFillColor(fundo)
    c.setStrokeColor(LINHA)
    c.setLineWidth(1)
    c.roundRect(x, y, largura, altura, 14, stroke=1, fill=1)


def numero_grande(c, valor, rotulo, x, y, cor=STAR, tamanho=54):
    c.setFillColor(cor)
    c.setFont(NEGRITO, tamanho)
    c.drawString(x, y, valor)
    c.setFillColor(DIM)
    c.setFont(NORMAL, 19)
    c.drawString(x, y - 30, rotulo)


def lista(c, itens, x, y, tamanho=26, gap=16, cor_marca=STAR, largura=None):
    largura = largura or (LADO - 2 * MARGEM - 30)
    for item in itens:
        c.setFillColor(cor_marca)
        c.circle(x + 6, y + tamanho * 0.33, 4.5, stroke=0, fill=1)
        y = bloco(c, item, x + 28, y, NORMAL, tamanho, DIM,
                  largura=largura) - gap
    return y


def desenhar_mapa(c, x0, y0, largura):
    """Os contornos do proprio componente do produto, nao uma ilustracao."""
    sys.path.insert(0, "simulador_operacional")
    from app.geografia import COORDENADAS_PRACAS, projetar

    with open(SVG_MAPA, encoding="utf-8") as arquivo:
        svg = arquivo.read()
    paths = re.findall(r'\sd="(M[^"]+)"', svg)

    todos = [
        (float(px), float(py))
        for d in paths
        for px, py in re.findall(r"(-?[\d.]+)\s+(-?[\d.]+)", d)
    ]
    menor_x = min(p[0] for p in todos)
    menor_y = min(p[1] for p in todos)
    escala = largura / (max(p[0] for p in todos) - menor_x)

    def para_tela(px, py):
        return x0 + (px - menor_x) * escala, y0 - (py - menor_y) * escala

    for desloc, cor in ((8, PAREDE), (0, TERRA)):
        c.setFillColor(cor)
        c.setStrokeColor(LINHA if desloc == 0 else cor)
        c.setLineWidth(0.7)
        for d in paths:
            forma = c.beginPath()
            partiu = False
            for comando, px, py in re.findall(
                r"([ML])\s*(-?[\d.]+)[\s,]+(-?[\d.]+)", d
            ):
                tx, ty = para_tela(float(px), float(py))
                ty -= desloc
                if comando == "M":
                    if partiu:
                        forma.close()
                    forma.moveTo(tx, ty)
                    partiu = True
                else:
                    forma.lineTo(tx, ty)
            if not partiu:
                continue
            forma.close()
            c.drawPath(forma, stroke=1, fill=1)

    for lat, lon in COORDENADAS_PRACAS.values():
        tx, ty = para_tela(*projetar(lat, lon))
        c.setFillColor(STAR)
        c.rect(tx - 2.5, ty, 5, 32, stroke=0, fill=1)
        c.setFillColor(OK)
        c.circle(tx, ty, 2.6, stroke=0, fill=1)


# ----------------------------------------------------------------- slides

def slide_capa(c, n, t):
    c.setFillColor(VOID)
    c.rect(0, 0, LADO, LADO, stroke=0, fill=1)
    c.setFillColor(STAR)
    c.rect(0, LADO - 7, LADO, 7, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.rect(0, LADO - 7, 190, 7, stroke=0, fill=1)

    logo = os.path.join(IMG, "orion-logo-horizontal.png")
    if os.path.exists(logo):
        proporcao = 724.0 / 2172.0
        c.drawImage(ImageReader(logo), MARGEM, 646, width=740,
                    height=740 * proporcao, mask="auto")

    c.setFillColor(LINHA)
    c.rect(MARGEM, 596, 200, 3, stroke=0, fill=1)

    bloco(c, "Simulador de gestão operacional por rodadas para uso didático. "
             "Equipes administram uma indústria: compras, produção, "
             "distribuição, investimentos e resultado financeiro.",
          MARGEM, 534, NORMAL, 29, INK, largura=880)

    bloco(c, "Regras derivadas de especificação acadêmica. Parâmetros, pesos "
             "de avaliação e módulos configuráveis por turma.",
          MARGEM, 404, NORMAL, 25, DIM, largura=880)

    numero_grande(c, "29", "modelos de domínio", MARGEM, 264)
    numero_grande(c, "16", "módulos de serviço", MARGEM + 280, 264)
    numero_grande(c, "442", "testes", MARGEM + 560, 264)
    numero_grande(c, "10", "praças de venda", MARGEM + 760, 264)

    c.setFillColor(LINHA)
    c.rect(MARGEM, 150, LADO - 2 * MARGEM, 1, stroke=0, fill=1)
    c.setFillColor(DIM)
    c.setFont(NORMAL, 21)
    c.drawString(MARGEM, 106, "Ficha técnica  ·  arquitetura, motor de regras e evolução")
    c.setFillColor(STAR)
    c.setFont(NEGRITO, 21)
    c.drawRightString(LADO - MARGEM, 106, "deslize")


def slide_escopo(c, n, t):
    moldura(c, n, t, "escopo")
    bloco(c, "O que o sistema simula", MARGEM, 856, NEGRITO, 44, INK)

    bloco(c, "Cada equipe opera uma indústria com unidade produtiva em Natal-RN "
             "e vendas em dez praças do país. O mercado é compartilhado: a "
             "decisão de uma equipe afeta o resultado das demais.",
          MARGEM, 782, NORMAL, 28, DIM)

    y = 644
    colunas = [
        ("Compras", "insumos por fornecedor, com prazo de entrega e custo "
                    "logístico por distância"),
        ("Produção", "linhas dedicadas, capacidade limitada por máquina e "
                     "mão de obra"),
        ("Distribuição", "envio antecipado por praça; venda limitada ao que "
                         "foi enviado"),
        ("Investimentos", "marketing por praça, capacidade, pessoal e "
                          "aplicação financeira"),
        ("Financeiro", "DRE por rodada, custo de armazenagem, perdas por "
                       "perecibilidade"),
    ]
    for titulo, desc in colunas:
        c.setFillColor(STAR)
        c.setFont(NEGRITO, 27)
        c.drawString(MARGEM, y, titulo)
        bloco(c, desc, MARGEM + 250, y, NORMAL, 24, DIM,
              largura=LADO - MARGEM - 250 - MARGEM)
        y -= 86

    cartao(c, MARGEM, 138, LADO - 2 * MARGEM, 122)
    bloco(c, "Eventos de mercado atingem todas as equipes na mesma rodada, por "
             "sorteio ou por decisão do moderador.",
          MARGEM + 34, 214, NORMAL, 25, INK, largura=LADO - 2 * MARGEM - 68)


def slide_ciclo(c, n, t):
    moldura(c, n, t, "ciclo da rodada")
    bloco(c, "Prazo, submissão e fechamento automático", MARGEM, 856,
          NEGRITO, 42, INK)

    passos = [
        ("1", "Abertura", "moderador define o prazo e o evento da rodada"),
        ("2", "Decisões", "equipe registra compras, produção, envios e investimentos"),
        ("3", "Submissão", "apenas o CEO da rodada consolida e envia"),
        ("4", "Fechamento", "automático no horário-limite; edição bloqueada"),
        ("5", "Processamento", "produção, vendas, estoque, DRE e classificação"),
    ]
    y = 752
    for indice, titulo, desc in passos:
        cartao(c, MARGEM, y - 70, LADO - 2 * MARGEM, 82)
        c.setFillColor(GOLD)
        c.setFont(NEGRITO, 28)
        c.drawString(MARGEM + 32, y - 42, indice)
        c.setFillColor(INK)
        c.setFont(NEGRITO, 28)
        c.drawString(MARGEM + 74, y - 42, titulo)
        c.setFillColor(DIM)
        c.setFont(NORMAL, 22)
        c.drawRightString(LADO - MARGEM - 32, y - 41, desc)
        y -= 100

    bloco(c, "Ausência de submissão aplica penalidade de 10% sobre o caixa; a "
             "equipe assume os custos da rodada e mantém os valores anteriores. "
             "O fechamento é idempotente: reexecução não duplica resultado nem "
             "recobra armazenagem.",
          MARGEM, 216, NORMAL, 25, DIM)


def slide_arquitetura(c, n, t):
    moldura(c, n, t, "arquitetura")
    bloco(c, "Regra de negócio fora da camada web", MARGEM, 856, NEGRITO, 42, INK)

    bloco(c, "Django 4.2  ·  Django REST Framework  ·  Docker  ·  JWT  ·  cron",
          MARGEM, 790, NEGRITO, 25, STAR)

    camadas = [
        ("Interface", "35 telas server-side, design system próprio, sem SPA"),
        ("API REST", "escopo por turma, autenticação JWT, documentação OpenAPI"),
        ("Serviços", "16 módulos sem dependência de view: produção, logística, "
                     "perecibilidade, DRE, marketing, pontuação, penalidades"),
        ("Domínio", "29 modelos, do catálogo de itens ao consolidado por rodada"),
        ("Automação", "job de fechamento agendado, com registro de execução "
                      "por turma e rodada"),
    ]
    y = 730
    for titulo, desc in camadas:
        c.setFillColor(STAR)
        c.rect(MARGEM, y - 4, 4, 30, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(NEGRITO, 26)
        c.drawString(MARGEM + 22, y, titulo)
        y = bloco(c, desc, MARGEM + 22, y - 34, NORMAL, 23, DIM,
                  largura=LADO - 2 * MARGEM - 22) - 18

    cartao(c, MARGEM, 140, LADO - 2 * MARGEM, 140)
    bloco(c, "O isolamento entre serviço e view permite executar o fechamento "
             "completo de uma rodada — com dezenas de equipes — sem levantar "
             "uma requisição HTTP.",
          MARGEM + 34, 238, NORMAL, 25, INK, largura=LADO - 2 * MARGEM - 68)


def slide_classificacao(c, n, t):
    moldura(c, n, t, "motor de classificação")
    bloco(c, "Avaliação multicritério ponderada", MARGEM, 856, NEGRITO, 42, INK)
    bloco(c, "A nota final combina cinco eixos. Os pesos são reconfiguráveis "
             "por turma e por rodada, conforme o foco pedagógico.",
          MARGEM, 790, NORMAL, 27, DIM)

    eixos = [
        ("Eficiência operacional", 0.30, "produção, comercialização e perdas"),
        ("Desempenho financeiro", 0.25, "lucratividade, ROA e giro"),
        ("Satisfação da demanda", 0.20, "atendimento do mercado por praça"),
        ("Eficiência de estoques", 0.15, "giro sobre estoque médio"),
        ("Sustentabilidade", 0.10, "perdas, proximidade logística, entregas"),
    ]
    inicio = MARGEM + 330
    maxima = (LADO - MARGEM - 92) - inicio
    y = 686
    for nome, peso, desc in eixos:
        c.setFillColor(INK)
        c.setFont(NORMAL, 25)
        c.drawString(MARGEM, y, nome)
        c.setFillColor(DIM)
        c.setFont(NORMAL, 19)
        c.drawString(MARGEM, y - 26, desc)
        c.setFillColor(STAR if peso > 0.10 else GOLD)
        c.rect(inicio, y - 4, maxima * (peso / 0.30), 22, stroke=0, fill=1)
        c.setFillColor(DIM)
        c.setFont(NEGRITO, 23)
        c.drawRightString(LADO - MARGEM, y, ("%.2f" % peso).replace(".", ","))
        y -= 84

    cartao(c, MARGEM, 150, LADO - 2 * MARGEM, 148)
    bloco(c, "Desempate por eficiência operacional, satisfação da demanda, "
             "sustentabilidade e receita bruta, nessa ordem. Cada fórmula "
             "referencia a seção da especificação que a define.",
          MARGEM + 34, 252, NORMAL, 25, INK, largura=LADO - 2 * MARGEM - 68)


def slide_parametros(c, n, t):
    moldura(c, n, t, "parametrização")
    bloco(c, "Uma instalação, várias turmas", MARGEM, 856, NEGRITO, 42, INK)
    bloco(c, "Cada turma é um jogo independente, com configuração própria. "
             "Leitura e escrita são sempre escopadas pela turma em foco.",
          MARGEM, 790, NORMAL, 27, DIM)

    grupos = [
        ("Partida", "capital, estoque, máquinas por linha, força de trabalho"),
        ("Duração", "número de rodadas e prazo de cada uma"),
        ("Catálogo", "itens habilitados, composição, custos e preços de insumo"),
        ("Avaliação", "os cinco pesos, somando 1"),
        ("Módulos", "produção, distribuição e financeiro ligáveis por turma"),
        ("Eventos", "sorteio automático ou definição manual pelo moderador"),
    ]
    largura_coluna = (LADO - 2 * MARGEM - 24) / 2
    for indice, (titulo, desc) in enumerate(grupos):
        coluna, linha_n = indice % 2, indice // 2
        x = MARGEM + coluna * (largura_coluna + 24)
        y = 690 - linha_n * 150
        cartao(c, x, y - 96, largura_coluna, 118, PANEL_2)
        c.setFillColor(STAR)
        c.setFont(NEGRITO, 25)
        c.drawString(x + 26, y - 18, titulo)
        bloco(c, desc, x + 26, y - 52, NORMAL, 21, DIM,
              largura=largura_coluna - 52)

    bloco(c, "A suíte de 442 testes verifica a conformidade do cálculo com a "
             "especificação e o isolamento entre turmas.",
          MARGEM, 200, NORMAL, 25, DIM)


def slide_interface(c, n, t):
    moldura(c, n, t, "interface")
    bloco(c, "Operação offline, sem dependência externa", MARGEM, 856,
          NEGRITO, 40, INK)

    bloco(c, "A especificação exige funcionamento sem internet. Não há CDN, "
             "biblioteca de mapas nem fonte remota: todo o front-end é servido "
             "pela própria aplicação.",
          MARGEM, 786, NORMAL, 27, DIM, largura=430)

    desenhar_mapa(c, 548, 776, 444)

    lista(c, [
        "Mapa das praças em SVG gerado a partir da malha estadual do IBGE: "
        "contornos simplificados por Douglas-Peucker, projeção "
        "equirretangular com rotação e achatamento, barras por cidade.",
        "Design system próprio, tema claro e escuro, sem framework de UI.",
        "Tabelas que se convertem em cartões no celular; alvos de toque de "
        "44 px; paleta de séries validada para daltonismo.",
        "Exportação de relatórios em PDF e Excel.",
    ], MARGEM, 470, tamanho=24)


def slide_verticais(c, n, t):
    moldura(c, n, t, "evolução · verticais")
    bloco(c, "O núcleo não é específico de indústria", MARGEM, 856,
          NEGRITO, 42, INK)
    bloco(c, "Rodada com prazo, capacidade limitada, demanda por praça, "
             "perecibilidade e avaliação ponderada são abstrações genéricas. "
             "Trocar o catálogo e as fórmulas de capacidade produz outro setor.",
          MARGEM, 790, NORMAL, 26, DIM)

    colunas = [
        ("ORION Agro", GOLD, [
            "Insumo no lugar da matéria-prima: semente, fertilizante, defensivo.",
            "Ciclo de safra com janela de plantio e colheita substituindo o "
            "tempo de máquina.",
            "Evento aleatório de natureza climática: estiagem, excesso de "
            "chuva, praga.",
            "Praças como cooperativas e armazéns; perecibilidade pós-colheita "
            "já modelada.",
        ]),
        ("ORION Serviços", OK, [
            "Capacidade em horas-equipe no lugar de máquinas por linha.",
            "Hora ociosa não estoca: perecibilidade total, que o motor já trata.",
            "Deslocamento e SLA no lugar de frete por tonelada.",
            "Carteira por região no lugar de demanda por praça; margem por "
            "contrato no lugar de margem por unidade.",
        ]),
    ]
    largura_coluna = (LADO - 2 * MARGEM - 28) / 2
    for indice, (titulo, cor, itens) in enumerate(colunas):
        x = MARGEM + indice * (largura_coluna + 28)
        cartao(c, x, 190, largura_coluna, 468, PANEL_2)
        c.setFillColor(cor)
        c.rect(x, 640, largura_coluna, 4, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(NEGRITO, 30)
        c.drawString(x + 26, 596, titulo)
        lista(c, itens, x + 26, 542, tamanho=21, gap=14, cor_marca=cor,
              largura=largura_coluna - 78)


def slide_roadmap(c, n, t):
    moldura(c, n, t, "roadmap")
    bloco(c, "Em desenvolvimento", MARGEM, 856, NEGRITO, 44, INK)

    itens = [
        ("Instrumento de avaliação", "questionário de percepção de "
         "aprendizagem ao fim do ciclo, com escala Likert, para uso em "
         "pesquisa acadêmica"),
        ("Modo offline completo", "operação em laboratório sem rede, com "
         "sincronização posterior dos resultados"),
        ("Ensaio de carga", "validação do intervalo de atualização em rede "
         "institucional com turma completa simultânea"),
        ("Verticais setoriais", "agronegócio e gestão de serviços a partir "
         "do mesmo núcleo parametrizável"),
        ("Rotação de CEO por rodada", "eleição registrada pela própria "
         "equipe, hoje disponível apenas por API"),
    ]
    y = 764
    for titulo, desc in itens:
        c.setFillColor(GOLD)
        c.circle(MARGEM + 7, y + 8, 6, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(NEGRITO, 27)
        c.drawString(MARGEM + 30, y, titulo)
        y = bloco(c, desc, MARGEM + 30, y - 32, NORMAL, 22, DIM,
                  largura=LADO - 2 * MARGEM - 30) - 26


def slide_fecho(c, n, t):
    c.setFillColor(VOID)
    c.rect(0, 0, LADO, LADO, stroke=0, fill=1)
    c.setFillColor(STAR)
    c.rect(0, LADO - 7, LADO, 7, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.rect(0, LADO - 7, 190, 7, stroke=0, fill=1)

    emblema = os.path.join(IMG, "orion-emblem.png")
    if os.path.exists(emblema):
        c.drawImage(ImageReader(emblema), MARGEM, 648, width=210, height=210,
                    mask="auto")

    bloco(c, "ORION", MARGEM, 566, NEGRITO, 64, STAR)
    bloco(c, "Simulador Gerencial Acadêmico", MARGEM, 506, NORMAL, 32, INK)

    c.setFillColor(LINHA)
    c.rect(MARGEM, 452, 200, 3, stroke=0, fill=1)

    bloco(c, "Django · DRF · Docker · SQLite · reportlab · openpyxl · cron",
          MARGEM, 398, NORMAL, 25, DIM)

    cartao(c, MARGEM, 168, LADO - 2 * MARGEM, 178)
    c.setFillColor(INK)
    c.setFont(NEGRITO, 32)
    c.drawString(MARGEM + 34, 290, "Rafael Marinheiro")
    c.setFillColor(DIM)
    c.setFont(NORMAL, 25)
    c.drawString(MARGEM + 34, 248, "Engenheiro de software  ·  back-end")
    c.setFillColor(STAR)
    c.setFont(NEGRITO, 25)
    c.drawString(MARGEM + 34, 202, "Disponível para novas oportunidades")

    c.setFillColor(DIM)
    c.setFont(NORMAL, 19)
    c.drawString(MARGEM, 108, "Especificação e validação pedagógica: "
                              "Prof. Dr. Pio Marinheiro")


SLIDES = [
    slide_capa, slide_escopo, slide_ciclo, slide_arquitetura,
    slide_classificacao, slide_parametros, slide_interface, slide_verticais,
    slide_roadmap, slide_fecho,
]


def main(destino="ORION-carrossel.pdf"):
    c = canvas.Canvas(destino, pagesize=(LADO, LADO))
    c.setTitle("ORION - Simulador Gerencial Academico")
    c.setAuthor("Rafael Marinheiro")
    c.setSubject("Ficha tecnica: arquitetura, motor de regras e evolucao")
    for i, desenhar in enumerate(SLIDES, start=1):
        desenhar(c, i, len(SLIDES))
        c.showPage()
    c.save()
    print("gerado:", destino, "-", len(SLIDES), "slides")


if __name__ == "__main__":
    main()
