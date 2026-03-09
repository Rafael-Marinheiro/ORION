# Release Checklist

## 1) Preparação
1. Atualizar branch com mudanças aprovadas.
2. Confirmar migrações versionadas.
3. Revisar backlog e changelog.

## 2) Qualidade
1. Executar local:
- `python -m compileall app`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test app --settings=simulador_operacional.settings_test`
2. CI verde com cobertura >= 85%.

## 3) Operação
1. Backup antes de deploy.
2. Aplicar migrações em produção.
3. Executar `seed_dados_base` (se necessário para novos catálogos).
4. Validar cron/jobs agendados.

## 4) Validação Pós-Deploy
1. Executar smoke test (GM + Grupo).
2. Validar `/jobs/`, `/relatorios/`, `/ranking/`.
3. Confirmar exportações PDF/Excel.

## 5) Encerramento
1. Publicar release notes.
2. Registrar versão/tag.
3. Comunicar mudanças e riscos residuais.
