# Changelog

## [1.0.0-rc2] - 2026-03-09

### Added
- Trilha de migracao limpa para CI em `app/migrations_ci`.
- `settings_ci` para validacao de ambiente limpo.
- Checklist dedicado de backup/restore em `docs/BACKUP_RESTORE_CHECKLIST.md`.
- Cobertura critica dedicada em `.coveragerc-critical`.
- Novos testes de servicos basicos (`producao`, `vendas`, `investimentos`).

### Changed
- Pipeline CI atualizado com validacoes de build, migracao e seed em ambiente limpo.
- Gate de cobertura ajustado para regras criticas (meta >=85%).
- Runbook e release checklist atualizados para fluxo operacional atual.

### Fixed
- Erros de runtime em `views.py` (import `csv`) e permissao de cadastro (apenas gamemaster).
- Coerencia do modelo `Investimento` com servicos e testes.
- Servicos legados (`distribuicao`, `classificacao`, `fechamento`) alinhados ao schema atual.
- Suite de testes estabilizada para 70 cenarios passando.

## [1.0.0-rc1] - 2026-03-09

### Added
- Capacidade dedicada por produto (A/B/C) com operadores por linha.
- Consolidado persistido por grupo/rodada.
- CEO por rodada e auditoria de submissoes.
- Demanda por cidade+produto com teto por produto.
- Investimentos por cidade/linha e aplicacao financeira com rendimento.
- Eventos de estado (atraso MP, retencao, bloqueio de producao, quebra de estoque).
- Dashboard de jobs e registro de execucao com `correlation_id`.
- Wizard de configuracao em 3 etapas.
- Novos endpoints API para consolidados, CEOs, auditoria, demanda, aplicacoes e jobs.
- Pipeline CI com gate de cobertura.
- Documentacao operacional (smoke test, runbook e release checklist).
