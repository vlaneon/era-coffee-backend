from django.urls import path
from . import views

urlpatterns = [
    path('api/register/', views.register, name='register'),
    path('api/login/', views.login, name='login'),
    path('api/profile/', views.profile, name='profile'),
    path('api/cart/', views.cart, name='cart'),
    path('api/cart/<int:item_id>/', views.cart_item, name='cart_item'),
    path('api/products/', views.product_list, name='products'),
    # path('api/products/add/', views.add_product, name='add_product'),
    # path('api/products/<int:product_id>/', views.delete_product, name='delete_product'),
    path('api/orders/create/', views.create_order, name='create_order'),
    path('api/loyalty/', views.loyalty_status, name='loyalty_status'),
    path('api/orders/history/', views.order_history, name='order_history'),
    path('api/orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('api/password-reset/', views.password_reset, name='password_reset'),
    path('api/profile/change-password/', views.change_password, name='change_password'),
    path('api/test-cloudinary/', views.test_cloudinary, name='test_cloudinary'),
]