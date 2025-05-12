from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/verify-product-code/', views.verify_product_code, name='verify_product_code'),
    path('test/', views.my_custom_admin_view, name='my_custom_admin_view'),
    path('create/', views.create_data, name='create_product_code_checks'),
]