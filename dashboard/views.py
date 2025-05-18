from multiprocessing import context
import re
from django.shortcuts import render
from django.http import HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import requests
from rest_framework.decorators import api_view, throttle_classes
from .throttling import ProductCodeCheckThrottle
import os
from dashboard.forms import SearchForm
from .models import Product, ProductCodeCheck, UserInfo, Category, Buyer
from .utils import get_client_ip, get_location_from_ip, get_geojson_data, get_unique_part_products, get_product_check_stats, round_num, get_category_summary
from user_agents import parse
import json
import logging
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Sum, F
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from .forms import MapFilterForm
from django.utils.html import format_html
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder



import folium
from folium.plugins import MarkerCluster


logger = logging.getLogger(__name__)
from user_agents import parse

def get_top_buyers():
    """Get top 5 buyers based on their product purchases"""
    return Buyer.objects.annotate(
        total_products=Count('product', distinct=True),
        total_quantity=Sum('product__quantity')
    ).order_by('-total_products')[:5]


def index(request):
    if request.method == 'POST':
        product_code = request.POST.get('pcode')
        phone_number = request.POST.get('phone_number')
        print(phone_number)
        print(product_code)
        
        if Product.objects.filter(product_code=product_code).exists():
            product = Product.objects.get(product_code=product_code)
            
            # Get client information
            ip_address = get_client_ip(request)
            location = get_location_from_ip(ip_address)
            ua_string = request.META.get('HTTP_USER_AGENT', '')
            user_agent = parse(ua_string)
            device_type = "PC" if user_agent.is_pc else "Mobile" if user_agent.is_mobile else "Tablet" if user_agent.is_tablet else "Unknown"   

            # Check if this is the first verification
            is_first = not ProductCodeCheck.objects.filter(product=product).exists()
            
            if is_first:
                # Create UserInfo
                user_info = UserInfo.objects.create(
                    ip_address=ip_address,
                    location=location.get('country', 'Unknown'),
                    device_type=device_type,
                    is_bot=user_agent.is_bot,
                    browser=user_agent.browser.family,
                    browser_version=user_agent.browser.version_string,
                    os=user_agent.os.family,
                    os_version=user_agent.os.version_string,
                    device_family=user_agent.device.family,
                    country_short=location.get('countryCode', 'Unknown'),
                    country=location.get('country', 'Unknown'),
                    region=location.get('regionName', 'Unknown'),
                    city=location.get('city', 'Unknown'),
                    latitude=location.get('lat', 'Unknown'),
                    longitude=location.get('lon', 'Unknown'),
                    phone_number=phone_number
                )
                
                # Create ProductCodeCheck
                check = ProductCodeCheck.objects.create(
                    product=product,
                    user_info=user_info,
                )
                
                context = {
                    'product': product,
                    'verification': {
                        'timestamp': check.checked_at,
                        'device_type': user_agent.device.family,
                        'location': location
                    }
                }
                return render(request, 'dashboard/certificate.html', context)
            else:
                return render(request, 'dashboard/used.html')
        else:
            return render(request, 'dashboard/404.html')
    else:
        context = {'form': SearchForm()}
        return render(request, 'dashboard/index.html')

