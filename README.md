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
   ```
3. Acesse os relatórios financeiros em `http://localhost:8000/financeiro/`
4. Veja o ranking atualizado em `http://localhost:8000/ranking/`
5. Sorteie um evento aleatório em `http://localhost:8000/eventos/`
6. Consulte o resumo de encerramento em `http://localhost:8000/encerramento/`

## Documentação de Sprints
O planejamento completo dos sprints encontra-se em [SPRINTS.md](SPRINTS.md), incluindo a divisão do Sprint 6 em etapas menores (6A, 6B e 6C).