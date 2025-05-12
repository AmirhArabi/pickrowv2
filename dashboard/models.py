from django.db import models
import uuid
from django.db.models import Sum
from django.db import transaction
import random
import time


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code_prefix = models.CharField(max_length=3, unique=True, blank=True, null=True, 
    help_text="3-character prefix for product codes (e.g., 'SEED' for seeds)")

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey("Category", related_name="products", on_delete=models.CASCADE)
    product_code = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    
    description = models.TextField()
    prod_date = models.DateField()
    exp_date = models.DateField()
    lot_number = models.CharField(max_length=100)
    treatment = models.CharField(max_length=255)
    germination = models.CharField(max_length=100)
    purity = models.CharField(max_length=100)

    part_number = models.PositiveIntegerField()
    modification_date = models.DateField(editable=True)
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True, null=True)
    buyer = models.ForeignKey("Buyer", on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if not self.product_code:
            # Generate a structured product code
            self.product_code = self.generate_product_code()
        super().save(*args, **kwargs)

    def generate_product_code(self):

        timestamp_part = int(time.time() % 10**6)  
        random_part = random.randint(100000, 999999) 
        
        code = f"{timestamp_part:06d}{random_part:06d}"
        
        while Product.objects.filter(product_code=code).exists():
            random_part = random.randint(100000, 999999)
            code = f"{timestamp_part:06d}{random_part:06d}"
            
        return code

    def __str__(self):
        return f"{self.category.name} - {self.product_code}"
    
    @property
    def is_checked(self):
        return self.code_checks.exists()

 
    @classmethod
    def create_multiple_products(cls, quantity, **kwargs):
        products = []
        used_codes = set()
        
        for _ in range(quantity):
            product = cls(quantity=quantity, **kwargs)
            
            while True:
                code = product.generate_product_code()
                if code not in used_codes:
                    used_codes.add(code)
                    product.product_code = code
                    break
                    
            products.append(product)
        
        batch_size = 1000
        created_products = []
        
        for i in range(0, len(products), batch_size):
            with transaction.atomic():
                batch = products[i:i + batch_size]
                created_products.extend(cls.objects.bulk_create(batch, batch_size=batch_size))
        
        return created_products


class Buyer(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return self.full_name

    

class ProductCodeCheck(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="code_checks")
    checked_at = models.DateTimeField(auto_now_add=True, editable=True)
    user_info = models.ForeignKey("UserInfo", on_delete=models.SET_NULL, null=True, blank=True, related_name="product_checks")

    class Meta:
        ordering = ["checked_at"]


class UserInfo(models.Model):
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=255)
    device_type = models.CharField(max_length=50, editable=False)
    is_mobile = models.BooleanField(default=False, null=True)
    is_tablet = models.BooleanField(default=False, null=True)
    is_pc = models.BooleanField(default=False, null=True)
    is_bot = models.BooleanField(default=False)
    browser = models.CharField(max_length=100)
    browser_version = models.CharField(max_length=50)
    os = models.CharField(max_length=100)
    os_version = models.CharField(max_length=50)
    device_family = models.CharField(max_length=100)
    country_short = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    latitude = models.CharField(max_length=20)
    longitude = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} - {self.device_type}"