@csrf_exempt
@api_view(['POST'])
@throttle_classes([ProductCodeCheckThrottle])
def verify_product_code(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        product_code = data.get('product_code')
        phone_number = data.get('phone_number')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

    if not product_code:
        return JsonResponse({'status': 'error', 'message': 'Product code is required'}, status=400)
    
    if not phone_number:
        return JsonResponse({'status': 'error', 'message': 'Phone number is required'}, status=400)

    try:
        with transaction.atomic():
            product = Product.objects.get(product_code=product_code)
            # product.seen_count += 1
            # product.save()
            # Get client information
            ip_address = get_client_ip(request)
            location = get_location_from_ip(ip_address)
            user_agent = parse(request.META.get('HTTP_USER_AGENT', ''))
            device_type = user_agent.device.family
            print("#######################3")
            print(user_agent.device)

            # Create or get UserInfo
            user_info, created = UserInfo.objects.get_or_create(
                ip_address=ip_address,
                defaults={
                    'location': location.get('country', 'Unknown'),
                    'device_type': device_type,
                    'is_mobile': user_agent.is_mobile,
                    'is_tablet': user_agent.is_tablet,
                    'is_pc': user_agent.is_pc,
                    'is_bot': user_agent.is_bot,
                    'browser': user_agent.browser.family,
                    'browser_version': user_agent.browser.version_string,
                    'os': user_agent.os.family,
                    'os_version': user_agent.os.version_string,
                    'device_family': user_agent.device.family,
                    'country_short': location.get('countryCode', 'Unknown'),
                    'country': location.get('country', 'Unknown'),
                    'region': location.get('regionName', 'Unknown'),
                    'city': location.get('city', 'Unknown'),
                    'latitude': location.get('lat', 'Unknown'),
                    'longitude': location.get('lon', 'Unknown'),
                    'phone_number': phone_number
                }
            )
            
            if not created and not user_info.phone_number:
                user_info.phone_number = phone_number
                user_info.save()

            # Create ProductCodeCheck
            is_first = not ProductCodeCheck.objects.filter(product=product).exists()
            check = ProductCodeCheck.objects.create(
                product=product,
                user_info=user_info,
            )


            return JsonResponse({
                'status': 'success',
                'message': 'Product code verified successfully',
                'product': {
                    'code': product.product_code,
                    'category': product.category.name,
                    'description': product.description,
                    'production_date': product.prod_date.strftime('%Y-%m-%d'),
                    'expiration_date': product.exp_date.strftime('%Y-%m-%d'),
                    'lot_number': product.lot_number,
                    'treatment': product.treatment,
                    'germination': product.germination,
                    'purity': product.purity
                },
                'verification': {
                    'is_first': is_first,
                    'timestamp': check.checked_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'device_type': device_type,
                    'location': location
                }
            })

    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)
    except Exception as e:
        logger.error(f"Error verifying product code: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)


def get_country_flag_url(country_code: str, size: str = "64x48") -> str:
    """
    Generate a flag image URL for a given country code using FlagCDN.
    
    Parameters:
        country_code (str): ISO Alpha-2 country code (e.g., 'ir', 'us').
        size (str): Optional flag size in format 'widthxheight' (e.g., '64x48', '128x96').
    
    Returns:
        str: URL of the flag image.
    
    Raises:
        ValueError: If country_code is not 2 characters.
    """
    if len(country_code) != 2:
        raise ValueError("Country code must be 2 characters (ISO Alpha-2).")
    
    country_code = country_code.lower()
    print(country_code)
    if country_code == 'sp':
        country_code = 'es'
    return f"https://flagcdn.com/{size}/{country_code}.png"

def dashboard_callback(request, context):

    # get 3 most viewed category by productcodecheck and return category name 
    most_viewed_category = ProductCodeCheck.objects.values('product__category').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:3]


    # Get date range
    eend_date = timezone.now()
    sstart_date = eend_date - timedelta(days=30)  # Last 30 days

    # Get verification statistics
    total_verifications = ProductCodeCheck.objects.count()
    checked_products = ProductCodeCheck.objects.values('product').count()
    unique_user_info = UserInfo.objects.count()

    # Get daily verification counts
    daily_verifications = ProductCodeCheck.objects.filter(
        checked_at__range=(sstart_date, eend_date)
    ).annotate(
        date=TruncDate('checked_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Get category statistics
    category_stats = []
    for category in Category.objects.all():
        product_count = Product.objects.filter(category=category).count()
        verification_count = ProductCodeCheck.objects.filter(product__category=category).count()
        category_stats.append({
            'name': category.name,
            'product_count': product_count,
            'verification_count': verification_count
        })
    
    # Sort by product count
    category_stats = sorted(category_stats, key=lambda x: x['product_count'], reverse=True)

    # Get device type statistics
    device_stats = UserInfo.objects.values('device_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Get country statistics
    country_stats = UserInfo.objects.values('country', 'country_short').annotate(
        count=Count('id')
    ).order_by('-count')[:3]  # Top 10 countries

    country_cards = []
    for country in country_stats:
        country_cards.append({
            'title': country['country'],
            'metric': country['count'],
            'icon': 'flag',
            'flag': get_country_flag_url(country['country_short'], '64x48')
            # 'flag': '/static/images/flags/{}.png'.format(country['country_short'])
        })


    # Get recent verifications
    recent_verifications = ProductCodeCheck.objects.select_related(
        'product', 'user_info'
    ).order_by('-checked_at')[:10]

    # Get top buyers
    top_buyers = get_top_buyers()
    
    # Get top viewed products
    top_viewed_products = "get_top_viewed_products()"
    
    # Get top categories
    sort_by = request.GET.get('category_sort', 'product_count')
    top_categories = get_top_categories()

    total_views = round_num(ProductCodeCheck.objects.count())
    total_users = round_num(UserInfo.objects.count())
    total_products = round_num(Product.objects.count())

    cards = [
        {
            'title': 'Verifications',
            'metric': total_verifications,
            'icon': '/static/images/icons/verify.svg',
            'footer': 'Total number of verifications',
            'border_color': '#1D2939',
        },
        {
            'title': 'Products',
            'metric': total_products,
            'icon': '/static/images/icons/product.svg',
            'footer': 'Total products',
            'border_color': '#EA9931',
        },
        {
            'title': 'Checked Products',
            'metric': checked_products,
            'icon': '/static/images/icons/verify2.svg',
            'footer': 'Total unique products',
            'border_color': '#EA9931',
        },
        {
            'title': 'Users',
            'metric': unique_user_info,
            'icon': '/static/images/icons/users.svg',
            'footer': 'Total unique user info',
            'border_color': '#009975',
        }
    ]


    context.update({
        'total_verifications': total_verifications,
        'checked_products': checked_products,
        'total_products': total_products,
        'unique_users': unique_user_info,
        'daily_verifications': list(daily_verifications),
        'category_stats': category_stats,
        'device_stats': device_stats,
        'country_stats': country_stats,
        'recent_verifications': recent_verifications,
        'start_date': sstart_date,
        'end_date': eend_date,
        'cards': cards,
        'top_buyers': top_buyers,
        'country_cards': country_cards,
        'top_viewed_products': "top_viewed_products",
        'top_categories': top_categories,
    })


    return context

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


@staff_member_required
def my_custom_admin_view(request):
    return render(request, "dashboard/my_dashboard.html")



# @staff_member_required
# def map_view(request):
#     geojson_data = requests.get(
#         "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/world_countries.json"
#     ).json()

#     m = folium.Map(tiles="cartodbpositron", world_copy_jump=True, zoom_start=3)

#     countries_with_data = list(ProductCodeCheck.objects.values_list("user_info__country", flat=True).distinct())

#     filtered_geojson = {
#         "type": "FeatureCollection",
#         "features": [
#             feature for feature in geojson_data["features"]
#             if feature["properties"]["name"] in countries_with_data  
#         ]
#     }
#     folium.GeoJson(
#         filtered_geojson,
#         name="Countries with Data",
#         style_function=lambda feature: {
#             "fillColor": "#b6dbd5",  
#             "color": "#4a635f",
#             "weight": 1,
#             "fillOpacity": 0.3,  
#         },
#         tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Country"]), 
#     ).add_to(m)

    
#     # Add markers for each ProductCodeCheck
#     marker_cluster = MarkerCluster().add_to(m)
#     for check in ProductCodeCheck.objects.select_related("user_info"):
#         if check.user_info.latitude != 'Unknown' and check.user_info.longitude != 'Unknown':
#             folium.Marker(
#                 location=[check.user_info.latitude, check.user_info.longitude],
#                 popup=folium.Popup(f"Product: {check.product.product_code}<br>Location: {check.user_info.city}, {check.user_info.country}", max_width=300),
#                 icon=folium.Icon(color="blue", icon="info-sign"),
#             ).add_to(marker_cluster)
    
#     map_html = m._repr_html_()

#     context = admin_site.each_context(request) 
#     context.update({
#         "title": "product on map",
#         'map': map_html,
#     })
#     return render(request, "admin/map_template.html", context)

import logging
from django.utils.dateparse import parse_date
from django.db.models import Q
import requests
import folium
from django.contrib import admin
from datetime import datetime, time
from django.utils.timezone import make_aware



@staff_member_required
def map_view(request):
    try:
        if request.method == 'GET':
                
            m = folium.Map(tiles="cartodbpositron", world_copy_jump=True, zoom_start=5)
            count = 0
            product_code_checks = ProductCodeCheck.objects.all()
            context = admin.site.each_context(request)
            print(request.GET.get("start_date"))
            
            if request.GET.get("product_code"):
                product_code = request.GET.get("product_code")
                product_code_checks = product_code_checks.filter(
                    product__product_code__icontains=product_code
                )
                context.update({
                    "product_code": product_code,
                    "data": product_code_checks,
                })
    
            if request.GET.get("start_date") and request.GET.get("end_date"):
                start_date = request.GET.get("start_date")
                end_date = request.GET.get("end_date")

                start_dt = make_aware(datetime.combine(datetime.strptime(start_date, "%m/%d/%Y").date(), time.min))
                print(start_dt)
                end_dt = make_aware(datetime.combine(datetime.strptime(end_date, "%m/%d/%Y").date(), time.max))
    
    
                product_code_checks = product_code_checks.filter(
                    checked_at__range=(start_dt, end_dt)
                )
                context.update({
                    "start_date": start_date,
                    "end_date": end_date,
                })

            if product_code_checks.exists():
                count = len(product_code_checks)
                countries_with_data = list(
                product_code_checks.values_list("user_info__country", flat=True)
                .distinct()
                .exclude(user_info__country__isnull=True)
                .exclude(user_info__country="")
                )

                

                geojson_data = get_geojson_data()


                filtered_geojson = {
                "type": "FeatureCollection",
                "features": [
                    feature for feature in geojson_data["features"]
                    if feature["properties"]["name"] in countries_with_data  
                    ]
                }

                folium.GeoJson(
                    filtered_geojson,
                    name="Countries with Data",
                    style_function=lambda feature: {
                        "fillColor": "#b6dbd5",
                        "color": "#4a635f",
                        "weight": 1,
                        "fillOpacity": 0.3,
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=["name"],
                        aliases=["Country"]
                    ),
                ).add_to(m)

            # add marker for each product code check
            marker_cluster = MarkerCluster().add_to(m)
            for check in product_code_checks:
                if check.user_info.latitude != 'Unknown' and check.user_info.longitude != 'Unknown':
                    folium.Marker(
                        location=[check.user_info.latitude, check.user_info.longitude],
                        popup=folium.Popup(f"Product: {check.product.product_code}<br>Location: {check.user_info.city}, {check.user_info.country}<br>Device: {check.user_info.device_type}<br>Part: {check.product.part_number}", max_width=300),
                    ).add_to(marker_cluster)

            
            map_html = m._repr_html_()
            print("map_html" if map_html else 'false')
        
            context = admin.site.each_context(request)
            context.update({
                "title": "Products on Map",
                "mapp": map_html,
                "count": count,
            })
            return render(request, "admin/map_template.html", context)
        else:
            return HttpResponseNotAllowed(["GET"], "Only GET requests are allowed for this view.")

    except requests.RequestException as e:
        logger.error(f"Failed to fetch GeoJSON data: {str(e)}")
        context = admin.site.each_context(request)
        context.update({
            "title": "Products on Map",
            "error": "Failed to load map data. Please try again later."
        })
        return render(request, "admin/map_template.html", context)
    
    except Exception as e:
        logger.error(f"Unexpected error in map_view: {str(e)}")
        print(f"Unexpected error in map_view: {str(e)}")
        context = admin.site.each_context(request)
        context.update({
            "title": "Products on Map",
            "error": "An unexpected error occurred."
        })
        return render(request, "admin/map_template.html", context)



from dashboard.models import ProductCodeCheck, UserInfo, Product
from faker import Faker
from geopy.geocoders import Nominatim
import random

fake = Faker()
geolocator = Nominatim(user_agent="geoapiExercises")


EUROPEAN_COUNTRIES = {
    "Germany": [
        {"city": "Berlin", "lat": 52.5200, "long": 13.4050},
        {"city": "Munich", "lat": 48.1351, "long": 11.5820},
        {"city": "Hamburg", "lat": 53.5511, "long": 9.9937},
    ],
    "France": [
        {"city": "Paris", "lat": 48.8566, "long": 2.3522},
        {"city": "Lyon", "lat": 45.7640, "long": 4.8357},
        {"city": "Marseille", "lat": 43.2965, "long": 5.3698},
    ],
    "Italy": [
        {"city": "Rome", "lat": 41.9028, "long": 12.4964},
        {"city": "Milan", "lat": 45.4642, "long": 9.1900},
        {"city": "Naples", "lat": 40.8518, "long": 14.2681},
    ],
    "Spain": [
        {"city": "Madrid", "lat": 40.4168, "long": -3.7038},
        {"city": "Barcelona", "lat": 41.3874, "long": 2.1686},
        {"city": "Valencia", "lat": 39.4699, "long": -0.3763},
    ],
    "Netherlands": [
        {"city": "Amsterdam", "lat": 52.3676, "long": 4.9041},
        {"city": "Rotterdam", "lat": 51.9225, "long": 4.4792},
        {"city": "Utrecht", "lat": 52.0907, "long": 5.1214},
    ]
}

def create_product_code_checks():
    products = Product.objects.all()
    if not products.exists():
        print("No products found in the database.")
        return

    for product in products:
        
        country = random.choice(list(EUROPEAN_COUNTRIES.keys())) 
        city_data = random.choice(EUROPEAN_COUNTRIES[country])  
        latitude = round(city_data["lat"] + random.uniform(-0.05, 0.05), 6)  
        longitude = round(city_data["long"] + random.uniform(-0.05, 0.05), 6)

        user_info = UserInfo.objects.create(
            ip_address=fake.ipv4(),
            location = country,
            device_type=random.choice(["Mobile", "Tablet", "PC"]),
            is_mobile=random.choice([True, False]),
            is_tablet=random.choice([True, False]),
            is_pc=random.choice([True, False]),
            is_bot=random.choice([True, False]),
            browser=fake.user_agent(),
            browser_version=f"{random.randint(1, 99)}.{random.randint(0, 9)}",
            os=random.choice(["Windows", "macOS", "Linux", "Android", "iOS"]),
            os_version=f"{random.randint(1, 15)}.{random.randint(0, 9)}",
            device_family=random.choice(["iPhone", "Samsung", "Xiaomi", "Huawei", "OnePlus", "Dell", "HP"]),
            country_short=country[:2].upper(),
            country=country,
            region=fake.state(),
            city=city_data["city"],
            latitude=str(latitude),
            longitude=str(longitude),
        )
        

        ProductCodeCheck.objects.create(
            product=product,
            checked_at=fake.date_time_this_year(),
            user_info=user_info,
        )
        print('mew record created')

    print("ProductCodeCheck records created successfully!")
    return "ProductCodeCheck records created successfully!"

def create_data(request):
    data = create_product_code_checks()
    return JsonResponse({'status': 'success', 'data': data})

def parts_view(request):
    try:
        if request.method == 'GET':
            context = admin.site.each_context(request)
            category_id = request.GET.get('category')
            print(category_id)
            parts = get_unique_part_products(category_id=category_id)
            
            # "http://127.0.0.1:8000/admin/dashboard/product/?=123"
            table_rows = []
            for part in parts:
                url = reverse('admin:dashboard_product_changelist') + f'?part_number={part.part_number}'
                btn = format_html('<a href={}><button type="button" class="w-full rounded-lg border border-sky-800 bg-white px-3 py-2 text-sm font-medium text-gray-900 hover:bg-sky-200 hover:text-primary-700 focus:z-10 focus:outline-none focus:ring-4 focus:ring-gray-100 sm:w-auto">View details</button></a>', url)
                stats = get_product_check_stats(part.part_number),
                checked = stats[0]['checked']
                unchecked = stats[0]['unchecked']
                row = [
                    format_html('<a class="text-sky-600" href="{}">{}</a>', url, part.part_number),
                    part.buyer.full_name if part.buyer else "-",
                    part.modification_date.strftime("%Y-%m-%d"),
                    part.quantity,
                    checked,
                    unchecked,
                    part.note if part.note else "-",
                    btn
                ]
                table_rows.append(row)
            context.update({
                'parts': parts,
                'table': {
                        "headers": ["Part Number", "Buyer", "Modification Date", "quantity", "Checked", "UnChecked", "Note", ' '],
                        "rows":table_rows
                    }
            })
            return render(request, "admin/parts_template.html", context)

    except Exception as e:
        print(e)
        return 'aa'
        # prepare this view to return eror 
        

def sms_view(request):
    try:
        if request.method == 'GET':
            context = admin.site.each_context(request)
            context.update({
                "title": "SMS",
            })
            return render(request, "admin/sms_template.html", context)
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'unsuccess', 'error': str(e)})



@staff_member_required
def reports_view(request):
    try:
        context = admin.site.each_context(request)
        now = datetime.today().strftime("%Y-%m-%d")
        unique_parts = Product.objects.values('part_number').distinct().count()
        checked_products = Product.objects.filter(code_checks__isnull=False).distinct().count()        
        total_products = Product.objects.count()
        unique_userinfo = UserInfo.objects.distinct().count()
        cateqories = Category.objects.all()
        products_count = Product.objects.count()
        checked_products_count = ProductCodeCheck.objects.count()
        all_buyers = Buyer.objects.annotate(
        checked_products=Count(
            'product',
            filter=Q(product__code_checks__isnull=False),
            distinct=True
        )
    ).order_by('-checked_products')[:10]
        buyer_names = [str(buyer.full_name) for buyer in all_buyers]
        checked_counts = [buyer.checked_products for buyer in all_buyers]
        categories_data = []
        for category in cateqories:
            data = get_category_summary(category.id)
            categories_data.append({
                'name': data['category'],
                'id': category.id,
                'total_products': data['total_products'],
                'unique_parts': data['unique_parts'],
                'verified_products': data['verified_products'],
                'unverified_products': data['unverified_products'],
                'last_updated': data['last_updated'],
                'products': data['products'],
                'most_used_part': data['most_used_part'],
                'most_unused_part': data['most_unused_part'],
                'most_used_country': data['most_used_country'],
            })

        data = {
                'unique_part_numbers': round_num(unique_parts),
                'checked_products': round_num(checked_products),
                'total_products': round_num(total_products),
                'unique_userinfo_records': round_num(unique_userinfo),
            }
        context.update({
            "title": "PickRow App Reports",
            "now": now,
            "card_data": data,
            "categories_data": categories_data,
            "products_count": products_count,
            "checked_products_count": checked_products_count,
            "percentage": float("{:.2f}".format(checked_products_count / products_count * 100)),
            "user_info_count": UserInfo.objects.count(),
            "all_buyers": all_buyers,
            'buyer_names_json': json.dumps(buyer_names, cls=DjangoJSONEncoder, ensure_ascii=False),
            'checked_counts_json': json.dumps(checked_counts, cls=DjangoJSONEncoder, ensure_ascii=False),
        })
        return render(request, "admin/reports_template.html", context)

    except Exception as err :
        print(err)
        return JsonResponse({'status': 'unsuccess', 'error': err})

def export_view(request):
    try:
        if request.method == 'GET':
            context = admin.site.each_context(request)
            context.update({
                "title": "Export Data",
            })
            return render(request, "admin/export_template.html", context)
        if request.method == 'POST':
            # Handle the export logic here
            # For example, you can generate a CSV or Excel file and return it as a response
            # For now, just return a success message
            return JsonResponse({'status': 'success', 'message': 'Export initiated successfully!'})
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'unsuccess', 'error': str(e)})
    
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
from django.db.models import Count
from .models import Product, ProductCodeCheck, UserInfo

def product_report(request, product_id):
    try:
        if request.method == 'GET':
            product = Category.objects.get(id=product_id)
            context = admin.site.each_context(request)
            context.update({
                "title": f"Product Report for {product.name}",
                "product": product,
            })
            return render(request, "admin/product_report_template.html", context)
        elif request.method == 'POST':
            report_type = request.POST.get('report_type')
            product = Product.objects.get(id=product_id)
            report_data = ProductCodeCheck.objects.filter(product=product).select_related('user_info')
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph(f"Product Report for {product.product_code}", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Description: {product.description}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Category: {product.category.name}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Production Date: {product.prod_date.strftime('%Y-%m-%d')}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Expiration Date: {product.exp_date.strftime('%Y-%m-%d')}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Lot Number: {product.lot_number}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Treatment: {product.treatment}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Germination: {product.germination}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Purity: {product.purity}", styles['Normal']))
            elements.append(Spacer(1, 12))
            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{product.product_code}_report.pdf"'
            return response
    except Exception as e:
        print('errore in report')
        print(e)
        return JsonResponse({'status': 'unsuccess', 'error': 'cant generate report'})

