# Plano de Sprints

## 0 – Preparação
- Configurar ambiente de desenvolvimento e versionamento.

## 1 – Autenticação Completa
- Implementar cadastro e edição de usuários pelo administrador.
- Criar fluxo de redefinição de senha.
- Ajustar permissões e papéis (aluno, professor, administrador).
*RF-03*

## 2 – Configuração do Jogo
- Modelar parâmetros iniciais (capital, estoque, produtos habilitados).
- Tela para ativar ou desativar módulos do jogo.
- Definir regras para eventos aleatórios por rodada.
*RF-04*, *RF-05*, *RF-06*

## 3 – Painel do Grupo
- Desenvolver painel com indicadores em tempo real.
- Histórico das decisões e suas consequências.
- Formulário para envio de decisões antes do fechamento de rodada.
*RF-07*, *RF-08*, *RF-09*

## 4 – Produção e Estoques
- Implementar cálculo automático de estoque.
- Alertas de risco de ruptura ou desperdício.
- Definir parâmetros de produção (máquinas, capacidade etc.).
*RF-10*, *RF-11*, *RF-12*

## 5 – Distribuição e Comercialização
- Cálculo de custos de transporte e prazos.
- Definição de preços/promos.
- Relatórios de vendas e demanda.
*RF-13*, *RF-14*, *RF-15*

## 6A – Resultados Financeiros
- Implementar o cálculo do DRE e fluxo de caixa por rodada.
- Preparar testes e validações para garantir a consistência desses cálculos.
*RF-16*

## 6B – Relatórios e Gráficos
- Gerar os relatórios e gráficos comparativos baseados nos dados financeiros calculados.
- Avaliar a performance e a clareza das informações apresentadas.
*RF-17*

## 6C – Ranking Dinâmico
- Implementar a lógica do ranking de grupos (ordenação, atualização em tempo real, etc.).
- Integrar o ranking com os relatórios, garantindo que alterações financeiras reflitam na classificação.
*RF-18*

## 7 – Eventos Aleatórios
- Sorteio e aplicação automática de eventos com probabilidades.
- Notificação imediata do impacto aos grupos.
*RF-19*, *RF-20*

## 8 – Encerramento da Rodada
- Encerramento automático da rodada no horário definido.
- Processamento das decisões e consolidação dos resultados.
- Apresentação de relatórios finais.
*RF-21*, *RF-22*

## Ações Transversais
- Garantir desempenho (<2 s) e suporte a até 100 usuários.
- Implementar documentação de ajuda online.
- Configurar backup automático e monitoramento da disponibilidade.
- Aplicar criptografia, controle de permissões e compatibilidade com navegadores/dispositivos.
- Manter código modular e preparado para integrações futuras.
