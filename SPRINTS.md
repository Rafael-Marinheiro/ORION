Este documento resume as funcionalidades previstas para cada sprint de desenvolvimento. Ele se baseia no arquivo de documentação `Sprints de programação.docx` localizado em `_documentação/DOC/`.

## Sprint 0 – Preparação
- Revisar documentação e criar backlog inicial.
- Configurar ambiente de desenvolvimento e versionamento.

## Sprint 1 – Autenticação Completa
- Implementar cadastro e edição de usuários pelo administrador.
- Criar fluxo de redefinição de senha.
- Ajustar permissões e papéis (aluno, professor, administrador).  
*Relacionado aos requisitos RF03.*

## Sprint 2 – Configuração do Jogo
- Modelar parâmetros iniciais (capital, estoque, produtos habilitados).
- Tela para ativar ou desativar módulos do jogo.
- Definir regras para eventos aleatórios por rodada.  
*Relacionado aos requisitos RF04, RF05 e RF06.*

## Sprint 3 – Painel do Grupo
- Desenvolver painel com indicadores em tempo real.
- Histórico das decisões e suas consequências.
- Formulário para envio de decisões antes do fechamento de rodada.  
*Relacionado aos requisitos RF07, RF08 e RF09.*

## Sprint 4 – Produção e Estoques
- Implementar cálculo automático de estoque.
- Alertas de risco de ruptura ou desperdício.
- Definir parâmetros de produção (máquinas, capacidade etc.).  
*Relacionado aos requisitos RF10, RF11 e RF12.*

## Sprint 5 – Distribuição e Comercialização
- Cálculo de custos de transporte e prazos.
- Definição de preços/promos por praça.
- Relatórios de vendas e demanda.  
*Relacionado aos requisitos RF13, RF14 e RF15.*

## Sprint 6 – Financeiro e Ranking
Para facilitar o desenvolvimento, recomenda-se dividir esta etapa em três sprints menores:

### Sprint 6a – Resultados Financeiros
- Cálculo de resultados financeiros por rodada (DRE, fluxo de caixa).

### Sprint 6b – Relatórios Comparativos
- Geração de relatórios e gráficos comparativos.

### Sprint 6c – Ranking Dinâmico
- Implementação do ranking dinâmico dos grupos.

*Todos os itens acima estão ligados aos requisitos RF16, RF17 e RF18.*

## Sprint 7 – Eventos Aleatórios
- Sorteio e aplicação automática de eventos com probabilidades.
- Notificação imediata do impacto aos grupos.  
*Relacionado aos requisitos RF19 e RF20.*

## Sprint 8 – Encerramento da Rodada
- Encerramento automático da rodada no horário definido.
- Processamento das decisões e consolidação dos resultados.
- Apresentação de relatórios finais.  
*Relacionado aos requisitos RF21 e RF22.*

## Ações Transversais
- Garantir desempenho inferior a 2 s e suporte a 100 usuários simultâneos.
- Documentação de ajuda online e backup automático.
- Aplicar criptografia e controle de permissões.
- Manter compatibilidade com navegadores e dispositivos.
- Escrever código modular preparado para futuras integrações.

## Sprint 17 – Expansão da API
- Abertura completa dos recursos via REST: criar endpoints para todos os modelos relevantes (grupos, decisões, resultados financeiros, eventos etc.) e garantir autenticação.
- Padrão de segurança e autenticação: uso de tokens ou JWT no Django REST Framework para permitir integrações externas de maneira controlada.
- Documentação automática: gerar especificação Swagger/OpenAPI para todos os endpoints, facilitando consultas e testes.

## Sprint 18 – Relatórios e Dashboards Avançados
- Visualizações gráficas: incorporar gráficos (Chart.js ou similar) para exibir comparativos de receita, custos e ranking em tempo real.
- Exportação e filtros: implementar exportação em PDF e Excel e permitir filtros por rodada ou grupo, conforme descrito no documento de telas{line_range_start=82 line_range_end=88 path=_documentação/TXT/Jogo Simulador Operacional - 10_Telas Menus e Relatórios - Semi-Pronto.txt git_url="https://github.com/Rafael-Marinheiro/ORION/blob/main/_documentação/TXT/Jogo Simulador Operacional - 10_Telas Menus e Relatórios - Semi-Pronto.txt#L82-L88"}.
- Notificações: exibir alertas no painel sobre novidades ou resultados da rodada.
*Status: implementado.*

## Sprint 19 – Automação de Rodadas
- Agendamento do encerramento: automatizar o comando fechar_rodadas com tarefas periódicas (Celery ou tarefas do Django) para execução no horário pré-definido.
- Lembretes por e‑mail: envio de avisos aos grupos quando o prazo para submissão de decisões estiver próximo do fim.
- Registro de logs: salvar em histórico os horários das execuções e eventuais falhas de processamento.
*Status: implementado.*

