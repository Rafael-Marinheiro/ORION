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

