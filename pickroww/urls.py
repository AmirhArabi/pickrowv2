from django.contrib import admin
from django.urls import path, include
from dashboard import views as dashboard

urlpatterns = [
    path("admin/map/", dashboard.map_view, name="admin_map"),
    path("admin/sms/", dashboard.sms_view, name="admin_sms"),
    path("admin/exports/", dashboard.export_view, name="admin_exports"),
    path("admin/parts/", dashboard.parts_view, name="admin_part"),
    path("admin/<int:product_id>/report", dashboard.product_report, name="admin_product_detail"),
    path("admin/reports/", dashboard.reports_view, name="admin_reports"),
    path('admin/', admin.site.urls),
    path('web/', include('web.urls')),
    path('', include('dashboard.urls')),
]
