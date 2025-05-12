from django.contrib.admin import AdminSite
from django.urls import path

class SecondAdminSite(AdminSite):
    site_header = "پنل ادمین دوم"
    site_title = "مدیریت پیشرفته"
    index_title = "پنل مدیریت سفارشی"

second_admin_site = SecondAdminSite(name='second_admin')

urlpatterns = [
    path('', second_admin_site.urls),
]