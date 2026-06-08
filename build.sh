#!/usr/bin/env bash
set -o errexit

pip install uv
uv pip install -r requirements.txt

uv run python manage.py collectstatic --noinput
uv run python manage.py migrate --noinput
uv run python manage.py create_admin