# Pontos para ratificação do autor da especificação

Documento para levar ao Prof. Dr. Pio Marinheiro. Cada item descreve **o que
o documento diz**, **o que o sistema faz** e **por que divergem**. Nenhum
deles é escolha de implementação: todos alteram ou interpretam a regra, e a
regra é dele.

Para cada item há uma decisão possível em uma linha. Se a resposta for
"não", a coluna *Como reverter* diz o custo — em todos os casos ele é baixo,
porque nenhuma dessas decisões foi embutida no motor.

Atualizado em 14/10/2026.

---

## 1. Evento com decisão da equipe — "Surto de gripe"

**O documento (§8.2):** *"Aplicação uniforme: o evento sorteado afeta todos
os grupos de maneira igual, independentemente de sua praça/cidade."*

**O documento (§8.3):** a tabela de variáveis afetadas lista custo
logístico, entregas, custo das matérias-primas e demanda. Não lista força de
trabalho nem caixa.

**O que o sistema faz:** na rodada em que o evento sai, todas as equipes
recebem a mesma oferta — imunizar a força de trabalho por um valor por
trabalhador. Quem aceita paga no fechamento e atravessa a rodada. Quem
recusa, ou não responde, tem uma parcela da equipe afastada, sorteada entre
15% e 35%, e produz menos pela própria RN-06 ("cada máquina exige 2
trabalhadores; máquinas sem operadores não produzem").

**Por que divergem:** a *oferta* é uniforme, mas o *resultado* passa a
depender da decisão de cada equipe. É uma leitura defensável do §8.2 — e,
pedagogicamente, transforma o evento em gestão de risco, que é o que o §8.6
diz querer ensinar. Mas é leitura, não o texto.

**Pergunta:** o senhor aceita que um evento faça oferta uniforme com
resultado dependente da decisão da equipe, e que o §8.3 passe a admitir
força de trabalho e caixa entre as variáveis afetadas?

**Como reverter:** desligar o pool estendido na configuração da turma. Ela
volta a sortear exatamente os seis eventos do §8.4, sem alteração de código.

---

## 2. Pool estendido de eventos aleatórios

**O documento (§8.4):** seis eventos, com probabilidades que somam 100%.

**O que o sistema faz:** os seis continuam sendo o padrão, com as
probabilidades originais. A turma que ligar a opção passa a sortear também
dez eventos fora da especificação, que somam 100% entre si — metade dos
sorteios cai no documento, metade na extensão.

**Por que propus:** três lacunas do §8.4 aparecem no uso.

- **O eixo econômico só sobe.** Há o *Boom de consumo* de +15% e nada
  simétrico; nenhuma rodada traz retração de demanda.
- **O eixo logístico só pune.** Greve e enchente; nenhum evento logístico
  favorável.
- **Nada atinge o planejamento de compra.** Nenhum dos seis mexe no prazo
  de entrega da matéria-prima, que é a decisão de antecipação mais difícil
  do jogo.

**Pergunta:** o senhor aprova o pool como opção desligada por padrão? E, se
aprovar, quer revisar os dez enunciados e impactos antes do uso em sala?

**Como reverter:** a opção já nasce desligada. Turma que não a ligar nunca
vê esses eventos.

---

## 3. Dois eventos simultâneos e evento determinado pelo professor

**O documento (§8.2):** *"a cada rodada, o sistema realiza um sorteio
automatizado para selecionar um único evento aleatório"*.

**O documento (RN-10, §5):** prevê *"até 2 eventos aleatórios simultâneos"*,
com *"ativação definida pelo moderador"* e anúncio *"na abertura da rodada"*.

**O que o sistema faz:** segue a RN-10. Na abertura, o professor pode
determinar o evento da rodada e escolher se um segundo, sorteado, ocorre
junto.

**Por que está aqui:** os dois trechos do documento não dizem a mesma coisa.
O sistema seguiu a RN-10 por ser a mais específica, mas a escolha merece
registro.

**Pergunta:** confirma que a RN-10 prevalece sobre a frase do §8.2?

---

## 4. "Consistência nas decisões" — definição do indicador

**O documento (§15.4.c):** lista entre os indicadores de uso *"submissões em
tempo, consistência nas decisões e variação entre desempenhos"*, sem definir
como medir a consistência.

**O que o sistema faz:** mede a parcela das rodadas submetidas em que a
equipe de fato registrou operação. O §11.2 faz a submissão vazia repetir a
rodada anterior; o indicador separa quem decidiu de quem apenas apertou
"enviar".

**Pergunta:** a definição serve, ou o senhor tem outra em mente?

**Como reverter:** é um cálculo isolado num único módulo; trocar a fórmula
não afeta mais nada.

---

## 5. Itens dos questionários do §15.4

**O documento (§15.4):** lista os **temas** dos questionários — clareza e
usabilidade, relevância do conteúdo, aprendizados percebidos e engajamento,
sugestões de melhoria (alunos); integração com a ementa, desenvolvimento de
competências, facilidade de uso e gestão, observações sobre os grupos
(docentes). Não traz os enunciados.

**O que o sistema faz:** nove itens em escala Likert de cinco pontos para o
aluno e seis para o docente, redigidos a partir desses temas, mais campos
abertos.

**Pergunta:** os enunciados precisam de revisão antes de virarem instrumento
de pesquisa? Se os dados forem usados na dissertação, convém que o senhor
valide o texto de cada item e a escala de cinco pontos.

---

## 6. Decisões tomadas durante o desenvolvimento, nunca apresentadas

Decididas por Rafael ao longo do projeto, por ausência de definição no
documento. Estão descritas em `GUIA_IMPLEMENTACAO.md` com o código
correspondente.

| Código | Assunto |
|---|---|
| B-4 | Sempre há exatamente um evento por rodada (as probabilidades do §8.4 somam 100%) |
| B-6 | Tratamento do arredondamento nos cálculos de capacidade |
| B-11 | Critério de ordenação quando há empate antes do §12.5 |
| B-12 | Comportamento do estoque de matéria-prima na virada de rodada |
| D-10 | Momento do débito da matéria-prima (na compra, não na produção) |
| D-12 | Tratamento de produto perecível retido por evento logístico |

**Pergunta:** o senhor quer revisar as seis, ou ratifica em bloco o que está
implementado e documentado?

---

## Ensaio de rede (§11.1) — não é ratificação, é agendamento

O §11.1 exige fechamento *"no momento exato do prazo-limite"*. A submissão
já é barrada no instante exato, e o processamento roda a cada minuto. O que
falta é medir na rede da instituição, com a turma inteira conectada: se o
servidor não aguentar a rajada do último minuto, a equipe que submeter em
cima do prazo perde a rodada por lentidão, não por decisão.

O instrumento de medição está pronto:

```bash
python manage.py ensaio_de_rede --equipes 12 --repeticoes 5
```

Ele mede a resposta do painel sob a carga de uma turma e se o fechamento
cabe na janela de um minuto. **Precisa rodar no servidor da instituição**,
não na máquina de desenvolvimento — é a rede deles que está em questão.
