from django.contrib import admin
from django.urls import path, include
from dashboard import views as dashboard

urlpatterns = [
    path("admin/map/", dashboard.map_view, name="admin_map"),
    path("admin/parts/", dashboard.parts_view, name="admin_part"),
    path("admin/reports/", dashboard.reports_view, name="admin_reports"),
    path('admin/', admin.site.urls),
    path('web/', include('web.urls')),
    path('', include('dashboard.urls')),
]
