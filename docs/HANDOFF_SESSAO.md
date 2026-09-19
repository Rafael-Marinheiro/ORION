# Handoff — continuar a implementação do ORION

> Cole o conteúdo abaixo (da linha `---` em diante) como primeira mensagem da
> nova sessão. Ele é auto-contido: não depende de nada do histórico anterior.

---

Você vai continuar a implementação do ORION, um simulador operacional
acadêmico em Django. Responda sempre em português do Brasil.

## Onde está o trabalho

O código vive em `C:\Projetos\ORION`, mas o trabalho recente está na branch
`claude/recursing-pascal-f25acd`, nos commits `01338cd`, `643804e` e
`21f4716`. Confira
que está nela antes de qualquer coisa — se abrir na `main`, você não verá nada
do que foi feito.

## Estado verificado

Em 2026-09-19 a suíte inteira rodou: **232 testes, todos OK**. Os gates de
cobertura passaram — núcleo acima de 85%, periférico em 79%. O trabalho dos
commits `01338cd`, `643804e` e `21f4716` está verificado.

Uma pegadinha do ambiente: `coverage` **não está na imagem do Docker**. Para
rodar os gates localmente, instale antes:

```bash
docker compose run --rm web sh -c "pip install -q coverage==7.6.1 && python -m coverage run --rcfile=../.coveragerc-critical manage.py test app --settings=simulador_operacional.settings_test"
```

A suíte sozinha não precisa disso:

```bash
docker compose run --rm web python manage.py test app --settings=simulador_operacional.settings_test
```

## Regras de trabalho, não negociáveis

- **Testes sempre via Docker.** Nunca crie venv local. Nunca rode `pytest` ou
  `manage.py test` fora do contêiner.
- **Nunca faça push nem abra PR** sem o Rafael pedir explicitamente.
- **Um commit por item**, mensagem em português, terminando com
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- **Rode a suíte antes de cada commit** e mostre a saída. Se não rodar, diga
  na mensagem do commit que não foi verificado — foi o que aconteceu no
  `01338cd` e está escrito lá.
- **Nenhum teste pode gravar arquivo dentro do repositório.** Isso já deu
  problema: um teste de exportação despejou PDFs em
  `simulador_operacional/relatorios/` e eles entraram num commit. Use
  `tempfile.TemporaryDirectory()`.

## Fonte da verdade

1. `docs/GUIA_IMPLEMENTACAO.md` — o documento central. Traz a matriz de
   conformidade (seção 4), o backlog priorizado (seção 5), os bloqueadores
   B1–B11 e os desvios deliberados. **Leia antes de decidir escopo.**
2. `_documentação/MD/` — a especificação do Dr. Pio Marinheiro, extraída dos
   `.docx` com tabelas preservadas e as 23 fórmulas que eram imagens já
   transcritas. É a especificação real.
3. `docs/BACKLOG.md` — **histórico, não use para decidir escopo.** Os status
   `CONCLUIDO` lá refletem entrega de sprint, não conformidade.

Na matriz da seção 4, `CONFORME` significa implementado **com teste
passando** — e é esse o estado atual de tudo. Mantenha o critério: não marque
uma linha como conforme sem a suíte verde na mão.

## Quem decide o quê

O Dr. Pio Marinheiro é o Product Owner e autor da especificação. O que ele
definiu tem prioridade sobre o que nos parece melhor. O que ele deixou em
aberto, decidimos nós — e as soluções já criadas para pontos em aberto ficam
como estão, não reabra.

Quando a especificação se contradiz, vale a **versão internamente
consistente** — aquela que reproduz os próprios números declarados. Duas
contradições já estão registradas e **não devem ser "corrigidas" em silêncio**:

- §12.6: a tabela de exemplo não reproduz a fórmula do §12.2 com os pesos do
  §12.4 (o G1 daria 77,9 e a tabela declara 75,35).
- §14.1.3: a tabela de exemplo não reproduz a fórmula do §14.1.1 (declara
  1,038 para R$ 1.000 onde a fórmula dá 1,150, e salta de 1,051 para 1,200
  entre R$ 5.000 e R$ 10.000 — degrau que nenhuma curva logarítmica produz).