## Sprint 20 – Melhoria de Usabilidade e Interface
- Revisão das telas: aplicar as recomendações do documento de menus e relatórios para menus mais claros, design responsivo e páginas dedicadas de ajuda.
- Aprimoramento do layout: utilizar componentes de frontend modernos para melhorar a experiência em dispositivos móveis e desktop.
- Tutoriais e FAQ: incluir páginas de auxílio rápido, contemplando a exigência de ajuda online dos requisitos não funcionais.
*Status: implementado.*

## Sprint 21 – Testes e Qualidade
- Cobertura de código: criar testes unitários e de integração para modelos, views e API, visando boa cobertura.
- Integração contínua: configurar pipeline (GitHub Actions ou similar) para executar testes a cada push, garantindo estabilidade das futuras releases.
*Status: implementado.*

## Sprint 22 – Empacotamento e Implantação
- Container Docker: preparar imagem do projeto com todas as dependências e documentação de variáveis de ambiente.
- Scripts de deploy: simplificar o processo de implantação, prevendo comandos de migração e carregamento de dados iniciais.
- Configuração de ambientes: separar configurações de produção e desenvolvimento (ex.: arquivos .env).
*Status: implementado.*
## Sprint 23 – Funcionalidades Avançadas
- Investimentos: implementar as categorias detalhadas em “Considerações Investimentos” (marketing, aquisição de máquinas, contratação de RH e aplicações financeiras){line_range_start=1 line_range_end=19 path=_documentação/TXT/Jogo Simulador Operacional - 14_Considerações Investimentos.txt git_url="https://github.com/Rafael-Marinheiro/ORION/blob/main/_documentação/TXT/Jogo Simulador Operacional - 14_Considerações Investimentos.txt#L1-L19"}{line_range_start=40 line_range_end=77 path=_documentação/TXT/Jogo Simulador Operacional - 14_Considerações Investimentos.txt git_url="https://github.com/Rafael-Marinheiro/ORION/blob/main/_documentação/TXT/Jogo Simulador Operacional - 14_Considerações Investimentos.txt#L40-L77"}.
- Múltiplas turmas/jogos: permitir que diferentes jogos ocorram simultaneamente, cada um com suas configurações e ranking.
- Possíveis extensões: preparar base para módulos futuros (Recursos Humanos, Sustentabilidade, integração LMS), seguindo as ideias presentes em “Futuras Melhorias e Possibilidades de Expansão”{line_range_start=42 line_range_end=59 path=_documentação/TXT/Jogo Simulador Operacional - 15_Considerações Finais.txt git_url="https://github.com/Rafael-Marinheiro/ORION/blob/main/_documentação/TXT/Jogo Simulador Operacional - 15_Considerações Finais.txt#L42-L59"}.

*Status: implementado.*

## Sprint 24 – Preparação de Assets e Base
- Criar diretório `static/css/` com `styles.css`.
- No `base.html`, adicionar `{% load static %}` e `<link rel="stylesheet" href="{% static 'css/styles.css' %}">`.
- Definir cores e fontes globais no CSS.
- Inserir rodapé simples no `base.html`.
*Status: não implementado.*

## Sprint 25 – Telas de Login e Registro
- Centralizar formulário em um card Bootstrap.
- Definir largura máxima (~400 px) e bordas com sombra.
- Padronizar mensagens de erro com classes `alert`.
*Status: não implementado.*

## Sprint 26 – Tela Home
- Adicionar logotipo e frase institucional centralizados.
- Incluir botão destacado para login ou acesso ao painel.
- Garantir que o layout funcione em telas menores.
*Status: não implementado.*

## Sprint 27 – Painel do Grupo
- Mostrar indicadores (capital, estoque, máquinas) em cards.
- Organizar formulários (decisões, distribuição) em colunas.
- Converter listagens em tabelas responsivas.
*Status: não implementado.*

## Sprint 28 – Configuração do Jogo e Rodadas
- Agrupar campos em grid para facilitar a leitura.
- Posicionar botões de ação (Salvar/Abrir) alinhados à direita.
- Exibir mensagens de confirmação após salvar.
*Status: não implementado.*

## Sprint 29 – Relatórios Financeiros e Ranking
- Colocar filtros em formulário horizontal.
- Tabelas com cabeçalho fixo e destaques nos totalizadores.
- Gráficos centralizados e responsivos.
*Status: não implementado.*

## Sprint 30 – Páginas de Ajuda
- Usar margens amplas para facilitar a leitura.
*Status: não implementado.*

## Sprint 31 – Componentes Reutilizáveis e Ajustes Finais
- Criar classes personalizadas de botões e alertas.
- Testar todas as telas em 320 px, 768 px e 1200 px.
- Garantir que navbar e rodapé funcionem bem em mobile.
*Status: não implementado.*
