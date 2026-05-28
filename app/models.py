from django.db import models
from django.contrib.auth.models import AbstractUser

CATEGORY_CHOICES = [
    ('classic', 'Классика'),
    ('slider', 'Слайдер'),
    ('seasonal', 'Сезонное'),
    ('ice', 'Айс кофе'),
    ('matcha', 'Матча'),
    ('author', 'Авторские напитки'),
    ('food', 'Основное меню'),
    ('dessert', 'Десерты'),
]

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username

class Category(models.Model):
    name = models.CharField(max_length=100, choices=CATEGORY_CHOICES, unique=True)
    
    def __str__(self):
        return self.get_name_display()

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True)
    addons = models.JSONField(default=dict, blank=True)
    available = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, blank=True)
    volume = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_hit = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    addons = models.JSONField(default=dict, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

    @property
    def total_price(self):
        return self.quantity * self.product.price

        
class Order(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Принят'),
        ('preparing', 'Готовится'),
        ('ready', 'Можно забирать'),
        ('done', 'Получен'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    items = models.ManyToManyField(CartItem)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')
    address = models.CharField(max_length=300)
    payment = models.CharField(max_length=100)
    promo = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ready_at = models.DateTimeField(blank=True, null=True)
    items_data = models.JSONField(default=list)  
    discounts = models.JSONField(default=list)  

    def __str__(self):
        return f"Заказ #{self.id} - {self.user.username}"


class LoyaltyCard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_card')
    stamps = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} — {self.stamps}/10 печатей"

    @property
    def free_drinks_count(self):
        return self.stamps // 10

    @property
    def free_drink_available(self):
        return self.stamps >= 10