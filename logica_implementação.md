# Lógica de Implementação do Simulador ORION

## 1. Introdução
- Sistema educacional gamificado para apoiar o ensino de gestão, engenharia de produção e áreas afins, permitindo que alunos gerenciem empresas simuladas e tomem decisões estratégicas. **Status:** Parcialmente implementado
- Objetivo de proporcionar experiência prática de tomada de decisão em ambiente competitivo, explorando indicadores de lucratividade, market share e sustentabilidade. **Status:** Parcialmente implementado
- Alinha-se a metodologias ativas como PBL, aprendizagem baseada em jogos e aprendizagem por projetos, colocando o aluno no papel de protagonista. **Status:** Parcialmente implementado

## 2. Descrição Geral
- Plataforma web modular operando por rodadas, voltada para ensino superior em diferentes contextos e níveis de complexidade. **Status:** Parcialmente implementado
- Permite trabalho offline temporário com sincronização posterior das decisões para o servidor. **Status:** Não implementado
- Restrições: funcionamento em navegadores modernos, necessidade de conexão para envio de decisões e limite inicial de até 12 grupos. **Status:** Parcialmente implementado
- Suposições: acesso via navegador, uso multiplataforma, gestão das rodadas por administrador e possibilidade de customizar cenários. **Status:** Parcialmente implementado

## 3. Requisitos do Sistema
### 3.1 Requisitos Funcionais
- Cadastro e autenticação com perfis de Aluno, Aluno CEO e Administrador, incluindo validação de e-mail e gerenciamento de permissões. **Status:** Implementado
- Configuração de jogos: criação de grupos, parâmetros iniciais, produtos habilitados, número de rodadas e definição de eventos aleatórios. **Status:** Parcialmente implementado
- Gestão de grupos e participantes com atribuição de CEO, inclusão de membros e controle de capital e máquinas. **Status:** Parcialmente implementado
- Registro e envio de decisões por rodada (produção, compras, vendas, distribuição e investimentos), com telas específicas para cada operação. **Status:** Parcialmente implementado
- Processamento automático das rodadas, aplicando eventos, calculando resultados financeiros e atualizando estoques. **Status:** Parcialmente implementado
- Emissão de relatórios e dashboards comparativos para acompanhamento de desempenho por grupo e por rodada. **Status:** Parcialmente implementado
- Gerenciamento de produtos, cidades e eventos com possibilidade de ajustes de demanda e custos logísticos. **Status:** Parcialmente implementado
- Histórico de partidas, exportação de dados em PDF/Excel e manutenção de registros para auditoria. **Status:** Parcialmente implementado

### 3.2 Requisitos Não Funcionais
- Segurança: acesso por login, perfis, criptografia de senha, registro de logs e política de backups periódicos. **Status:** Parcialmente implementado
- Desempenho: resposta média inferior a 3s na interface e processamento de rodada em até 10s para 12 grupos. **Status:** Não avaliado
- Usabilidade: interface intuitiva e responsiva, com possibilidade de suporte multilíngue e acessibilidade. **Status:** Parcialmente implementado
- Compatibilidade: suporte aos principais navegadores e dispositivos desktop/mobile. **Status:** Parcialmente implementado
- Escalabilidade: arquitetura modular prevista para expansão de recursos e número de grupos. **Status:** Parcialmente implementado

## 4. Estrutura de Dados e Relacionamentos
- Tabelas principais: usuários, grupos, rodadas, produtos, estoques, produção, distribuição, financeiro e eventos, com chaves estrangeiras para manter integridade. **Status:** Implementado
- DER simplificado liga usuários → grupos → rodadas → decisões e módulos operacionais, permitindo rastreamento de todas as ações. **Status:** Implementado
- Produtos se relacionam com estoques, produção e distribuição; rodadas com eventos; grupos com ranking e resultados financeiros agregados. **Status:** Implementado

