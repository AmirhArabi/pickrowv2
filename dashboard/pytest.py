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
    # واکشی تمام محصولات
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
        

        # ایجاد رکورد ProductCodeCheck
        ProductCodeCheck.objects.create(
            product=product,
            user_info=user_info,
        )
        print('mew record created')

    print("ProductCodeCheck records created successfully!")

# اجرای تابع
if __name__ == "__main__":
    create_product_code_checks()