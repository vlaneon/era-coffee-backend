from rest_framework import serializers
from .models import User, Product, CartItem
from cloudinary.utils import cloudinary_url


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'phone', 'address']


class ProductSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    def get_categories(self, obj):
        return [c.name for c in obj.categories.all()]

    def get_image_url(self, obj):
        if obj.image:
            # Преобразуем CloudinaryResource в строку (public_id)
            public_id = str(obj.image)
            url, options = cloudinary_url(public_id, secure=True)
            return url
        return None

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image_url', 'description',
                  'addons', 'available', 'categories', 'volume',
                  'created_at', 'is_hit']


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'addons', 'total_price', 'added_at']

    def create(self, validated_data):
        user = self.context['request'].user
        product_id = validated_data.pop('product_id')
        product = Product.objects.get(id=product_id)

        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': validated_data.get('quantity', 1)}
        )

        if not created:
            cart_item.quantity += validated_data.get('quantity', 1)
            cart_item.save()

        return cart_item