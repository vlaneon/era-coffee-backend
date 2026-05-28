import os
import cloudinary
import cloudinary.uploader
import django
from pathlib import Path
import re
import unicodedata

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from app.models import Product

cloudinary.config(
    cloud_name='dn3ku8mvi',
    api_key='661985634419612',
    api_secret='5q-_forjEjBv1hHgbt3AozlsYAM'
)

MEDIA_DIR = Path('media/products')

def slugify(text):
    """Транслитерация и нормализация для сравнения"""
    # Приводим к нижнему регистру, заменяем пробелы и знаки препинания
    text = text.lower()
    # Замена ё на е
    text = text.replace('ё', 'е')
    # Убираем все символы, кроме букв, цифр и пробелов
    text = re.sub(r'[^\w\s]', '', text)
    # Заменяем пробелы на _
    text = re.sub(r'\s+', '_', text)
    return text

# Получаем все файлы из папки с расширениями .webp, .jpg, .png
files = list(MEDIA_DIR.glob('*.webp')) + list(MEDIA_DIR.glob('*.jpg')) + list(MEDIA_DIR.glob('*.png'))
print(f'Найдено файлов: {len(files)}')

# Строим словарь: нормализованное имя файла -> путь к файлу
file_map = {}
for f in files:
    stem = slugify(f.stem)  # нормализуем имя без расширения
    file_map[stem] = f
    print(f'  {stem} -> {f.name}')

for product in Product.objects.all():
    product_slug = slugify(product.name)
    # Ищем файл, где нормализованное имя файла содержит имя товара или наоборот
    best_match = None
    best_score = 0
    for file_slug, file_path in file_map.items():
        # Совпадение по полному вхождению
        if product_slug == file_slug:
            best_match = file_path
            break
        if product_slug in file_slug or file_slug in product_slug:
            score = len(set(product_slug) & set(file_slug))
            if score > best_score:
                best_score = score
                best_match = file_path
    if not best_match:
        print(f'❌ Не найден файл для {product.name} (slug: {product_slug})')
        continue
    
    print(f'✅ Загружаем {product.name} -> {best_match.name}')
    with open(best_match, 'rb') as f:
        # Загружаем в Cloudinary с public_id = product.id
        result = cloudinary.uploader.upload(f, folder='products', public_id=str(product.id))
        product.image = result['public_id']
        product.save()
        print(f'   Загружено: {result["public_id"]}')