## 5. Regras de Negócio
- Autenticação com e-mail institucional e senha mínima de 8 caracteres, com perfis diferenciados para alunos e administradores. **Status:** Implementado
- Configuração do jogo: 3–12 rodadas, grupos de 3–6 participantes, capital inicial de R$1.000.000, 40 máquinas e definição de módulos ativos. **Status:** Parcialmente implementado
- Submissão de decisões consolidada pelo CEO; atrasos resultam em penalidades de capital e perda de receita potencial. **Status:** Parcialmente implementado
- Penalidades automáticas de 10% do capital e perdas de produtos por decisões não enviadas ou atrasadas. **Status:** Parcialmente implementado
- Limites operacionais baseados em capacidade de produção, estoque disponível e mão de obra. **Status:** Implementado
- Cada rodada representa uma semana com turno de 87 horas; produção depende de máquinas, trabalhadores e disponibilidade de matéria-prima. **Status:** Implementado
- Estoques sem venda geram custo de armazenagem proporcional; vendas dependem de preço, qualidade percebida e marketing por praça. **Status:** Parcialmente implementado
- Sistema calcula receitas, despesas e aplica juros sobre saldos negativos; duas rodadas consecutivas no vermelho restringem investimentos. **Status:** Parcialmente implementado
- Eventos aleatórios podem alterar demanda, custos logísticos, preços de MP ou causar perdas de estoque. **Status:** Implementado
- Demanda por cidade considera preço, disponibilidade e marketing; ranking final usa lucro, market share e caixa como desempate. **Status:** Parcialmente implementado

## 6. Considerações sobre Matérias-Primas
- Quatro tipos de matéria-prima disponíveis, cada uma com fornecedores localizados em cidades específicas e prazos de entrega definidos. **Status:** Parcialmente implementado
- Compras consideram custo unitário da MP e logística (R$1,50/km * quantidade), influenciando o custo final do produto. **Status:** Implementado
- Desconto logístico de R$0,50/km aplicado quando há remessa de produtos para a mesma cidade do fornecedor. **Status:** Parcialmente implementado
- Matérias-primas são recebidas na rodada seguinte à compra; armazenagem custa 2% do valor comprado por rodada. **Status:** Implementado
- Integração com estoques, financeiro e distribuição exige planejamento de suprimentos e logística, evitando rupturas de produção. **Status:** Parcialmente implementado

## 7. Considerações sobre Produtos Comercializados
- Produtos compostos por combinações específicas de matérias-primas, com custo recalculado a cada rodada conforme preço de aquisição e logística. **Status:** Implementado
- Produto A: não perecível; Produto B: perecível com validade de 1 rodada; Produto C: alto custo e não perecível, exigindo maior planejamento. **Status:** Implementado
- Produção bloqueada sem matéria-prima suficiente; apenas unidades inteiras são produzidas por linha específica de máquinas. **Status:** Implementado
- Armazenagem custa 2% do valor de produção de cada unidade estocada e é debitada a cada rodada. **Status:** Parcialmente implementado

## 8. Produção
- Converte MPs em produtos respeitando máquinas específicas, tempo por unidade e disponibilidade de trabalhadores. **Status:** Implementado
- Cada linha possui máquinas exclusivas; capacidade inicial permite até 800 un. de A, 600 de B e 400 de C por rodada, podendo ser ampliada via investimentos. **Status:** Implementado
- Novas máquinas aumentam capacidade a partir da rodada seguinte e exigem dois operadores cada, com impacto no custo fixo de pessoal. **Status:** Implementado
- Produtos têm validade de duas rodadas; vencidos são descartados e geram perdas financeiras. **Status:** Implementado
- Indicadores incluem quantidade produzida, tempo utilizado, eficiência e perdas por vencimento, exibidos em relatórios. **Status:** Parcialmente implementado

## 9. Considerações sobre Cidades/Praças
- Fábrica localizada em Natal-RN; vendas ocorrem em diversas cidades com limites de mercado e elasticidade de demanda própria. **Status:** Parcialmente implementado
- Custo de envio proporcional à distância e volume; limite de venda depende do envio prévio e da capacidade de recepção da praça. **Status:** Parcialmente implementado
- Curva de sensibilidade ao preço distribui demanda entre grupos conforme preço, disponibilidade e marketing local. **Status:** Parcialmente implementado
- Estratégias exigem balancear risco de sobra e falta, considerando eventos que afetam demanda e custos logísticos. **Status:** Parcialmente implementado

