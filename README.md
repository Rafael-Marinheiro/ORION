# Simulador Operacional

## Descrição
Sistema de simulação operacional para fins pedagógicos, permitindo que grupos tomem decisões empresariais em um ambiente simulado com rodadas e rankings.

## Requisitos do Sistema

### 3.1 Requisitos Funcionais (RF)

#### Módulo 1 – Autenticação e Acesso
- RF-01 – O sistema deverá permitir que os usuários realizem login com usuário e senha individuais.
- RF-02 – O sistema deverá validar automaticamente as credenciais inseridas pelo usuário e notificar imediatamente erros de autenticação.
- RF-03 – O sistema deverá permitir ao administrador cadastrar novos usuários e redefinir senhas.

#### Módulo 2 – Configuração do Jogo
- RF-04 – O administrador deverá poder configurar parâmetros iniciais do jogo.
- RF-05 – O sistema deverá permitir ao administrador ativar e desativar módulos específicos.
- RF-06 – O sistema deverá possibilitar o ajuste manual ou automático dos eventos aleatórios por rodada.

#### Módulo 3 – Painel do Grupo
- RF-07 – Cada grupo terá acesso a um painel personalizado com indicadores em tempo real.
- RF-08 – O painel deverá permitir visualizar consequências das decisões anteriores.
- RF-09 – O sistema deve permitir que grupos submetam decisões antes do encerramento da rodada.

#### Módulo 4 – Controle de Estoques e Produção
- RF-10 – Cálculo automático de estoque disponível.
- RF-11 – Geração de alertas automáticos para risco de ruptura ou desperdício.
- RF-12 – Definição de parâmetros de produção.

#### Módulo 5 – Distribuição e Comercialização
- RF-13 – Cálculo automático de custos e prazos de transporte.
- RF-14 – Definição de preços e estratégias promocionais por praça.
- RF-15 – Relatórios detalhados de vendas e demanda.

#### Módulo 6 – Financeiro e Ranking
- RF-16 – Cálculo automático de resultados financeiros por rodada.
- RF-17 – Exibição de relatórios e gráficos financeiros comparativos.
- RF-18 – Ranking dinâmico atualizado automaticamente.

#### Módulo 7 – Eventos Aleatórios
- RF-19 – Aplicação automática de eventos aleatórios com impacto.
- RF-20 – Notificação imediata sobre ocorrência de eventos.

#### Módulo 8 – Encerramento da Rodada
- RF-21 – Encerramento automático da rodada após tempo pré-definido.
- RF-22 – Consolidação e apresentação de relatórios ao encerrar rodada.

### 3.2 Requisitos Não Funcionais (RNF)

#### Desempenho
- RNF-01 – Tempo de resposta inferior a 2 segundos.
- RNF-02 – Suporte a 100 usuários simultâneos.

#### Usabilidade
- RNF-03 – Interface intuitiva e autoexplicativa.
- RNF-04 – Documentação de ajuda online acessível.

#### Disponibilidade e Confiabilidade
- RNF-05 – Taxa de disponibilidade mínima de 99,5%.
- RNF-06 – Backup diário automático.

#### Segurança
- RNF-07 – Acessos criptografados.
- RNF-08 – Controle rigoroso de permissões.

#### Portabilidade e Compatibilidade
- RNF-09 – Compatível com principais navegadores.
- RNF-10 – Funcionalidade em dispositivos móveis e desktops.

#### Manutenção e Evolução
- RNF-11 – Código modular e documentado.
- RNF-12 – Permite integração futura via API.

## Instalação

