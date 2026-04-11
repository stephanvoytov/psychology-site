#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
python manage.py create_admin
cd /opt/render/project/src
source .venv/bin/activate
python manage.py shell -c "from django.db import connections; print(connections['default'].settings_dict['NAME'])"
python manage.py shell -c "from django.db import connections; print(connections['default'].settings_dict['HOST'])"