## 10. Considerações sobre Eventos Aleatórios
- Introduzem incerteza e afetam todos os grupos igualmente, podendo alterar receitas e custos de forma significativa. **Status:** Implementado
- Um evento é sorteado por rodada com probabilidades predefinidas e dura apenas na rodada atual, podendo ser desativado pelo administrador. **Status:** Implementado
- Eventos podem alterar demanda, custos logísticos, preços de MP ou gerar perdas de estoque, exigindo estratégias de mitigação. **Status:** Implementado
- Implementação inclui tabela de eventos com nome, tipo, intensidade e probabilidade, registrando sorteios por rodada. **Status:** Implementado

## 11. Investimentos
- Categorias: Marketing, Máquinas, Recursos Humanos e Aplicações Financeiras, cada uma com regras específicas de custo e retorno. **Status:** Parcialmente implementado
- Marketing por cidade aumenta demanda até 20% conforme investimento acumulado, utilizando fator logarítmico de saturação. **Status:** Parcialmente implementado
- Máquinas podem expandir até 50% da capacidade inicial; exigem contratação de operadores e são ativadas na rodada seguinte. **Status:** Implementado
- Recursos Humanos: custo fixo de R$1.800/mês por funcionário com possibilidade de ociosidade e impacto em eficiência. **Status:** Parcialmente implementado
- Aplicações financeiras rendem 1,5% por rodada com juros compostos e exigem decisão explícita para aplicação e resgate. **Status:** Parcialmente implementado

## 12. Telas, Menus e Relatórios
- Telas organizadas por perfil (Administrador, CEO, Membro), com permissões específicas e fluxo de navegação dedicado. **Status:** Parcialmente implementado
- Administrador configura jogo, gerencia rodadas, sorteia eventos e acessa relatórios gerais para acompanhamento do desempenho global. **Status:** Parcialmente implementado
- CEO possui painel com status do grupo, decisões de compras/produção/comercialização/investimentos e relatórios comparativos e ranking. **Status:** Parcialmente implementado
- Membros visualizam decisões e relatórios em modo leitura, colaborando na análise estratégica. **Status:** Parcialmente implementado
- Menus incluem Painel, Decisões, Relatórios, Ranking e Ajuda, com exportação de dados e gráficos dinâmicos em desenvolvimento. **Status:** Parcialmente implementado

## 13. Fechamento da Rodada
- Rodadas abertas e prazos definidos pelo administrador, com controle de tempo e notificações aos grupos. **Status:** Parcialmente implementado
- Encerramento automático bloqueia edições e processa decisões, eventos e resultados, gerando relatórios. **Status:** Parcialmente implementado
- Decisões não informadas mantêm valores anteriores, aplicam custos normais e multa de 10% do caixa disponível. **Status:** Implementado
- Processamento envolve validação, execução, atualização de estoques, consolidação financeira, cálculo de ranking e transição para nova rodada. **Status:** Parcialmente implementado

## 14. Classificação dos Grupos
- Avaliação multicritério ponderada considerando Eficiência Operacional, Desempenho Financeiro, Eficiência de Estoques, Satisfação da Demanda e Sustentabilidade. **Status:** Parcialmente implementado
- Pesos ajustáveis; componentes incluem lucratividade, ROA, atendimento ao mercado, market share e indicadores ambientais. **Status:** Parcialmente implementado
- Critérios de desempate: eficiência operacional, satisfação da demanda, sustentabilidade, receita e ordem alfabética do grupo. **Status:** Implementado

## 15. Considerações Finais
- Projeto destaca integração de módulos, eventos aleatórios e feedback automático, oferecendo ambiente de aprendizagem imersivo. **Status:** Parcialmente implementado
- Suporta metodologias ativas, desenvolvendo competências técnicas e socioemocionais por meio de simulações e decisões em grupo. **Status:** Parcialmente implementado
- Avaliação inclui feedback de alunos e docentes, além de indicadores de uso coletados em relatórios. **Status:** Não implementado
- Futuras melhorias: módulos de RH e Sustentabilidade, expansão internacional, dashboards avançados, app mobile e integração com LMS. **Status:** Não implementado
