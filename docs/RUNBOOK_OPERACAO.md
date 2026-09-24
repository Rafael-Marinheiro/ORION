# Roteiro da primeira turma — ensaio local

Validado em 20/09/2026 pelo cenário automatizado `test_primeira_turma`:
duas equipes de três pessoas, três rodadas, compra D+1, produção, distribuição,
submissão, resultados e classificação. O ensaio controla o sorteio para
Estabilidade econômica; em sala os eventos são aleatórios e os valores variam.

## 1. Preparação pelo responsável técnico

Trabalhar no PowerShell, em:

```powershell
Set-Location 'C:\Projetos\ORION\.claude\worktrees\recursing-pascal-f25acd'
```

O banco deste worktree estava vazio e recebeu migrações e seed nesta execução.
Ainda não há alunos. A migração antiga criou uma conta de administrador; sua senha
foi invalidada nesta execução. Para usar essa conta, o responsável deve definir
uma senha nova com `changepassword`. Instalações novas não criam contas automaticamente.
Se preparar outra instalação, criar `.env` a partir de `.env.example` apenas
se não existir. Para ensaio local: `DJANGO_DEBUG=True` e hosts
`localhost,127.0.0.1`; definir uma chave secreta própria. Este roteiro é local,
não um procedimento de publicação na internet.

Usar sempre os **dois arquivos Compose** abaixo. O segundo mantém o banco no
worktree, serve os estilos no ensaio local e inicia o processo de rodadas.
O Compose original sozinho não instala cron nem preserva o banco quando o
contêiner é recriado.

```powershell
docker compose -f docker-compose.yml -f docker-compose.turma.yml build
docker compose -f docker-compose.yml -f docker-compose.turma.yml run --rm web python manage.py migrate --noinput
# Somente em preparação, antes de haver partida em andamento:
docker compose -f docker-compose.yml -f docker-compose.turma.yml run --rm web python manage.py seed_dados_base
# Neste worktree, redefinir interativamente a conta existente:
docker compose -f docker-compose.yml -f docker-compose.turma.yml run --rm web python manage.py changepassword rafasilvamarinheiro@gmail.com
# Em instalação nova, ou para criar outro professor, escolher e-mail, nome e senha:
docker compose -f docker-compose.yml -f docker-compose.turma.yml run --rm web python manage.py createsuperuser
docker compose -f docker-compose.yml -f docker-compose.turma.yml up -d
```

Abrir `http://localhost:8000/`. O responsável entrega o endereço e o acesso do
professor. Para alunos em outras máquinas, o responsável deve validar a rede,
os hosts e o endereço do servidor antes da aula. Não houve teste dessa rede.

Antes de entregar ao professor:

- Entrar, conferir estilos, sair e entrar novamente.
- Em Configuração, conferir os padrões da seção 2.
- Confirmar 12 cidades e 36 demandas de produto na base; fontes em
  `docs/BASE_REGIONAL.md`.
- Confirmar que o serviço `rodadas` está ativo. Há somente um processador;
  não habilitar outro cron de fechamento em paralelo.
- Ensaiar uma rodada curta, observar os resultados após o prazo e verificar
  o job com sucesso em **Gestão → Execuções de jobs**.

```powershell
docker compose -f docker-compose.yml -f docker-compose.turma.yml ps
docker compose -f docker-compose.yml -f docker-compose.turma.yml logs --tail 40 rodadas
```

O painel bloqueia submissões ao vencer o prazo. O processamento consulta as
rodadas a cada segundo, mais o tempo dos comandos; os resultados podem aparecer
logo depois. O agendador do sistema operacional não fornece garantia de execução
no instante exato previsto pelo DOCX 11; registre a tolerância observada no
ensaio. Falhas aparecem nos logs e em Execuções de jobs. Manter a máquina ligada
e sem suspensão na aula.

## 2. Professor: preparar a turma

1. Entre com seu e-mail e senha. Abra **Gestão → Configuração**.
2. Para o primeiro teste, use capital **R$ 1.000.000**, estoque **0**, máquinas
   **40**, linhas A/B/C **15/15/10**, trabalhadores **80** e **3 rodadas**.
   Mantenha os três módulos ativos e produtos **A,B,C**.
3. Confira os cinco pesos: EO **0,30**, DF **0,25**, EE **0,15**, SD **0,20**,
   DS **0,10**. A soma deve ser 1. Salve e reabra para conferir.
4. Abra **Gestão → Grupos → Novo grupo**. Escolha **Jogo Principal** em todos
   os grupos deste ensaio. Cadastre três integrantes, com e-mails distintos,
   senhas de pelo menos oito caracteres com letras e números, e marque
   exatamente um líder. Confira os e-mails institucionais; não há filtro de domínio.
5. Distribua os acessos por canal privado. Cada pessoa entra com sua conta.
   O líder é o CEO inicial. O membro consulta o painel; só o CEO registra as
   operações e envia a decisão oficial.
6. Abra **Gestão → Abrir rodada**, escolha o mesmo jogo, número **1** e uma
   data/hora futura. Todos os horários da interface são de Currais Novos (UTC−3).

