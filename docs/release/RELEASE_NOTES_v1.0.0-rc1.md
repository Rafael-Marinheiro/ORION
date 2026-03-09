# Release Notes - v1.0.0-rc1

Data: 2026-03-09

## Resumo
Esta release candidata consolida o backlog funcional do ORION com foco em:
- regras operacionais completas por rodada;
- robustez de fechamento e indicadores;
- melhoria de UX do painel e relatórios;
- governança (isolamento por jogo, auditoria e observabilidade);
- base de qualidade com CI e cobertura.

## Principais Entregas

### Núcleo de Simulação
- Capacidade produtiva dedicada por produto/linha (A/B/C), incluindo operadores.
- Fechamento consolidado por grupo/rodada com métricas financeiras e operacionais.
- CEO oficial por rodada com auditoria de submissão (usuário, data/hora, IP).
- Demanda por cidade+produto com teto por produto.

### Realismo Operacional e Financeiro
- Investimentos:
  - marketing por cidade;
  - máquinas e RH por linha com ativação D+1;
  - aplicações financeiras (aplicar/resgatar) com rendimento por rodada.
- Desconto logístico cruzado (compra MP x envio na mesma cidade), parametrizável.
- Eventos de estado:
  - atraso de MP;
  - retenção de entrega;
  - bloqueio de produção;
  - quebra de estoque.

### Produto e UX
- Painel do grupo reorganizado em módulos.
- Filtro por rodada no painel.
- Ajustes de contraste/tema e responsividade de tabelas.
- Fallback para gráfico financeiro quando CDN externa indisponível.
- Wizard de configuração em 3 etapas.

### Plataforma e Governança
- Isolamento multi-jogo reforçado nas APIs e no fechamento.
- Registro de execução de jobs com `correlation_id`.
- Dashboard operacional de jobs.

### Qualidade e Operação
- Suite de testes expandida.
- CI com:
  - checagem de migrações pendentes;
  - execução de testes;
  - gate de cobertura >= 85%.
- Documentação operacional:
  - smoke test;
  - runbook;
  - checklist de release.

## Validações Executadas
- `python -m compileall app`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test app --settings=simulador_operacional.settings_test`

## Riscos / Observações
- Dependência de CDN externa para `chart.js` (há fallback de interface, mas sem gráfico).
- Recomenda-se smoke test completo após deploy.

## Tag Sugerida
- `v1.0.0-rc1`
