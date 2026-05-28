# app/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from decimal import Decimal
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, Product, CartItem, Order, LoyaltyCard
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserSerializer,
    ProductSerializer,
    CartItemSerializer
)


# Регистрация
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Логин
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            users = User.objects.filter(email=email)
            user = None
            for u in users:
                user = authenticate(username=u.username, password=password)
                if user:
                    break
        except User.DoesNotExist:
            user = None
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Неверный email или пароль'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Профиль пользователя
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Список продуктов
@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    products = Product.objects.filter(available=True)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


# Корзина пользователя
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cart(request):
    if request.method == 'GET':
        cart_items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        addons_data = request.data.get('addons', {})
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Товар не найден'}, status=404)
        
        existing = CartItem.objects.filter(
            user=request.user,
            product=product,
            addons=addons_data
        ).first()
        
        if existing:
            existing.quantity += quantity
            existing.save()
            serializer = CartItemSerializer(existing)
            return Response(serializer.data)
        else:
            cart_item = CartItem.objects.create(
                user=request.user,
                product=product,
                quantity=quantity,
                addons=addons_data
            )
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


# Обновление/удаление элемента корзины
@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
    except CartItem.DoesNotExist:
        return Response({'error': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'PUT':
        quantity = request.data.get('quantity', 1)
        addons_data = request.data.get('addons', None)
        if quantity > 0:
            cart_item.quantity = quantity
            if addons_data is not None:
                cart_item.addons = addons_data
            cart_item.save()
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data)
        else:
            cart_item.delete()
            return Response({'message': 'Товар удален из корзины'})
    
    elif request.method == 'DELETE':
        cart_item.delete()
        return Response({'message': 'Товар удален из корзины'})


# Создание заказа
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    if not cart_items.exists():
        return Response({'error': 'Корзина пуста'}, status=400)
    
    total = sum(item.total_price for item in cart_items)
    promo = request.data.get('promo', '')
    address = request.data.get('address', '')
    payment = request.data.get('payment', '')
    discounts = []
    
    card, _ = LoyaltyCard.objects.get_or_create(user=user)
    
    # Бесплатные напитки (лояльность)
    free_items = request.data.get('free_items', [])
    free_drinks_used = 0
    
    for f in free_items:
        if free_drinks_used >= card.stamps // 10:
            break
        try:
            item = cart_items.get(id=f['itemId'], user=user)
            drink_categories = ['classic', 'ice', 'matcha', 'author']
            item_categories = [c.name for c in item.product.categories.all()]
            if any(c in drink_categories for c in item_categories):
                total -= item.product.price
                free_drinks_used += 1
                discounts.append(f'Бесплатный напиток: {item.product.name} (-{item.product.price}₽)')
        except (CartItem.DoesNotExist, KeyError):
            pass
    
    # 🕐 Счастливые часы (8:00-10:00 и 18:00-20:00)
    from datetime import datetime
    current_hour = datetime.now().hour
    if (8 <= current_hour < 10) or (18 <= current_hour < 20):
        happy_discount = sum(item.total_price for item in cart_items 
                           if any(c.name in ['classic', 'ice', 'matcha', 'author'] for c in item.product.categories.all()))
        happy_discount = happy_discount * Decimal('0.2')
        total -= happy_discount
        discounts.append(f'🕐 Счастливые часы: скидка 20% на напитки (-{round(happy_discount)}₽)')
    
    # 🥐 Комбо "Завтрак бариста": напиток + круассан = скидка 15%
    has_drink = any(item for item in cart_items 
                    if any(c.name in ['classic', 'ice', 'matcha', 'author'] for c in item.product.categories.all()))
    has_croissant = any(item for item in cart_items 
                        if 'круассан' in item.product.name.lower())
    
    if has_drink and has_croissant:
        # Находим самый дешёвый напиток и круассан
        drinks = [i for i in cart_items if any(c.name in ['classic', 'ice', 'matcha', 'author'] for c in i.product.categories.all())]
        croissants = [i for i in cart_items if 'круассан' in i.product.name.lower()]
        if drinks and croissants:
            combo_discount = min(d.total_price for d in drinks) * Decimal('0.15')
            total -= combo_discount
            discounts.append(f'🥐 Комбо "Завтрак бариста": скидка 15% (-{round(combo_discount)}₽)')
    
    # 🍜 Комбо "Обед": суп + напиток = фиксированная скидка
    has_soup = any(item for item in cart_items 
                   if 'суп' in item.product.name.lower() or 'удон' in item.product.name.lower() or 'соба' in item.product.name.lower())
    if has_drink and has_soup:
        total -= Decimal('50')
        discounts.append('🍜 Комбо "Обед": скидка 50₽')
    
    # 🎫 Промокоды
    if promo == 'ERA10':
        total = total * Decimal('0.9')
        discounts.append('🎫 Промокод ERA10: скидка 10%')
    elif promo == 'ERA20':
        total = total * Decimal('0.8')
        discounts.append('🎫 Промокод ERA20: скидка 20%')
    elif promo == 'VKCOFFEE':
        total = total * Decimal('0.85')
        discounts.append('🎫 Промокод VK: скидка 15%')
    elif promo == 'MAXCOFFEE':
        total = total * Decimal('0.85')
        discounts.append('🎫 Промокод Max: скидка 15%')
    
    total = max(total, 0)
    
    # Сохраняем состав
    items_data = []
    for item in cart_items:
        items_data.append({
            'name': item.product.name,
            'price': str(item.product.price),
            'quantity': item.quantity,
            'addons': item.addons,
            'total': str(item.total_price)
        })
    
    order = Order.objects.create(
        user=user,
        total_price=total,
        address=address,
        payment=payment,
        promo=promo,
        items_data=items_data,
        discounts=discounts
    )
    
    # Печати — теперь начисляются только за НАПИТКИ
    stamps_earned = 0
    for item in cart_items:
        item_categories = [c.name for c in item.product.categories.all()]
        if any(cat in ['classic', 'ice', 'matcha', 'author'] for cat in item_categories):
            stamps_earned += item.quantity
    
    card = LoyaltyCard.objects.get(user=user)
    card.stamps += stamps_earned
    card.total_orders += 1
    if free_drinks_used > 0:
        card.stamps = max(0, card.stamps - free_drinks_used * 10)
    card.save()
    
    CartItem.objects.filter(user=user).delete()
    
    return Response({
        'order_id': order.id,
        'status': order.get_status_display(),
        'total': str(total),
        'discounts': discounts,
        'stamps_earned': stamps_earned,
        'total_stamps': card.stamps,
        'free_drinks_used': free_drinks_used,
    })


# История заказов
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    data = []
    for order in orders:
        # Используем сохранённые данные заказа
        data.append({
            'id': order.id,
            'status': order.get_status_display(),
            'status_code': order.status,
            'total': str(order.total_price),
            'address': order.address,
            'payment': order.payment,
            'promo': order.promo or 'Не применялся',
            'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
            'ready_at': order.ready_at.strftime('%d.%m.%Y %H:%M') if order.ready_at else None,
            'items': order.items_data,   # <-- состав заказа
            'discounts': order.discounts,
        })
    return Response(data)


# Обновление статуса заказа (админ)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_order_status(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=404)
    
    new_status = request.data.get('status')
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        if new_status == 'ready':
            order.ready_at = timezone.now()
        order.save()
        return Response({'status': order.get_status_display()})
    return Response({'error': 'Неверный статус'}, status=400)


# Слайдер
@api_view(['GET'])
def slider_products(request):
    products = Product.objects.filter(available=True)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


# Карта лояльности
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loyalty_status(request):
    card, _ = LoyaltyCard.objects.get_or_create(user=request.user)
    return Response({
        'stamps': card.stamps,
        'total_orders': card.total_orders,
        'free_available': card.free_drink_available,
        'next_reward': 10 - card.stamps
    })

#сброс пароля
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Введите email'}, status=400)
    try:
        user = User.objects.get(email=email)
        # В реальном проекте здесь отправка письма со ссылкой
        return Response({'message': 'Инструкция по сбросу пароля отправлена на email (имитация)'})
    except User.DoesNotExist:
        return Response({'error': 'Пользователь с таким email не найден'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    if not user.check_password(old_password):
        return Response({'error': 'Неверный старый пароль'}, status=400)
    user.set_password(new_password)
    user.save()
    return Response({'message': 'Пароль изменён'})