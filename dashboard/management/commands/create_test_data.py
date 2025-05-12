# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Category, Product, UserInfo, ProductCodeCheck, Buyer
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Creates test data for the dashboard app'

    def add_arguments(self, parser):
        parser.add_argument('--categories', type=int, default=5, help='Number of categories to create')
        parser.add_argument('--products', type=int, default=20, help='Number of products to create')
        parser.add_argument('--users', type=int, default=10, help='Number of users to create')
        parser.add_argument('--checks', type=int, default=30, help='Number of product code checks to create')
        parser.add_argument('--buyers', type=int, default=5, help='Number of buyers to create')

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Create categories
        categories = []
        category_names = ['Seeds', 'Fertilizers', 'Pesticides', 'Tools', 'Equipment']
        for i in range(options['categories']):
            name = category_names[i] if i < len(category_names) else f'Category {i+1}'
            prefix = name[:3].upper()
            category = Category.objects.create(
                name=name,
                code_prefix=prefix
            )
            categories.append(category)
            self.stdout.write(f'Created category: {category.name}')
        
        # Create buyers
        buyers = []
        for i in range(options['buyers']):
            buyer = Buyer.objects.create(
                full_name=f'Buyer {i+1}',
                email=f'buyer{i+1}@example.com',
                phone=f'+98{random.randint(1000000000, 9999999999)}',
                address=f'Address {i+1}, City {i+1}',
                note=f'Note for buyer {i+1}'
            )
            buyers.append(buyer)
            self.stdout.write(f'Created buyer: {buyer.full_name}')
        
        # Create products
        products = []
        treatments = ['None', 'Treated', 'Organic', 'Chemical']
        for i in range(options['products']):
            category = random.choice(categories)
            prod_date = timezone.now().date() - timedelta(days=random.randint(1, 365))
            exp_date = prod_date + timedelta(days=random.randint(30, 730))
            
            product = Product.objects.create(
                category=category,
                description=f'Description for product {i+1}',
                prod_date=prod_date,
                exp_date=exp_date,
                lot_number=f'LOT{random.randint(1000, 9999)}',
                treatment=random.choice(treatments),
                germination=f'{random.randint(80, 100)}%',
                purity=f'{random.randint(95, 100)}%',
                part_number=random.randint(1000, 9999),
                modification_date=timezone.now().date(),
                quantity=random.randint(1, 100),
                buyer=random.choice(buyers),
                note=f'Note for product {i+1}'
            )
            products.append(product)
            self.stdout.write(f'Created product: {product.product_code}')
        
        # Create users
        users = []
        countries = ['Iran', 'United States', 'Germany', 'France', 'Japan', 'China', 'India', 'Brazil', 'Australia', 'Canada']
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
        operating_systems = ['Windows', 'macOS', 'Linux', 'iOS', 'Android']
        device_families = ['iPhone', 'Samsung Galaxy', 'iPad', 'MacBook', 'ThinkPad']
        
        for i in range(options['users']):
            country = random.choice(countries)
            is_mobile = random.choice([True, False])
            is_tablet = random.choice([True, False])
            is_pc = not (is_mobile or is_tablet)
            
            device_type = 'Mobile' if is_mobile else 'Tablet' if is_tablet else 'Desktop'
            
            user = UserInfo.objects.create(
                ip_address=f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}',
                location=f'Location {i+1}',
                device_type=device_type,
                is_mobile=is_mobile,
                is_tablet=is_tablet,
                is_pc=is_pc,
                is_bot=False,
                browser=random.choice(browsers),
                browser_version=f'{random.randint(10, 100)}.0',
                os=random.choice(operating_systems),
                os_version=f'{random.randint(10, 15)}.{random.randint(0, 9)}',
                device_family=random.choice(device_families),
                country_short=country[:2].upper(),
                country=country,
                region=f'Region {i+1}',
                city=f'City {i+1}',
                latitude=str(random.uniform(-90, 90)),
                longitude=str(random.uniform(-180, 180)),
                phone_number=f'+98{random.randint(1000000000, 9999999999)}'
            )
            users.append(user)
            self.stdout.write(f'Created user: {user.ip_address}')
        
        # Create product code checks
        for i in range(options['checks']):
            product = random.choice(products)
            user = random.choice(users)
            
            check = ProductCodeCheck.objects.create(
                product=product,
                user_info=user
            )
            self.stdout.write(f'Created product code check: {check.id} for product {product.product_code}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created test data')) 