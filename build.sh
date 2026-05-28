#!/bin/bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Принудительно очищаем БД перед загрузкой дампа (удалит все данные, но структура останется)
python manage.py flush --noinput

# Загружаем дамп (если файла нет – будет ошибка, и деплой остановится)
python manage.py loaddata db_backup.json --ignorenonexistent

# Создаём суперпользователя заново
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').delete(); User.objects.create_superuser('admin', 'admin@example.com', '123')"