1. Clone este repositório
2. Crie um ambiente virtual Python:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate  # Windows
   ```
   A pasta `.venv` já está listada no `.gitignore` e não será versionada.
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Registre as tarefas agendadas:
   ```bash
   python manage.py crontab add
   ```

## Uso

1. Configure o banco de dados:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
2. Inicie o servidor:
   ```bash
   python manage.py runserver
   ```
   Também é possível utilizar o atalho abaixo, que encaminha os argumentos
   para o `manage.py`:
   ```bash
   python main.py runserver
   ```
3. Acesse `/register/` para criar uma nova conta ou `/login/` para entrar.
   Administradores podem configurar o jogo em `/config/`.
   Usuários autenticados acessam o painel do grupo em `/painel/`.
   No painel informe a quantidade produzida em cada decisão para atualizar o estoque automaticamente.
   Alertas de ruptura ou desperdício serão exibidos conforme o nível de estoque.
   Utilize o formulário de distribuição para enviar produtos às cidades e registrar custos de transporte automaticamente.
   Consulte o ranking financeiro atualizado em `/ranking/` para comparar o desempenho dos grupos.
   Para dúvidas rápidas acesse a página de ajuda em `/ajuda/`.
   A cada rodada um evento aleatório será sorteado e exibido no painel, podendo alterar custos de produção, transporte ou demanda.
   Administradores podem abrir uma nova rodada em `/abrir_rodada/` definindo a data e hora de encerramento.
   A gestão de grupos é realizada em `/grupos/`, onde é possível criar ou editar grupos existentes.
   Utilize o comando `python manage.py fechar_rodadas` para processar rodadas cujo prazo terminou e aplicar penalidades aos grupos que não enviaram decisões.
   Os comandos `fechar_rodadas` e `enviar_lembretes` são executados automaticamente via `django-crontab`, gerando logs em `agendamentos.log`.
   Gere backups do banco periodicamente executando `python manage.py backupdb`.
  Utilize a API REST em `/api/` para integrar outras aplicações. O ranking financeiro pode ser obtido em `/api/ranking/`.

## Docker

1. Copie o arquivo `.env.example` para `.env` e ajuste as variáveis.
2. Construa a imagem:
   ```bash
   docker build -t simulador-operacional .
   ```
3. Inicie o container:
   ```bash
   docker run --env-file .env -p 8000:8000 simulador-operacional
   ```
   Ou utilize o `docker-compose`:
   ```bash
   docker compose up --build
   ```

## Historico de Sprints

### Implementados
- **Sprint 1 – Autenticacao Completa:** cadastro de usuarios, redefinicao de senha e permissoes.
- **Sprint 2 – Configuracao do Jogo:** parametros iniciais e ativacao de modulos.
- **Sprint 3 – Painel do Grupo:** indicadores em tempo real e envio de decisoes.
- **Sprint 4 – Producao e Estoques:** calculo de estoque e alertas de ruptura.
- **Sprint 5 – Distribuicao e Comercializacao:** custos de transporte e relatorios de vendas.
- **Sprint 6 – Financeiro e Ranking:** resultados financeiros, relatorios comparativos e ranking.
- **Sprint 7 – Eventos Aleatorios:** sorteio automatico de eventos.
- **Sprint 8 – Encerramento da Rodada:** processamento automatico e relatorios finais.
- **Sprint 9 – Configuracao Inicial e Usuarios:** modelos de Grupo e Rodada, gestao em `/grupos/`.
- **Sprint 10 – Painel do Grupo e Decisoes:** painel com indicadores basicos e envio de decisoes.
- **Sprint 11 – Estoques e Producao:** calculo de estoque e alertas automaticos.
- **Sprint 12 – Distribuicao e Comercializacao:** despacho de produtos e custos de transporte.
- **Sprint 13 – Financeiro e Ranking:** consolidacao de resultados e ranking dinamico.
- **Sprint 14 – Eventos Aleatorios e Encerramento:** sorteio de eventos e fechamento das rodadas.
- **Sprint 15 – Requisitos Nao Funcionais:** HTTPS e backups automaticos.
- **Sprint 16 – Revisao e Evolucao:** documentacao e API REST, layout responsivo.
- **Sprint 17 – Expansao da API:** expor todos os recursos via REST e autenticacao segura.
- **Sprint 18 – Relatorios e Dashboards Avancados:** graficos, exportacao e notificacoes.
- **Sprint 19 – Automacao de Rodadas:** agendamentos e lembretes automaticos.

- **Sprint 20 – Melhoria de Usabilidade e Interface:** revisao dos templates com Bootstrap e pagina de ajuda.

- **Sprint 21 – Testes e Qualidade:** testes automatizados e integracao continua.
- **Sprint 22 – Empacotamento e Implantacao:** container Docker e scripts de deploy.
- **Sprint 23 – Funcionalidades Avancadas:** investimentos e multiplos jogos.

### Planejados
- **Sprint 24 – Preparação de Assets e Base:** organização do CSS e inclusão de rodapé.
- **Sprint 25 – Telas de Login e Registro:** card centralizado e mensagens de erro padronizadas.
- **Sprint 26 – Tela Home:** logotipo e acesso ao painel com layout responsivo.
- **Sprint 27 – Painel do Grupo:** indicadores em cards e formulários em colunas.
- **Sprint 28 – Configuração do Jogo e Rodadas:** campos em grid e confirmações.
- **Sprint 29 – Relatórios Financeiros e Ranking:** filtros horizontais e gráficos responsivos.
- **Sprint 30 – Páginas de Ajuda:** margens amplas para leitura.
- **Sprint 31 – Componentes Reutilizáveis e Ajustes Finais:** botões personalizados e testes em várias resoluções.
