from django.contrib import admin
from django import forms
from .models import Product, CartItem
from .models import Order
import json

class ProductForm(forms.ModelForm):
    ADDON_TYPES = [
        ('Сахар', 'Сахар (количество)'),
        ('Корица', 'Корица (добавить/нет)'),
        ('Молоко', 'Молоко (выбор типа)'),
        ('Сироп', 'Сироп (выбор вкуса)'),
        ('Сливки', 'Сливки (количество)'),
        ('Лёд', 'Лёд (количество)'),
    ]
    
    addons_json = forms.JSONField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 8, 'cols': 60}),
        help_text='''
        JSON формат:<br>
        Простые (количество): {"Сахар": 0, "Сливки": 0}<br>
        С подтипами: {"Молоко": {"коровье": 0, "миндальное": 0, "овсяное": 0}, "Сироп": {"ванильный": 0, "карамельный": 0}}<br>
        Без количества: {"Корица": false}
        '''
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.addons:
            self.fields['addons_json'].initial = self.instance.addons

    class Meta:
        model = Product
        fields = '__all__'

    def clean_addons_json(self):
        data = self.cleaned_data['addons_json']
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Невалидный JSON")
        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        addons_data = self.cleaned_data.get('addons_json')
        if addons_data is not None:
            instance.addons = addons_data
        if commit:
            instance.save()
        return instance

class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ['name', 'get_categories', 'price', 'is_hit', 'available', 'created_at']
    list_filter = ['categories', 'is_hit', 'available']
    list_editable = ['is_hit', 'available']
    search_fields = ['name']
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'description', 'price', 'volume')
        }),
        ('Категории и видимость', {
            'fields': ('categories', 'is_hit', 'available')
        }),
        ('Изображение', {
            'fields': ('image',)
        }),
        ('Добавки', {
            'fields': ('addons_json',),
            'description': 'Настройка добавок для этого продукта'
        }),
    )

    def get_categories(self, obj):
        return ", ".join([c.get_name_display() for c in obj.categories.all()])
    get_categories.short_description = 'Категории'

admin.site.register(Product, ProductAdmin)
admin.site.register(CartItem)

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_price', 'status', 'address', 'created_at']
    list_filter = ['status']
    list_editable = ['status']

admin.site.register(Order, OrderAdmin)
