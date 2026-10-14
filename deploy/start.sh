#!/bin/sh
set -e
cd /app/simulador_operacional
python manage.py migrate --noinput
# Catalogo do 6, 7, 8 e 9 (produtos, materias-primas, eventos e pracas).
# Idempotente: numa base que ja tem dados, so atualiza o que mudou.
#
# Sem isto, um clone novo sobe com o banco vazio -- sem produto, sem praca
# e sem evento -- e nao da para verificar nada na tela.
python manage.py seed_dados_base
exec gunicorn simulador_operacional.wsgi:application --bind 0.0.0.0:8000
