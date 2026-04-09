# 🌿 Сайт психолога — Лицей №23

Django-сайт для записи к школьному психологу.

---

## 📁 Структура проекта

```
lyceum23/
├── manage.py                  # Управление проектом
├── requirements.txt           # Зависимости
├── lyceum23/                  # Настройки Django
│   ├── settings.py            # Конфигурация (БД, ключи)
│   └── urls.py                # Главные URL-маршруты
├── booking/                   # Приложение записи
│   ├── models.py              # Модели: TimeSlot, Appointment
│   ├── views.py               # Логика страниц
│   ├── forms.py               # Форма записи
│   ├── urls.py                # URL-маршруты приложения
│   └── admin.py               # Панель администратора
└── templates/booking/         # HTML-шаблоны
    ├── base.html              # Общий шаблон (шапка, стили)
    ├── home.html              # Главная страница
    ├── schedule.html          # Расписание / выбор времени
    ├── book.html              # Форма записи
    ├── success.html           # Подтверждение записи
    └── contacts.html         # Контакты
```

---

## 🚀 Установка и запуск

### 1. Установите зависимости

```bash
pip install -r requirements.txt
```

> Если возникнет ошибка с `mysqlclient`, установите системную библиотеку:
> - Ubuntu/Debian: `sudo apt install python3-dev default-libmysqlclient-dev`
> - Windows: скачайте .whl с https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient

### 2. Создайте базу данных MySQL

```sql
CREATE DATABASE lyceum23_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Настройте подключение к БД

Откройте файл `lyceum23/settings.py` и укажите свои данные:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lyceum23_db',
        'USER': 'root',          # ← ваш пользователь MySQL
        'PASSWORD': 'пароль',    # ← ваш пароль
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

> **Для быстрого теста без MySQL** — раскомментируйте блок с SQLite в settings.py

### 4. Примените миграции (создайте таблицы)

```bash
python manage.py migrate
```

### 5. Создайте администратора

```bash
python manage.py createsuperuser
```

Введите логин, email и пароль.

### 6. Запустите сервер

```bash
python manage.py runserver
```

Сайт будет доступен по адресу: **http://127.0.0.1:8000**

---

## ⚙️ Как пользоваться

### Добавить свободные слоты (расписание)

1. Зайдите в панель администратора: **http://127.0.0.1:8000/admin/**
2. Войдите с данными, которые указали при `createsuperuser`
3. Перейдите в раздел **«Временные слоты»**
4. Нажмите **«Добавить временной слот»**
5. Укажите дату и время — галочка «Доступен» должна быть установлена

### Просмотр записей

В панели администратора → раздел **«Записи»** — все заявки от учеников и родителей.

### Отменить или освободить слот

В разделе **«Временные слоты»** можно прямо в списке снять или поставить галочку «Доступен».

---

## ✏️ Что легко изменить

| Что изменить | Где |
|---|---|
| Имя психолога, кабинет, телефон | `templates/booking/contacts.html` |
| Текст на главной странице | `templates/booking/home.html` |
| Цвета сайта | `templates/booking/base.html` → блок `:root { }` |
| Поля формы записи | `booking/forms.py` и `booking/models.py` |
| Название лицея | `templates/booking/base.html` → тег `.logo` |

---

## 🔒 Перед запуском на сервере

В файле `settings.py`:

```python
DEBUG = False
SECRET_KEY = 'сгенерируйте-новый-ключ'
ALLOWED_HOSTS = ['ваш-домен.ru', 'www.ваш-домен.ru']
```

Сгенерировать ключ: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
