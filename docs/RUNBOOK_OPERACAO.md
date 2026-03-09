# Runbook Operacional

## Comandos de Rotina
1. Aplicar migrações:
`python manage.py migrate`
2. Popular base:
`python manage.py seed_dados_base`
3. Fechar rodadas vencidas:
`python manage.py fechar_rodadas`
4. Alias legado:
`python manage.py encerrar_rodadas`
5. Enviar lembretes:
`python manage.py enviar_lembretes`

## Observabilidade
1. Dashboard operacional:
`/jobs/`
2. API de execuções:
`/api/execucoes-jobs/`
3. Log de agendamentos:
`simulador_operacional/agendamentos.log`
4. Correlação:
- cada execução de `fechar_rodadas` registra `correlation_id`.

## Backup e Restauração
1. Gerar backup (SQLite):
`python manage.py backupdb`
2. Arquivos gerados em:
`simulador_operacional/backups/`
3. Restauração manual (ambiente parado):
- copiar backup desejado para sobrescrever `simulador_operacional/db.sqlite3`.

## Diagnóstico Rápido
1. Rodada não fecha:
- checar data/hora (`fim <= now`);
- executar manualmente `fechar_rodadas`;
- verificar `/jobs/` e `agendamentos.log`.
2. Dados não aparecem no painel/ranking:
- validar vínculo de usuário com grupo;
- validar jogo associado (`jogo_id`);
- conferir filtros por rodada e permissões.
3. Diferença de resultados:
- revisar evento da rodada em `EVENTOS_RODADA`;
- revisar submissão/auditoria de CEO por rodada;
- revisar investimentos pendentes/processados.

## Segurança Operacional
1. Não executar scripts manuais destrutivos em produção sem backup.
2. Scripts manuais ficam em `tools/manual/` e não fazem parte do fluxo padrão de operação.
3. Validar `.env` e `ALLOWED_HOSTS` antes de expor ambiente.
4. Rodar smoke test após deploy.
