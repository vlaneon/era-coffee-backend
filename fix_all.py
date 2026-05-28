import os
import cloudinary
import cloudinary.uploader
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from app.models import Product

# --- НАСТРОЙКИ CLOUDINARY (ПРОВЕРЬТЕ ВАШИ ДАННЫЕ) ---
cloudinary.config(
    cloud_name='dn3ku8mvi',
    api_key='661985634419612',
    api_secret='5q-_forjEjBv1hHgbt3AozlsYAM'
)

MEDIA_DIR = Path('media/products')

# --- ЯВНОЕ СООТВЕТСТВИЕ НАЗВАНИЯ ТОВАРА И ФАЙЛА ---
# Сюда я добавил все пары из ваших логов, включая те, что раньше не работали.
MAPPING = {
    'Эспрессо': 'эспрессо.webp',
    'Фильтр-кофе': 'филтр_кофе.webp',  # <- заметил, что файл без дефиса
    'Американо': 'американо.webp',
    'Американо на молоке': 'американо_на_молоке.webp',
    'Латте': 'латте.webp',
    'Капучино': 'капуч.webp',
    'Флэт Уайт': 'флэтуайт.webp',
    'Раф': 'раф.webp',
    'Айс Американо': 'айс_американо.webp',
    'Айс Латте': 'айс_латте.webp',
    'Айс Латте Черничный': 'айс_латте_черника.webp',
    'Айс Раф Банановый': 'раф.webp',
    'Бамбл': 'бамбл_карамел.webp',
    'Эспрессо Тоник': 'эспрессо_тоник.webp',
    'Матча Классический': 'матча_классический.webp',
    'Матча Клубничный': 'матча_клубничный.webp',
    'Матча Дыня-Черника': 'матча_дыня_черникаэ.webp',
    'Айс Матча Банановый': 'айс_матча_бананэ.webp',
    'Айс Матча Земляника-Роза': 'айс_матча_замляникароза.webp',
    'Айс Матча Черничный': 'айс_матча_черника.webp',
    'Лимонад Молоко Единорога': 'limonade-milk_VKWUaT9.webp',
    'Панна-кота': 'панна_кота.webp',
    'Удон с  курицей и овощами': 'удон.webp',
    'Блинчики  с творогом': 'блинчики.webp',
    'Соба с говядиной': 'соба.webp',
    'Киш с  курицей и грибами': 'киш.webp',
    'Салат с киноа и печеной тыквой': 'салат.webp',
    'Круассан с ветчиной и сыром': 'круассан.webp',
    'Трубочка со сгущенкой': 'трубочка.webp',
    'Сырники': 'сырники.webp',
    'Панна-кота ягодная и Черепаха': 'панна_и_черепаха.webp',
    'Черепаха «капелька»': 'черепаха.webp',
    'Кольцо  заварное с кремом': 'кольцо_заварное.webp',
}

for product in Product.objects.all():
    filename = MAPPING.get(product.name)
    if not filename:
        print(f'⚠️ Пропускаем "{product.name}" — нет пары в MAPPING')
        continue
    filepath = MEDIA_DIR / filename
    if not filepath.exists():
        print(f'❌ Не найден файл {filename} для товара "{product.name}"')
        continue
    print(f'🔄 Загружаем "{product.name}" -> {filename}')
    with open(filepath, 'rb') as f:
        # Здесь самое важное: public_id ставим в products/ID
        result = cloudinary.uploader.upload(f, folder='products', public_id=str(product.id), overwrite=True, invalidate=True)
        product.image = result['public_id']
        product.save()
        print(f'   ✅ Обновлён {product.name}, public_id = {result["public_id"]}')