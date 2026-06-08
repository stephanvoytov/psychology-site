# AGENTS.md — Сайт психолога (Лицей №23)

## Быстрый старт

```bash
cp .env.example .env   # заполнить SECRET_KEY (обязателен, без fallback)
python manage.py migrate
python manage.py createsuperuser   # или create_admin (кастомная команда)
python manage.py seed_data         # демо-записи (сначала сгенерировать слоты в админке)
python -m pytest booking/tests.py  # или manage.py test booking (96 тестов)
```

## Запуск

```bash
python manage.py runserver 0.0.0.0:8000   # dev-сервер
gunicorn lyceum23.wsgi:application        # production (Render)
```

Переменные окружения — в `.env`, загружаются через `python-dotenv` в `manage.py`.  
**`SECRET_KEY` обязателен**, в коде `os.environ['SECRET_KEY']` — без fallback.

## Архитектура

- **`lyceum23/`** — Django project (settings, root urls, health_check, email_check)
- **`booking/`** — единственное приложение, вся бизнес-логика
- **`templates/`** (в корне, а не в `booking/`) — шаблоны сайта и админки
- **`templates/email/`** — HTML-письма с inline-стилями
- **Статика**: WhiteNoise, `STATICFILES_DIRS = [BASE_DIR / 'static']`

### Модели

| Модель | Связь | Ключевое |
|--------|-------|----------|
| `Psychologist` | has_many `TimeSlot`, `AppointmentType` (M2M) | `email` — для уведомлений |
| `AppointmentType` | `form_type`: `consultation` / `preschool_exam` | Определяет набор полей формы |
| `TimeSlot` | OneToOne → `Appointment` | `unique_together = (psychologist, date, time)` |
| `Appointment` | FK → `TimeSlot` (OneToOne) | `phone`/`parent_phone` — нормализуются при `save()` |

**Phone normalization**: `phone` и `parent_phone` хранятся как `+79161234567`.  
`Appointment.save()` вызывает `normalize_phone()` — учитывать при seed-данных и тестах.  
`format_phone()` → `+7 (916) 123-45-67` для отображения.

### URL-маршруты

| Путь | View | Описание |
|------|------|----------|
| `/` | `home` | Главная |
| `/schedule/` | `choose_psychologist` | Выбор психолога |
| `/schedule/<id>/` | `schedule` | Расписание слотов |
| `/book/<slot_id>/` | `book` | Форма записи (POST) |
| `/success/` | `success` | Страница после записи |
| `/my-appointment/` | `my_appointment` | Инфо/отмена записи |
| `/my-appointment/cancel/` | `cancel_appointment_direct` | Отмена (POST) |
| `/contacts/` | `contacts` | Контакты с fallback без БД |
| `/admin/` | Django admin | Кастомный дашборд |
| `/health/` | `health_check` | Мониторинг |

### Админ-панель (кастомизирована)

- **Дашборд** подменён через monkey-patch `AdminSite.index` в `admin.py`
- Показывает: статистику (сегодня/неделя/свободно), статус email, **блок дубликатов**
- **Дубликаты**: группировка по `phone`, `parent_phone`, `child_name`, `parent_name` (Count > 1). Только будущие записи, дублирующиеся группы (по разным полям для одного набора записей) склеиваются
- User/Group скрыты, массовое удаление отключено (`actions = None`)
- `TimeSlotAdmin` имеет кастомный `change_list_template` + генератор слотов

## Email

- **Асинхронные** — `threading.Thread(daemon=True)`, не блокирует ответ
- **DEBUG=True** → console backend. **Production** → SMTP relay (103.71.21.98:2587) → Яндекс
- BCC: `NOTIFICATION_BCC_LIST = ['voytov.st.vi@gmail.com']`
- Два письма: `send_appointment_notification` + `send_cancellation_notification`
- Шаблоны: `templates/email/new_appointment.html`, `templates/email/cancellation.html`
- **`from_email`**: `settings.DEFAULT_FROM_EMAIL` (stepanvoytov@yandex.ru)
- Заголовки: `"Новая запись: {date} в {time}"` / `"Отмена записи: {date} в {time}"`

## Форма записи

- `AppointmentForm` — динамическая: поля зависят от `form_type` (consultation vs preschool_exam)
- JS-маска телефона в `book.html`: автоформат `+7 (___) ___-__-__`
- Валидация на бэке: `clean_phone()` + `clean_parent_phone()` через `normalize_phone()`
- Два набора полей: `(full_name, who, phone, email, grade, message)` / `(child_name, child_birthdate, kindergarten, address, parent_name, parent_phone)`

## Тесты

```bash
python manage.py test booking                             # все 96 тестов
SECRET_KEY=test-key python manage.py test booking          # CI (тоже)
```

- `tests.py` — модели, формы, views, email, админка — всё в одном файле
- Используют фикстуры `create_psychologist()`, `create_timeslot()`, `create_appointment_type()`
- **CI**: `.github/workflows/ci.yml` — на push/PR в main, ubuntu + python 3.12

## Инструменты разработки

- **Ruff** (linter + formatter) через pre-commit: `.pre-commit-config.yaml`
- **Sentry**: `SENTRY_DSN` из окружения, только production
- **Timezone**: `Europe/Kaliningrad` (UTC+2)

## Развёртывание (Render)

```yaml
# render.yaml
buildCommand: ./build.sh
startCommand: gunicorn lyceum23.wsgi:application --bind 0.0.0.0:$PORT
```

`build.sh` делает: `pip install → collectstatic → migrate → create_admin`

## Ручные команды

```bash
python manage.py seed_data          # демо-записи (нужны слоты в БД)
python manage.py create_admin       # создание админа (используется в build.sh)
```