Não usar o assistente para recalibrar máquinas/estoques neste primeiro ensaio:
a personalização operacional ainda não está certificada. Use a tela completa
com os padrões acima. Não criar duas turmas no mesmo jogo nem compartilhar
contas entre grupos.

## 3. Alunos: uma operação pequena, fácil de conferir

Os números abaixo são um exercício de funcionamento, não uma estratégia de
lucro. O frete de insumos é alto pela regra documental: R$ 1,50/km/kg. A folha
é de R$ 144.000 por rodada com os 80 operadores iniciais.

**Rodada 1 — comprar para produzir depois**

No Painel, o CEO registra as quatro compras para uma unidade do produto A:

| Insumo | Quantidade (kg) | Fornecedor |
|---|---:|---|
| MP1 | 120 | Caico |
| MP2 | 40 | Campina Grande |
| MP3 | 60 | Assu |
| MP4 | 80 | Patos |

Confira o débito e o recebimento previsto na rodada 2. Ainda não é possível
produzir usando essas compras na rodada 1. Depois de revisar, preencha a
descrição da decisão, quantidade 0 no resumo e envie a **submissão oficial**.
Registrar compras não substitui enviar a decisão; após enviar, as operações
ficam bloqueadas. O professor acompanha os envios em **Gerenciamento do jogo**.

**Rodada 2 — produzir e vender**

Após os resultados da rodada 1 aparecerem, o professor abre a rodada 2 no
mesmo jogo. O CEO entra no Painel para receber os insumos. Se um evento reteve
entregas, confira o boletim e o estoque; pode ser necessário aguardar a rodada 3.
Se há estoque suficiente, registre produção de **1 unidade de A**. Depois,
distribua **1 unidade de A para Natal**, com preço **R$ 5.000**. Envie a decisão
oficial. A quantidade vendida só é apurada no fechamento.

**Rodada 3 — revisar o resultado**

O professor abre a rodada 3. Cada equipe consulta relatórios, estoque e caixa,
registra as operações que couberem e envia a decisão. Mesmo sem nova operação,
é necessário enviar a decisão para evitar multa. Não prometer lucro: a folha,
o frete, os eventos e a demanda fazem parte da discussão didática.

## 4. Professor: conferir e encerrar

Depois de cada prazo, confira **Execuções de jobs**, **Ranking**, **Relatórios**
e **Encerramento**. Os alunos devem ver somente resultados de rodadas fechadas
nas telas desse roteiro. Na terceira rodada fechada, abra **Classificação final**.
Confira as duas equipes, os três resultados de cada grupo e exporte PDF/Excel.
Se o resultado não aparecer, peça ao responsável que confira os logs antes de
abrir outra rodada. Não refaça operações nem reaplique o seed para tentar corrigir.

O ranking ainda depende de ratificações pedagógicas registradas no guia
(B8/B12: fórmula e escala do SD — o denominador era o mercado inteiro, 37×
maior que a planta, e o eixo valia no máximo 0,54 de 100; B11: escala do giro
de estoque — o indicador não tinha teto e o estoque zerado valia 0, invertendo
o incentivo do §12.3.3. B11 e B12 foram decididos pelo Rafael e ainda não
apresentados ao Dr. Pio; D11: variedade de eventos). Use o ensaio para avaliar a ferramenta; não trate a
pontuação como nota oficial antes da ratificação do Dr. Pio.

## 5. Backup, retomada e diagnóstico técnico

```powershell
docker compose -f docker-compose.yml -f docker-compose.turma.yml exec web python manage.py backupdb
```

O banco persistente fica em `simulador_operacional/db.sqlite3` e os backups em
`simulador_operacional/backups/`. Antes de restaurar, pare web e rodadas; copie
o arquivo escolhido sobre o banco com os serviços parados e depois reinicie.
Consulte também `docs/BACKUP_RESTORE_CHECKLIST.md`. Não sobrescreva o banco de
uma turma para preparar outro ensaio.

```powershell
docker compose -f docker-compose.yml -f docker-compose.turma.yml stop
# Para retomar preservando o banco:
docker compose -f docker-compose.yml -f docker-compose.turma.yml up -d
```

Para fechar manualmente uma rodada vencida, pare primeiro o serviço `rodadas`
e execute `python manage.py fechar_rodadas` no serviço web; depois reinicie
`rodadas`. Não usar o alias histórico como processador alternativo.

## 6. Verificação automatizada

```powershell
docker compose -f docker-compose.yml -f docker-compose.turma.yml run --rm web python ../tools/verificar_base_limpa.py
docker compose -f docker-compose.yml -f docker-compose.turma.yml run --rm web python manage.py test app.tests.test_primeira_turma --settings=simulador_operacional.settings_test
docker compose -f docker-compose.yml -f docker-compose.turma.yml run --rm web python manage.py test app --settings=simulador_operacional.settings_test
```

O banco dos testes é isolado e descartado pelo Django. O ensaio automatizado
não cria pessoas nem decisões no banco da turma. A verificação cobre o fluxo
HTTP, regras e persistência; o responsável ainda deve executar a lista de
navegador, rede e rodada curta antes de reunir os alunos.
