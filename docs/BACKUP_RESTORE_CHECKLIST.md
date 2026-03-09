# Backup and Restore Checklist

## Antes da mudanca
1. Confirmar janela de manutencao.
2. Confirmar versao/tag em deploy.
3. Executar backup:
`python manage.py backupdb`
4. Validar arquivo gerado em `simulador_operacional/backups/`.
5. Registrar timestamp e responsavel.

## Durante a mudanca
1. Aplicar migracoes.
2. Executar seed (se necessario).
3. Rodar checks de sanidade.
4. Rodar smoke test basico.

## Se rollback for necessario
1. Parar aplicacao.
2. Selecionar backup valido mais recente.
3. Restaurar `db.sqlite3` com o arquivo selecionado.
4. Subir aplicacao.
5. Rodar `python manage.py check`.
6. Validar `/jobs/`, `/ranking/` e `/relatorios/`.
7. Registrar incidente, causa raiz e acao corretiva.
