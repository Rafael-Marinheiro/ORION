@@ -73,26 +73,33 @@ Sistema de simulação operacional para fins pedagógicos, permitindo que grupos

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
