# Commit Plan - v1.0.0-rc1

Objetivo: organizar o merge em blocos lÃ³gicos para facilitar revisÃ£o e rollback parcial.

## Bloco 1 - Core de negÃ³cio e domÃ­nio
Mensagem:
`feat(core): concluir motor operacional com CEO por rodada, demanda cidade+produto, investimentos e eventos de estado`

Escopo:
- modelos, serializers, views e URLs do domÃ­nio.
- comandos de fechamento/seed.
- migraÃ§Ãµes `0003` a `0011`.

## Bloco 2 - Front-end e experiÃªncia
Mensagem:
`feat(front): reorganizar painel em mÃ³dulos, melhorar responsividade e ajustar contraste/relatÃ³rios`

Escopo:
- templates do painel, relatÃ³rios, ranking, jobs, base e wizard.
- `static/css/styles.css`.

## Bloco 3 - Qualidade e CI
Mensagem:
`chore(ci): adicionar gate de cobertura e validaÃ§Ãµes de migraÃ§Ã£o/testes no pipeline`

Escopo:
- `.github/workflows/django.yml`
- `.coveragerc`
- `requirements-dev.txt`
- testes atualizados/novos.

## Bloco 4 - OperaÃ§Ã£o e release
Mensagem:
`docs(ops): adicionar runbook, smoke test, checklist de release e notas de versÃ£o`

Escopo:
- `docs/`
- `docs/CHANGELOG.md`
- `docs/VERSION`
- atualizaÃ§Ã£o de `README.md`

## Bloco 5 - OrganizaÃ§Ã£o de utilitÃ¡rios manuais
Mensagem:
`chore(repo): mover scripts manuais para tools/manual`

Escopo:
- `tools/manual/*`
- remoÃ§Ã£o dos scripts equivalentes na raiz.

---

## Exemplo de tag final
1. `git tag -a v1.0.0-rc1 -m "Release v1.0.0-rc1"`
2. `git push origin v1.0.0-rc1`
