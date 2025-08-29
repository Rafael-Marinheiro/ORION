# Etapas de Implementação

Este guia apresenta uma ordem sugerida de implementação para o simulador ORION. Cada etapa sintetiza decisões e regras descritas em `logica_implementação.md` e no material em `_documentação/TXT`.

## 1. Configuração do ambiente e dependências básicas
**Status:** Implementado.
- Preparar ambiente Python e serviços necessários, atendendo a requisitos de segurança, desempenho e compatibilidade.
- Definir variáveis de ambiente, dependências e infraestrutura Docker.

## 2. Modelagem de dados e criação das tabelas principais
**Status:** Parcial – faltam tabelas específicas para produtos, estoques detalhados e matérias-primas.
- Estruturar tabelas de usuários, grupos, rodadas, produtos, estoques, produção, distribuição, financeiro e eventos.
- Garantir relacionamentos e chaves estrangeiras que permitam rastrear ações do jogo.

## 3. Autenticação e gerenciamento de perfis
**Status:** Implementado.
- Implementar cadastro e login com perfis Aluno, CEO e Administrador, incluindo validação de e-mail e criptografia de senha.
- Gerir permissões e fluxo de navegação específico para cada perfil.

## 4. Configuração de jogos
**Status:** Parcial – configuração básica disponível; falta interface completa para produtos habilitados e regras de eventos.
- Criar telas e APIs para definição de grupos, parâmetros iniciais, produtos habilitados, rodadas e eventos aleatórios.
- Controlar capital inicial, máquinas e configuração dos módulos ativos.

## 5. Regras de negócio
**Status:** Parcial – limites e penalidades básicas implementados; faltam cálculos completos de preços, custos e demanda.
- Aplicar limites operacionais de produção, estoques e mão de obra.
- Calcular preços, custos e demanda considerando marketing, logística e eventos.
- Tratar penalidades automáticas para atrasos ou ausência de decisões.

## 6. Módulo de matérias-primas
**Status:** Parcial – apenas controle de quantidade; faltam fornecedores, logística e armazenagem.
- Incluir fornecedores, prazos de entrega, custos logísticos (R$1,50/km com desconto de R$0,50 quando há remessa de produtos para a mesma cidade) e armazenagem (taxa de 2% por rodada).
- Integrar compras com estoques, financeiro e distribuição.

## 7. Módulo de produtos e estoques
**Status:** Parcial – controle simples de estoque; faltam composição, validade e custos de produção.
- Definir composição de cada produto, validade e custos de produção.
- Controlar armazenamento, perdas por vencimento e custo de estocagem.

## 8. Módulo de produção
**Status:** Parcial – capacidade calculada e uso de matéria-prima; faltam registros detalhados e expansão por investimentos.
- Modelar linhas de produção com capacidade, máquinas e mão de obra associada.
- Permitir investimentos para expansão e cálculo de eficiência.

## 9. Módulo de distribuição e vendas
**Status:** Parcial – distribuição e vendas básicas; faltam limites de mercado e efeitos avançados de marketing.
- Gerenciar cidades, limites de mercado, custos de envio e efeitos de marketing.
- Determinar demanda conforme preço, disponibilidade e ações promocionais.

## 10. Eventos aleatórios
**Status:** Implementado.
- Implementar catálogo de eventos com tipo, intensidade e probabilidade.
- Registrar sorteio por rodada e aplicar efeitos imediatos nas operações.

## 11. Investimentos
**Status:** Parcial – categorias disponíveis; faltam regras de retorno e ativação completa nas rodadas.
- Disponibilizar categorias de marketing, máquinas, RH e aplicações financeiras.
- Definir regras de custo, retorno e ativação nas rodadas subsequentes.

## 12. Interfaces e relatórios
**Status:** Parcial – painéis e exportações básicos; faltam dashboards e relatórios avançados.
- Criar painéis diferenciados por perfil com visualização das decisões e resultados.
- Implementar exportações e dashboards para análise comparativa.

## 13. Fechamento de rodada
**Status:** Parcial – processamento automático e penalidades básicas; faltam relatórios completos e ajustes finais.
- Processar automaticamente decisões, aplicar eventos e gerar relatórios.
- Aplicar multas de 10% do caixa para grupos que não informarem decisões.

## 14. Classificação de grupos
**Status:** Parcial – ranking básico calculado; faltam critérios adicionais e desempate completo.
- Calcular ranking com critérios de eficiência operacional, desempenho financeiro, atendimento à demanda e sustentabilidade.
- Utilizar regras de desempate conforme especificado na documentação.

## 15. Considerações finais e roadmap de melhorias futuras
**Status:** Não Implementado.
- Registrar oportunidades de expansão, novos módulos e integração com outras plataformas.
- Coletar feedback de usuários e planejar evolução do simulador.

