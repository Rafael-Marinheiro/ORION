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
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
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
3. Acesse `/register/` para criar uma nova conta ou `/login/` para entrar.
   Administradores podem configurar o jogo em `/config/`.
   Usuários autenticados acessam o painel do grupo em `/painel/`.
   No painel informe a quantidade produzida em cada decisão para atualizar o estoque automaticamente.
   Alertas de ruptura ou desperdício serão exibidos conforme o nível de estoque.
   Utilize o formulário de distribuição para enviar produtos às cidades e registrar custos de transporte automaticamente.
   Consulte o ranking financeiro atualizado em `/ranking/` para comparar o desempenho dos grupos.
   A cada rodada um evento aleatório será sorteado e exibido no painel, podendo alterar custos de produção, transporte ou demanda.
   Administradores podem abrir uma nova rodada em `/abrir_rodada/` definindo a data e hora de encerramento.
   A gestão de grupos é realizada em `/grupos/`, onde é possível criar ou editar grupos existentes.
   Utilize o comando `python manage.py fechar_rodadas` para processar rodadas cujo prazo terminou e aplicar penalidades aos grupos que não enviaram decisões.
   Gere backups do banco periodicamente executando `python manage.py backupdb`.
   Utilize a API REST em `/api/` para integrar outras aplicações. O ranking financeiro pode ser obtido em `/api/ranking/`.

## Sprints Implementados

- **Sprint 9 – Configuração Inicial e Usuários:** modelos de Grupo e Rodada com formulários administrativos, migrações e página de gestão de grupos em `/grupos/`.
- **Sprint 10 – Painel do Grupo e Decisões:** painel com indicadores básicos e envio de decisões por rodada.
- **Sprint 11 – Estoques e Produção:** cálculo de estoque e alertas automáticos para ruptura ou desperdício.
- **Sprint 12 – Distribuição e Comercialização:** despacho de produtos para cidades e cálculo de custos de transporte.
- **Sprint 13 – Financeiro e Ranking:** consolidação de resultados financeiros e ranking dinâmico em `/ranking/`.
- **Sprint 14 – Eventos Aleatórios e Encerramento:** sorteio de eventos, abertura de rodadas em `/abrir_rodada/` e fechamento com `fechar_rodadas`.

**Sprint 15 – Requisitos Não Funcionais:** HTTPS habilitado, controle de permissões e comando `backupdb` para backups automáticos.

**Sprint 16 – Revisão e Evolução:** documentação aprimorada, API REST disponível em `/api/` e layout responsivo para navegadores e dispositivos móveis.
