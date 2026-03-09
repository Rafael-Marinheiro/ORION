# Release Checklist

## 1) Preparacao
1. Atualizar branch com mudancas aprovadas.
2. Confirmar migracoes versionadas (principal e CI).
3. Revisar backlog e changelog (`docs/CHANGELOG.md`).
4. Definir versao em `docs/VERSION`.

## 2) Qualidade
1. Executar local:
- `python -m compileall simulador_operacional/app`
- `python simulador_operacional/manage.py makemigrations --check --dry-run`
- `python simulador_operacional/manage.py makemigrations --check --dry-run --settings=simulador_operacional.settings_ci`
- `python simulador_operacional/manage.py test app --settings=simulador_operacional.settings_test`
2. Cobertura critica:
- `coverage run --rcfile=.coveragerc-critical simulador_operacional/manage.py test app --settings=simulador_operacional.settings_test`
- `coverage report --rcfile=.coveragerc-critical --fail-under=85`
3. CI verde em todas as etapas.

## 3) Operacao
1. Backup antes de deploy.
2. Aplicar migracoes em producao.
3. Executar `seed_dados_base` se houver novos catalogos.
4. Validar jobs agendados e `/jobs/`.

## 4) Pos-deploy
1. Executar smoke test completo (GM + Grupo).
2. Validar `/relatorios/`, `/ranking/` e exportacoes.
3. Confirmar trilha de auditoria e consolidado por rodada.

## 5) Encerramento
1. Publicar release notes.
2. Congelar tag/versao.
3. Comunicar riscos residuais e plano de rollback.
