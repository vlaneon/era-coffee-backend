import os
import cloudinary
import cloudinary.uploader
import django
from pathlib import Path
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from app.models import Product

cloudinary.config(
    cloud_name='dn3ku8mvi',
    api_key='661985634419612',
    api_secret='5q-_forjEjBv1hHgbt3AozlsYAM'
)

MEDIA_DIR = Path('media/products')

def normalize_name(name):
    # Убираем пробелы, приводим к нижнему регистру, удаляем знаки препинания
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)  # убираем знаки препинания
    name = re.sub(r'\s+', '_', name)      # заменяем пробелы на _
    return name

# Получаем все файлы из папки
files = list(MEDIA_DIR.glob('*.*'))
print(f'Найдено файлов: {len(files)}')

for product in Product.objects.all():
    product_norm = normalize_name(product.name)
    found_file = None
    for f in files:
        file_norm = normalize_name(f.stem)
        # Если нормализованное имя товара содержится в имени файла или наоборот
        if product_norm in file_norm or file_norm in product_norm:
            found_file = f
            break
    if not found_file:
        print(f'❌ Не найден файл для {product.name}')
        continue
    
    print(f'Обработка {product.name} -> {found_file.name}')
    with open(found_file, 'rb') as f:
        result = cloudinary.uploader.upload(f, folder='products', public_id=str(product.id))
        product.image = result['public_id']
        product.save()
        print(f'✅ Загружено: {result["public_id"]}')