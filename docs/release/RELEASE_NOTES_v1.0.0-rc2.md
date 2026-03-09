# Release Notes - v1.0.0-rc2

Data: 2026-03-09

## Resumo
Release de hardening tecnico com foco em:
- estabilidade de testes;
- pipeline de qualidade ponta a ponta;
- validacao de ambiente limpo com migracao e seed;
- preparo operacional para release.

## Entregas
1. Fechamento tecnico da versao
- hotfixes de runtime (`csv`, permissao de registro, coerencia de investimento);
- alinhamento de servicos legados ao schema atual.

2. Pipeline de qualidade
- workflow CI com:
  - `compileall`;
  - `makemigrations --check` (trilha principal + trilha CI);
  - `migrate + seed + check` em ambiente limpo (`settings_ci`);
  - testes com gate de cobertura critica `>=85%`.

3. Testes e fluxos principais
- suite estabilizada em 70 testes verdes;
- testes adicionais para servicos criticos.

4. Operacao
- runbook revisado;
- checklist de backup/restore adicionado.

## Validacoes executadas
- `python manage.py makemigrations --check --dry-run`
- `python manage.py makemigrations --check --dry-run --settings=simulador_operacional.settings_ci`
- `python manage.py migrate --noinput --settings=simulador_operacional.settings_ci`
- `python manage.py seed_dados_base --settings=simulador_operacional.settings_ci`
- `python manage.py check --settings=simulador_operacional.settings_ci`
- `python manage.py test app --settings=simulador_operacional.settings_test`
- `coverage report --rcfile=.coveragerc-critical` (90%)
