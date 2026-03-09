# Commit Plan - v1.0.0-rc1

Objetivo: organizar o merge em blocos lógicos para facilitar revisão e rollback parcial.

## Bloco 1 - Core de negócio e domínio
Mensagem:
`feat(core): concluir motor operacional com CEO por rodada, demanda cidade+produto, investimentos e eventos de estado`

Escopo:
- modelos, serializers, views e URLs do domínio.
- comandos de fechamento/seed.
- migrações `0003` a `0011`.

## Bloco 2 - Front-end e experiência
Mensagem:
`feat(front): reorganizar painel em módulos, melhorar responsividade e ajustar contraste/relatórios`

Escopo:
- templates do painel, relatórios, ranking, jobs, base e wizard.
- `static/css/styles.css`.

## Bloco 3 - Qualidade e CI
Mensagem:
`chore(ci): adicionar gate de cobertura e validações de migração/testes no pipeline`

Escopo:
- `.github/workflows/django.yml`
- `.coveragerc`
- `requirements-dev.txt`
- testes atualizados/novos.

## Bloco 4 - Operação e release
Mensagem:
`docs(ops): adicionar runbook, smoke test, checklist de release e notas de versão`

Escopo:
- `docs/`
- `CHANGELOG.md`
- `VERSION`
- atualização de `README.md`

## Bloco 5 - Organização de utilitários manuais
Mensagem:
`chore(repo): mover scripts manuais para tools/manual`

Escopo:
- `tools/manual/*`
- remoção dos scripts equivalentes na raiz.

---

## Exemplo de tag final
1. `git tag -a v1.0.0-rc1 -m "Release v1.0.0-rc1"`
2. `git push origin v1.0.0-rc1`