Em ambos vale a fórmula, que é a parte normativa.

## Armadilhas já mapeadas — não repita

- **`atendimento_demanda_percent` é `vendidos / ofertados`**, uma métrica de
  oferta. Não é satisfação da demanda e não serve para o eixo SD; é duplicata
  do segundo componente do EO.
- **Duas trilhas de migração.** `app/migrations` é a principal e hoje **não
  aplica limpa** (item `ORION-C-22`); `app/migrations_ci` é a limpa, usada por
  `settings_ci`. Toda migração nova precisa entrar nas duas. `settings_test`
  usa `MIGRATION_MODULES = {'app': None}` e monta as tabelas a partir dos
  modelos, então a suíte passa mesmo com a trilha principal quebrada.
- **`//` em `Decimal` trunca em direção ao zero, não para baixo.** Para teto,
  use `(a / b).to_integral_value(ROUND_CEILING)`.
- **Comentário multilinha em template Django:** `{# #}` é de uma linha só;
  para várias use `{% comment %}`.
- **Gráficos:** a paleta categórica tem 5 posições fixas em `static/css/styles.css`
  (`--o-series-1` a `--o-series-5`). Não cicle com `i % n` e não reutilize as
  cores de status (`--o-ok`, `--o-warn`, `--o-bad`) como série.

## Backlog — o que falta

Prioridade, de cima para baixo:

- `ORION-C-02` — unificar o desconto logístico cruzado; há duas
  implementações divergentes da mesma regra. A de `services/materias_primas.py`
  é a que segue a especificação. **Depende de `C-26`.**
- `ORION-C-26` `BLOQUEADO` — B6 e B7, frete de produto acabado e unidade do
  frete de matéria-prima, seguem sem decisão do Rafael. Não comece trabalho de
  logística antes disso.
- `ORION-C-08` — custo do operador e conversão mês/rodada.
- `ORION-C-10` — documentar ou corrigir a taxa de frete de produto acabado.
- `ORION-C-13` — tela de Encerramento da Rodada (o template
  `financeiro/encerramento.html` já existe, falta view e rota).
- `ORION-C-14` — Relatórios Comparativos (templates em `dashboard/` já existem).
- `ORION-C-16` — Classificação final (template `classificacao.html` já existe).
- `ORION-C-17` — Ranking com destaques da rodada e evolução do grupo.
- `ORION-C-18` — Gerenciamento do jogo: monitorar participação por grupo.
- `ORION-C-19` a `C-22`, `C-25` — dívida e higiene: remover `homeold.html`,
  resolver `GameConfig.capacidade_maquina = 100`, decidir o destino de
  `services/vendas.py` (hoje só usado por teste), consertar a trilha principal
  de migrations e subir a catraca dos gates.

Dois pontos de análise que estão registrados no guia e continuam abertos:

- **B9** — o giro de estoque é contado duas vezes: dentro do DF (como IE) e
  como eixo próprio (EE), somando ~22,5% da pontuação.
- **B10** — o limiar de 1.000 km do DS₃ é inerte no mapa regional, cuja praça
  mais distante está a 470 km. Já foi recalibrado para 200 km em
  `parametros.DISTANCIA_REGIONAL_KM`, mas vale confirmar com o Rafael.

## Pergunta em aberto para o Rafael

Um grupo que não opera na rodada tira DS = 80 e EO = 20, porque "não teve
perdas" e "não comprou longe" são verdade quando não houve operação. É a
fórmula do §12.3 ao pé da letra. Se ele considerar isso exploração indevida,
o caminho é zerar os eixos quando não há atividade. Pergunte antes de mudar.

## Como trabalhar

Mudanças pequenas e revisáveis. Um item por vez, com teste que falha sem a
correção. Quando encontrar divergência entre código e especificação, registre
no `docs/GUIA_IMPLEMENTACAO.md` em vez de decidir calado — é assim que o
documento continua sendo útil.
