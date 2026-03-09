# Changelog

## [2026-03-09] - Backlog Completo + Estabilização

### Added
- Capacidade dedicada por produto (A/B/C) com operadores por linha.
- Consolidado persistido por grupo/rodada.
- CEO por rodada e auditoria de submissões.
- Demanda por cidade+produto com teto por produto.
- Investimentos por cidade/linha e aplicação financeira com rendimento.
- Eventos de estado (atraso MP, retenção, bloqueio de produção, quebra de estoque).
- Dashboard de jobs e registro de execução com `correlation_id`.
- Wizard de configuração em 3 etapas.
- Novos endpoints API para consolidados, CEOs, auditoria, demanda, aplicações e jobs.
- Pipeline CI com gate de cobertura.
- Documentação operacional (smoke test, runbook e release checklist).

### Changed
- Painel reorganizado em módulos com foco gerencial.
- Relatórios e ranking com ajustes de visibilidade e responsividade.
- Regras de isolamento por jogo reforçadas nas APIs e processamento.
- Exportações PDF/Excel alinhadas ao consolidado de rodada.

### Fixed
- Navegação de usuários autenticados para ranking/relatórios sem bloqueio indevido.
- Contraste em tema escuro no painel.
- Fallback para gráfico em caso de indisponibilidade de CDN externa.
