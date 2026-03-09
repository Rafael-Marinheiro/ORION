# Documentacao ORION

Este diretorio concentra toda a documentacao funcional, tecnica e operacional do projeto.

## Estrutura
- `BACKLOG.md`: backlog oficial de implementacao.
- `CHANGELOG.md`: historico de mudancas por versao.
- `VERSION`: versao alvo da release.
- `roadmap.md`: ideias e sugestoes de evolucao.
- `RUNBOOK_OPERACAO.md`: operacao do sistema em ambiente.
- `SMOKE_TEST_CHECKLIST.md`: roteiro de validacao rapida pos-deploy.
- `RELEASE_CHECKLIST.md`: checklist de release.
- `BACKUP_RESTORE_CHECKLIST.md`: plano de backup/restore.
- `release/`: notas e artefatos de releases (`rc1`, `rc2`, etc.).

## Convencoes
- Novos documentos devem ser criados em `docs/`.
- Atualizacoes de release devem refletir em:
  - `docs/VERSION`
  - `docs/CHANGELOG.md`
  - `docs/release/RELEASE_NOTES_<versao>.md`
