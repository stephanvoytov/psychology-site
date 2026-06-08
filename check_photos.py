import os
os.environ['SECRET_KEY'] = 'test'
os.environ['YA_PASSWORD'] = 'test'
os.environ['DATABASE_URL'] = 'postgresql://postgres2_oni9_user:I6THUMjbA6k3wcNDhFMaDPGERuD83hM9@dpg-d8j8equq1p3s73ffh3l0-a.frankfurt-postgres.render.com/postgres2_oni9'
os.environ['DJANGO_SETTINGS_MODULE'] = 'lyceum23.settings'

import django; django.setup()
from booking.models import Psychologist

for p in Psychologist.objects.all():
    print(repr(p.name) + ': photo=' + repr(p.photo))
