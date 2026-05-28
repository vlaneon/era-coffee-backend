from rest_framework import serializers
from .models import User, Product, CartItem
from cloudinary.utils import cloudinary_url   # добавьте этот импорт

class ProductSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()   # новое поле

    def get_categories(self, obj):
        return [c.name for c in obj.categories.all()]

    def get_image_url(self, obj):
        if obj.image:
            # obj.image — это public_id (например, "image/upload/v...")
            url, options = cloudinary_url(obj.image, secure=True)
            return url
        return None

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image_url', 'description', 
                  'addons', 'available', 'categories', 'volume', 
                  'created_at', 'is_hit']