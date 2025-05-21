from collections import OrderedDict
from datetime import datetime, timedelta
import os
from django.utils import timezone
from django.conf import settings
import requests
import json
from .models import Product, ProductCodeCheck, UserInfo, Category
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
# from twilio.rest import Client
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader
from django.db.models.functions import TruncMonth

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
    

def get_product_check_record(product_code):
    """
    Check if a product has been verified and return its check record if exists
    
    Args:
        product_code (str): The product code to check
    
    Returns:
        dict: Dictionary containing check status and related records
            {
                'is_checked': bool,
                'check_record': ProductCodeCheck object or None,
                'product': Product object or None,
                'error': str (optional error message)
            }
    """
    try:
        product = Product.objects.get(product_code=product_code)
        
        check_record = ProductCodeCheck.objects.filter(product=product).first()
        
        return {
            'is_checked': check_record is not None,
            'check_record': check_record,
            'product': product
        }
        
    except Product.DoesNotExist:
        return {
            'is_checked': False,
            'check_record': None,
            'product': None,
            'error': 'Product with this code not found'
        }
    except Exception as e:
        return {
            'is_checked': False,
            'check_record': None,
            'product': None,
            'error': str(e)
        }
    

def round_num(number: int):
    """
    Convert a number to a string with K for thousands.
    
    Args:
        number (int): The number to convert.
        
    Returns:
        str: The converted number as a string.
    """
    if number >= 1000:
        return f"{number / 1000:.1f}K"
    return str(number)


# def send_sms(phone_number, msg):
#     account_sid = settings.TWILIO_ACCOUNT_SID
#     auth_token = settings.TWILIO_AUTH_TOKEN
#     try:
#         client = Client(account_sid, auth_token)
#         sms = client.messages.create(
#             body=msg,
#             from_=settings.TWILIO_PHONE_NUMBER,
#             to=phone_number
#         )
#         if sms.error_code:
#             raise Exception(sms.error_message)
#         return sms.sid
#     except Exception as e:
#         print(f"Error sending SMS: {str(e)}")
#         return None

def generate_country_chart(top_countries):
    plt.figure(figsize=(6, 4))
    countries = [item['country'] for item in top_countries]
    visits = [item['visits'] for item in top_countries]
    
    plt.pie(visits, labels=countries, autopct='%1.1f%%')
    plt.title('Top Visitor Countries')
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()
    img_buffer.seek(0)
    
    return ImageReader(img_buffer)


def most_checked_countries_by_category(category_id):
    """
    Get the most checked countries for a specific category.
    Args:
        category_id (int): The ID of the category to filter by.
    Returns:
        QuerySet: A queryset containing the most checked countries for the category.
    """
    data = ProductCodeCheck.objects.filter(product__category_id=category_id) \
        .values('user_info__country') \
        .annotate(total_checks=Count('id')) \
        .order_by('-total_checks')
    if data.exists():
        return data
    else:
        return {}


def get_category_summary(category_id):
    """
    Get summary of all products and parts in a category.

    Args:
        category_id (int): The
            ID of the category to summarize.
    Returns:
        dict: A dictionary containing the summary of products and parts.
    """
    try:
        category = Category.objects.get(id=category_id)
        products = Product.objects.filter(category=category)
        
        total_products = products.count()
        unique_parts = products.values('part_number').distinct().count()
        most_used_country = most_checked_countries_by_category(category_id)
        
        return {
            'category': category.name,
            'total_products': total_products,
            'unique_parts': unique_parts,
            'verified_products': products.filter(code_checks__isnull=False).count(),
            'unverified_products': total_products - products.filter(code_checks__isnull=False).count(),
            'last_updated': products.order_by('-modification_date').first().modification_date.strftime("%Y-%m-%d") if total_products > 0 else None,
            'products': products.values('id', 'part_number', 'category', 'description', 'modification_date'),
            'most_used_part': Product.objects
                .filter(category_id=category_id)
                .annotate(total_checks=Count('code_checks'))  
                .values('part_number') 
                .annotate(total_checks=Count('code_checks'))  
                .order_by('-total_checks')
                .first(),
            'most_unused_part': Product.objects
                .filter(category_id=category_id)
                .annotate(total_checks=Count('code_checks'))  
                .values('part_number') 
                .annotate(
                    total_checks=Count('code_checks'),  
                    total_products=Count('id') 
                )
                .order_by('total_checks')
                .first(),
            'most_used_country': most_used_country if most_used_country else {},
        }
    except Category.DoesNotExist:
        return {
            'error': 'Category not found'
        }
    except Exception as e:
        return {
            'error': str(e)
        }

def monthly_report():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # ایجاد دیکشنری برای همه ماه‌های ۱۲ ماه اخیر
    all_months = OrderedDict()
    current = start_date
    while current <= end_date:
        month_key = current.strftime('%Y-%m')
        all_months[month_key] = 0
        current = current + timedelta(days=32)
        current = current.replace(day=1)
    
    # پر کردن داده‌های موجود
    monthly_data = (
        ProductCodeCheck.objects
        .filter(checked_at__gte=start_date)
        .annotate(month=TruncMonth('checked_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    for item in monthly_data:
        month_key = item['month'].strftime('%Y-%m')
        all_months[month_key] = item['count']
    
    context = {
        'months': json.dumps(list(all_months.keys())),
        'counts': json.dumps(list(all_months.values())),
        'total_checks': sum(all_months.values()),
    }
    return context

