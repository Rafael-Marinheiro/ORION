# Runbook Operacional

## 1) Rotina de operacao
1. Aplicar migracoes:
`python manage.py migrate`
2. Popular catalogos base:
`python manage.py seed_dados_base`
3. Fechar rodadas vencidas:
`python manage.py fechar_rodadas`
4. Alias legado:
`python manage.py encerrar_rodadas`
5. Enviar lembretes:
`python manage.py enviar_lembretes`

## 2) Validacao de ambiente limpo (CI/local)
1. Checar migracoes principais:
`python manage.py makemigrations --check --dry-run`
2. Checar trilha limpa de CI:
`python manage.py makemigrations --check --dry-run --settings=simulador_operacional.settings_ci`
3. Subir banco limpo:
`python manage.py migrate --noinput --settings=simulador_operacional.settings_ci`
4. Popular base limpa:
`python manage.py seed_dados_base --settings=simulador_operacional.settings_ci`
5. Sanidade do Django:
`python manage.py check --settings=simulador_operacional.settings_ci`

## 2.1) Smoke automatizado
Executar fluxo tecnico automatizado com relatorio:
`python tools/run_smoke.py`

Saida:
- status das etapas no terminal;
- relatorio em `docs/reports/smoke_YYYYMMDD_HHMMSS.md`.

## 3) Observabilidade
1. Dashboard operacional:
`/jobs/`
2. API de execucoes:
`/api/execucoes-jobs/`
3. Log de agendamentos:
`simulador_operacional/agendamentos.log`
4. Correlacao:
- cada execucao de `fechar_rodadas` registra `correlation_id`.

## 4) Backup e restauracao
1. Gerar backup SQLite:
`python manage.py backupdb`
2. Local dos backups:
`simulador_operacional/backups/`
3. Restauracao manual (ambiente parado):
- copiar backup escolhido sobre `simulador_operacional/db.sqlite3`.
4. Checklist detalhado:
- `docs/BACKUP_RESTORE_CHECKLIST.md`

## 5) Diagnostico rapido
1. Rodada nao fecha:
- validar `fim <= now`;
- executar `python manage.py fechar_rodadas`;
- conferir `/jobs/` e `agendamentos.log`.
2. Painel/ranking sem dados:
- validar vinculo do usuario com grupo;
- validar `jogo_id`;
- conferir filtros de rodada e permissoes.
3. Divergencia de resultado:
- revisar evento da rodada em `EVENTOS_RODADA`;
- revisar auditoria/submissao do CEO da rodada;
- revisar investimentos pendentes/processados.

## 6) Seguranca operacional
1. Nao executar scripts manuais destrutivos em producao sem backup.
2. Scripts manuais ficam em `tools/manual/` e nao entram no fluxo padrao.
3. Validar `.env` e `ALLOWED_HOSTS` antes de expor ambiente.
4. Executar smoke test apos deploy.
