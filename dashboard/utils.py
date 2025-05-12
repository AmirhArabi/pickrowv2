import IP2Location
import os
from django.utils import timezone
from django.conf import settings
import requests
import json
from .models import Product, ProductCodeCheck, UserInfo, Category
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

def get_client_ip(request):
    """get client ip address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    # check if ip is 127.0.0.1 or localhost return 5.75.198.32
    if ip == "127.0.0.1" or ip == "localhost":
        return "5.75.198.32"
    return ip

def get_location_from_ip(ip):

    """get user location from ip address"""
    db_path = os.path.join("dashboard", "data", "IP2LOCATION-LITE-DB5.BIN")
    if not os.path.exists(db_path):
        return {"error": "Database file not found."}
    
    try:
        db = IP2Location.IP2Location(db_path)
        record = db.get_all(ip)
        
        if not record:
            return {"error": "Invalid IP address or no data found."}
        
        return {
            "countryCode": record.country_short,
            "country": record.country_long,
            "regionName": record.region,
            "city": record.city,
            "lat": record.latitude,
            "long": record.longitude,
        }
    
    except ValueError:
        return {"error": "Invalid IP address format."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
    

# def dashboard_callback(request, context):
#     """
#     Callback function for Unfold dashboard customization.
#     This function is called by Unfold to customize the admin dashboard.
#     """
#     # Get total counts
#     total_products = Product.objects.count()
#     total_categories = Product.objects.values('category').distinct().count()
#     total_checks = ProductCodeCheck.objects.count()
#     total_users = UserInfo.objects.count()
    
#     # Get recent activity
#     recent_checks = ProductCodeCheck.objects.select_related('product', 'user_info').order_by('-checked_at')[:5]
    
#     # Get verification statistics
#     verification_stats = {
#         'total': total_checks,
#         'unique_products': ProductCodeCheck.objects.values('product').distinct().count(),
#         'unique_users': UserInfo.objects.count(),
#     }
    
#     # Add data to context
#     context.update({
#         'total_products': total_products,
#         'total_categories': total_categories,
#         'total_checks': total_checks,
#         'total_users': total_users,
#         'recent_checks': recent_checks,
#         'verification_stats': verification_stats,
#     })
    
#     return context



def get_top_categories(limit=5, sort_by='product_count'):
    """
    Get the top categories based on various sorting criteria
    
    Args:
        limit (int): Number of categories to return
        sort_by (str): Field to sort by, options:
            - 'product_count': Number of products in category
            - 'view_count': Total number of views
            - 'unique_buyers': Number of unique buyers
    
    Returns:
        QuerySet: Top categories with their counts
    """
    if sort_by == 'product_count':
        return Category.objects.annotate(
            product_count=Count('products')
        ).values('id', 'name', 'product_count').order_by('-product_count')[:limit]
    
    elif sort_by == 'view_count':
        return Category.objects.annotate(
            view_count=Count('products__code_checks')
        ).values('id', 'name', 'view_count').order_by('-view_count')[:limit]
    
    elif sort_by == 'unique_buyers':
        return Category.objects.annotate(
            unique_buyers=Count('products__buyer', distinct=True)
        ).values('id', 'name', 'unique_buyers').order_by('-unique_buyers')[:limit]
    
    else:
        # Default to product count if invalid sort_by is provided
        return Category.objects.annotate(
            product_count=Count('products')
        ).values('id', 'name', 'product_count').order_by('-product_count')[:limit]


def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
    
def get_geojson_data():
    db_path = os.path.join("dashboard", "data", "world_countries.json")
    return load_json(db_path)

def get_unique_part_numbers(category_id=None):
    """
    Returns a list of all unique part_number values from the Product model.
    If category_id is provided, only part_numbers from that category are included.
    """
    qs = Product.objects.all()
    if category_id:
        qs = qs.filter(category__id=category_id)
    return list(qs.values_list('part_number', flat=True).distinct())

def get_unique_part_products(category_id=None):
    """
    Returns a list of Products, each with a unique part_number.
    If category_id is provided, only products from that category are included.
    Compatible with all database backends.
    """
    qs = Product.objects.all()
    if category_id:
        qs = qs.filter(category__id=category_id)
    unique_parts = qs.order_by('part_number').values_list('part_number', flat=True).distinct()
    products = []
    for part_number in unique_parts:
        product = qs.filter(part_number=part_number).first()
        if product:
            products.append(product)
    return products



def get_product_check_stats(part_number):
    """    
    Args:
        part_number (int/str):
    """
    try:
        total_products = Product.objects.filter(part_number=part_number).count()
        
        checked_products = Product.objects.filter(
            part_number=part_number,
            code_checks__isnull=False
        ).distinct().count()
        
        unchecked_products = total_products - checked_products
        
        return {
            'success': 'true',
            'checked': checked_products,
            'unchecked': unchecked_products,
            'total': total_products,
            'part_number': part_number
        }
        
    except Exception as e:
        print(f"Error in get_product_check_stats: {str(e)}")
        return {
            'success': "false",
        }