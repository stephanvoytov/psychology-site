#!/usr/bin/env bash
set -o errexit

# uv — быстрый pip на Rust (ускорение в 10-50x)
pip install uv
uv pip install -r requirements.txt --system

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py create_admin