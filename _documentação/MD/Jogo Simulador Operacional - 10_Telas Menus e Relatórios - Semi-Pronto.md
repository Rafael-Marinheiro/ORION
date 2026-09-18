> Extraido de `_documentação/DOC/` preservando tabelas. As formulas e os
> diagramas do documento original sao **imagens coladas**, sem texto: foram
> lidos e transcritos nos blocos marcados abaixo. A fonte de verdade continua
> sendo o `.docx`; este arquivo existe para o conteudo ser pesquisavel e
> versionado.

10. Considerações sobre Telas, Menus e Relatórios

10.1 Estrutura Geral e Acessos

O sistema apresenta um conjunto de telas organizadas conforme o tipo de acesso do usuário (Administrador, CEO do Grupo, Membro do Grupo), com menus modulares, interface amigável e navegação lógica. A arquitetura segue uma abordagem hierárquica que parte da Tela Inicial até as funcionalidades específicas por perfil.

10.2 Sugestão de Telas Principais

Tela Inicial

Exibição da logomarca do sistema e frase institucional

Acesso ao botão de login

Tela de Login

Entrada de e-mail e senha

Direcionamento conforme o tipo de usuário:

Administrador

CEO do Grupo

Membro do Grupo (modo leitura)

10.3 Telas por Tipo de Usuário

Administrador

Tela de Configurações

Cadastro de grupos

Definição do número de rodadas

Configuração de eventos aleatórios

Tela de Gerenciamento do Jogo

Abrir / Fechar rodada

Monitoramento da participação dos grupos

Relatórios:

Relatórios Gerais

Relatórios por Grupo (DRE e Fluxo de Caixa)

Relatórios Comparativos

Visualização de Ranking Geral

🧑‍💼 CEO do Grupo

Tela de Painel Geral do Grupo

Nome do grupo, cidade, rodada atual

Status da rodada e notificações

Botões de acesso rápido para decisões pendentes

Tela de Decisões por Rodada

Decisões de Compras

Decisões de Produção

Decisões de Comercialização

Decisões de Investimentos

Tela de Relatórios Financeiros

Demonstrativo de Resultados (DRE)

Fluxo de Caixa por rodada

Histórico de movimentações

Tela de Relatórios Comparativos

Gráficos comparativos entre grupos

Análise de performance (Lucro, Market Share, Eficiência Operacional)

Tela de Visualização de Rankings

Ranking geral por indicadores

Destaques da rodada

Evolução do grupo ao longo da competição

Membros do Grupo

Acesso ao Painel Geral do Grupo

Visualização das decisões tomadas (modo leitura)

Acesso aos relatórios e gráficos explicativos

Apoio nas estratégias do grupo

10.4 Estrutura de Menus

O sistema contará com um menu lateral ou superior, adaptável a cada tipo de perfil, contendo:

Para CEO do Grupo:

Painel Geral

Decisões por Rodada

Relatórios Financeiros

Relatórios Comparativos

Ranking

Encerramento da Rodada

Ajuda

Para Administrador:

Configuração do Jogo

Gerenciamento do Jogo

Relatórios (Gerais, Por Grupo, Comparativos)

Ranking Geral

Encerrar Rodada

Painel de Controle

Suporte

10.5 Funcionalidades Comuns nas Telas

Exportação em PDF / Excel dos relatórios

Filtros por rodada, grupo ou indicador

Gráficos dinâmicos e tabelas comparativas

Notificações em tempo real

Visual limpo com foco na clareza e na experiência do usuário

10.6 Observações Finais

A inclusão das telas específicas de Painel Geral, Decisões por Rodada, Relatórios Financeiros, Comparativos entre Grupos e Ranking contribui fortemente para:

Maior autonomia dos grupos nas análises estratégicas;

Aprimoramento do processo decisório pedagógico;

Clareza e profundidade na visualização de desempenho, com foco na aprendizagem baseada em dados e feedback contínuo.

```
LOGOMARCA E FRASE INSTITUCIONAL

  Marca: constelacao de tres nos ligados, sobre fundo azul royal.
  Titulo: ORION — Simulador Operacional
  Autoria: By Pio Marinheiro e Rafael Marinheiro
  Frase institucional, em amarelo:
    "Cada decisão é uma peça. Encaixe certo e monte o sucesso"

  Paleta do mockup: azul royal de fundo, creme para texto e caixas,
  amarelo para a frase institucional.
```

```
FLUXO: TELA INICIAL → TELA DE LOGIN

  A tela inicial exibe a logomarca e a frase institucional.
  Uma seta leva a tela de login, com tres elementos empilhados:
    [ Email ]  [ Senha ]  [ Entrar ]
```

```
MAPA DO PERFIL ADMINISTRADOR

  ADMINISTRADOR →  Configuracoes
                     • Cadastro dos grupos
                     • Numero de rodadas
                     • Eventos aleatorios
                 →  Gerenciamento do Jogo
                     • Abrir/Fechar Rodada
                     • Relatorios
```

```
MAPA DO PERFIL CEO

  CEO →  Decisoes
           • Decisoes de Compras
           • Numero de Producao
           • Eventos aleatorios
           • Relatorios
```

```
MAPA DO PERFIL GRUPO

  GRUPO →  Relatorios
             • DRE
             • Fluxo de Caixa
             • Decisoes
             • Ranking
```

```
MAPA DE NAVEGACAO COMPLETO

  Frase institucional no topo.

  TELA INICIAL → TELA DE LOGIN ([E-mail] [Senha] [LOGIN])
       ├──  ADMINISTRADOR
       │      Configuracao: cadastro dos grupos, numero de rodadas,
       │                    eventos aleatorios
       │      Gerenciamento do Jogo: abrir/fechar rodada,
       │                    relatorios gerais (DRE, Fluxo de Caixa),
       │                    relatorios comparativos
       ├──  CEO DO GRUPO
       │      Decisoes: compras, producao, comercializacao
       │      Relatorios: DRE, Fluxo de Caixa, Ranking, Decisoes
       └──  COMPONENTE DO GRUPO
              Relatorios: DRE, Fluxo de Caixa, Ranking, Decisoes
```