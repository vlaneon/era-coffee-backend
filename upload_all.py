import os
import cloudinary
import cloudinary.uploader
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from app.models import Product

cloudinary.config(
    cloud_name='dn3ku8mvi',
    api_key='661985634419612',
    api_secret='5q-_forjEjBv1hHgbt3AozlsYAM'
)

MEDIA_DIR = 'media/products/'

for product in Product.objects.all():
    # Пытаемся найти файл по имени товара (латиницей или транслитом)
    # Проще: предполагаем, что файл называется как product.id + расширение
    for ext in ['.jpg', '.png', '.webp', '.jpeg']:
        filename = str(product.id) + ext
        filepath = os.path.join(MEDIA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                result = cloudinary.uploader.upload(f, folder='products', public_id=str(product.id))
                product.image = result['public_id']
                product.save()
                print(f'✅ {product.name} -> {result["public_id"]}')
            break
    else:
        print(f'❌ Не найден файл для {product.name}')