# Release Checklist

## Ensaio de primeira turma — 20/09/2026

- [x] Fontes regionais, datas e diferenças em `BASE_REGIONAL.md`.
- [x] Auditoria RN-01/RN-02 e correções com testes.
- [x] Suíte no Docker: 248 testes; gates 93%/85%.
- [x] Migrações reais + seed duas vezes sem conta administrativa automática.
- [x] Cenário de duas equipes e três rodadas até classificação e exportações.
- [x] Roteiro para professor/alunos e preparação técnica separados.
- [ ] Responsável define senha do professor; nunca usar senha antiga provisionada.
- [ ] Responsável executa ensaio de navegador, rede e fechamento no ambiente da aula.
- [ ] Dr. Pio ratifica pendências pedagógicas antes do uso como nota oficial.

Usar `RUNBOOK_OPERACAO.md` e os dois arquivos Compose para o ensaio local.
Os passos gerais de release abaixo continuam sendo para publicação posterior.


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
- `coverage report --rcfile=.coveragerc-critical --fail-under=90`
- `coverage report --rcfile=.coveragerc-perifericos --fail-under=70`
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
