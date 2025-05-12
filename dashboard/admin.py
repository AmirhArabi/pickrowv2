from django.contrib import admin
from unfold.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html
from .utils import get_unique_part_numbers, get_product_check_record
from django.contrib import messages
from .models import Category, Product, ProductCodeCheck, Buyer, UserInfo
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from unfold.contrib.inlines.admin import NonrelatedStackedInline
from unfold.components import BaseComponent, register_component
from unfold.sections import TemplateSection
from unfold.decorators import action, display
from django.urls import reverse
from django.db.models import Count
from django.template.loader import render_to_string
from import_export import resources
from import_export.admin import ExportMixin
from unfold.contrib.import_export.forms import ExportForm
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from dashboard.resources import ProductResource, BuyerResource
from django.db import transaction


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "code_prefix", "get_products_link", "parts_count", "get_add_product_button")
    search_fields = ("name", "code_prefix")
    ordering = ("name",)

    def get_products_link(self, obj):
        url = reverse('admin:dashboard_product_changelist') + f'?category__id__exact={obj.id}'
        count = obj.products.count()
        return format_html('<a href="{}">{} Products</a>', url, count)
    get_products_link.short_description = 'Products'

    def parts_count(self, obj):
        parts = get_unique_part_numbers(obj.id)
        url = reverse('admin_part') + f'?category={obj.id}'
        return format_html("""
                           <a class="button text-blue bg-gray-50 hover:bg-gray-300 focus:ring-4 focus:outline-none focus:ring-gray-700 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center" href="{}">
                            {} Part
                           </a>""", url, len(parts))
    parts_count.short_description = "Parts"

    def get_add_product_button(self, obj):
        url = reverse('admin:dashboard_product_add') + f'?category={obj.id}'
        return format_html("""
                           <a class="button" href="{}">
                           <button type="button" class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
                            Add Product
                            <svg class="rtl:rotate-180 w-3.5 h-3.5 ms-2" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 10">
                            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M1 5h12m0 0L9 1m4 4L9 9"/>
                            </svg>
                            </button>
                           </a>""", url)
    get_add_product_button.short_description = 'Add Product'


class ChartSection(TemplateSection):
    template_name = "dashboard/buyer_section.html"

# @admin.register(Buyer)
# class BuyerAdmin(ModelAdmin):
#     list_display = ("full_name", "email", "phone","products_count")
#     list_section = [ChartSection]
#     list_sections_classes = "lg:grid-cols-2"
#     list_sections_per_page = 10
#     search_fields = ["full_name", "email_name", "phone"]
#     warn_unsaved_form = True
#     compressed_fields = True
#     list_filter = ("full_name",)
#     list_before_template = "dashboard/buyer_list_before.html"
    
#     fieldsets = (
#         ("Contact Information", {
#             "fields": ("full_name", "email", "phone", "address")
#         }),
#         ("Additional Information", {
#             "fields": ("note",)
#         }),
#     )

#     def product_count(self, obj):
#         return obj.product_set.count()
#     product_count.short_description = "Products Count"




@admin.register(Buyer)
class BuyerAdmin(ModelAdmin, ExportActionModelAdmin, ImportExportModelAdmin):
    list_display = ["full_name", "email", "phone", "product_count", "last_purchase_date", "last_part_number", "display_parts"]
    search_fields = ["full_name", "email", "phone"]
    list_filter = ["full_name","email","phone"]
    list_before_template = "dashboard/buyer_list_before.html"
    export_template_name = 'export.html'
    resource_classes = [ProductResource]
    export_format = ["csv", "xlsx", "json", "html"]
    export_form_class = ExportForm

    
    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = "product count"
    product_count.admin_order_field = "product_count"

    # @display(description="Parts", dropdown=True)
    # def display_parts(self, instance: Buyer):
    #     parts = instance.product_set.values_list("part_number", flat=True)
    #     items = []
    #     for part in parts:
    #         title = f"part number: {part}"
    #         items.append(title)
        
    #     return {
    #         "title": f"{len(parts)} parts",
    #         "items": items,
    #         "striped": True,
    #     }
    # display_parts.short_description = "Parts"
    # @display(description="Parts", dropdown=True)
    # def display_parts(self, instance: Buyer):
    #     unique_parts = instance.product_set.values('part_number').annotate(
    #         count=Count('part_number')
    #     ).order_by('part_number')
        
    #     items = []
    #     for part in unique_parts:
    #         url = reverse('admin:dashboard_product_changelist') + f"?buyer__id__exact={instance.id}&part_number__exact={part['part_number']}"
    #         items.append({
    #             "label": format_html("Part {} ({})", part['part_number'], part['count']),
    #             "link": url,
    #             "icon": "box",
    #         })
        
    #     return {
    #         "title": f"{len(unique_parts)} Unique Parts",
    #         "items": items,
    #         "footer": f"Total products: {instance.product_set.count()}"
    #     }

    @display(description="Parts", dropdown=True)
    def display_parts(self, instance: Buyer):
        unique_parts = instance.product_set.values('part_number').annotate(
            count=Count('part_number')
        ).order_by('part_number')
        
        items = []
        for part in unique_parts:
            title = f"Part {part['part_number']}"
            if part['count'] > 1:
                title += f" (count: {part['count']})"
            items.append(title)
        
        return {
            "title": f"{len(unique_parts)} Unique Parts",
            "items": items,
            "striped": True,
        }
    display_parts.short_description = "Parts"

    def last_part_number(self, obj):
        last_product = obj.product_set.order_by("-prod_date").first()
        return last_product.part_number if last_product else "no purchase"
    last_part_number.short_description = "last part number"


    def last_purchase_date(self, obj):
        last_product = obj.product_set.order_by("-prod_date").first()
        return last_product.prod_date if last_product else "no purchase"
    last_purchase_date.short_description = "last purchase date"



@admin.register(Product)
class ProductAdmin(ModelAdmin, ExportActionModelAdmin, ImportExportModelAdmin):
    change_form_after_template = "dashboard/product_extra_info.html"
    list_display = ('category', 'product_code_link', 'part_number', 'description', 'prod_date', 'exp_date', 'quantity', 'is_checked', 'buyer', 'modification_date')
    search_fields = ('product_code', 'description', 'lot_number', 'buyer__full_name')
    list_filter = ('part_number', 'category', 'prod_date', 'exp_date', 'buyer')
    readonly_fields = ('product_code',)
    ordering = ['-prod_date']
    autocomplete_fields = ["buyer"]
    resource_classes = [ProductResource]
    export_format = ["csv", "xlsx", "json", "html"]
    export_form_class = ExportForm
    save_as = True
    # change_list_template = "admin/product_change_list.html"


    def product_code_link(self, obj):
        print(obj)
        result = get_product_check_record(obj.product_code)
        if result['is_checked'] == True:
            url = reverse('admin_map') + f'?product_code={obj.product_code}'
            return format_html('<a class="text-blue-600 hover:underline" href="{}">{}</a>', url, obj.product_code)
        return obj.product_code
    product_code_link.short_description = 'Product Code'


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        category_id = request.GET.get('category')
        if category_id and not obj:  # Only for new objects
            form.base_fields['category'].initial = category_id
        return form

    def save_model(self, request, obj, form, change):
        if not change and obj.quantity > 1:
            try:
                with transaction.atomic():
                    created = Product.create_multiple_products(
                        category=obj.category,
                            description=obj.description,
                            prod_date=obj.prod_date,
                            exp_date=obj.exp_date,
                            lot_number=obj.lot_number,
                            treatment=obj.treatment,
                            germination=obj.germination,
                            purity=obj.purity,
                            part_number=obj.part_number,
                            modification_date=obj.modification_date,
                            quantity=obj.quantity,
                            buyer=obj.buyer,
                            note=obj.note
                    )
                    messages.success(request, f"Created {len(created)} products with unique product codes.")
                return
            except Exception as e:
                messages.error(request, f"خطا: {str(e)}")
                raise
    
    

    fieldsets = (
        ("Category Information", {
            "fields": ("category",)
        }),
        ("Product Information", {
            "fields": ("description", "prod_date", "exp_date", "lot_number", "treatment", "germination", "purity"),
            "classes": ("column",)
        }),
        ("Part Information", {
            "fields": ("part_number", "modification_date", "quantity", "buyer", "note"),
            "classes": ("column",)
        }),
        ("System Information", {
            "fields": ("product_code",),
            "classes": ("collapse",)
        }),
    )


@admin.register(ProductCodeCheck)
class ProductCodeCheckAdmin(ModelAdmin):
    list_display = ("product", "checked_at", "get_user_info_link")
    search_fields = ("product__product_code", "user_info__ip_address")
    list_filter = ("checked_at", "product__category", "user_info__country")
    readonly_fields = ("product", "checked_at", "user_info")
    ordering = ["-checked_at"]

    def get_user_info_link(self, obj):
        if obj.user_info:
            url = reverse('admin:dashboard_userinfo_change', args=[obj.user_info.id])
            return format_html('<a href="{}">{}</a>', url, obj.user_info)
        return "-"
    get_user_info_link.short_description = 'User Info'
    get_user_info_link.admin_order_field = 'user_info'


@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('country', 'city', 'phone_number', 'device_type', 'ip_address',)
    list_filter = ('country',)
    search_fields = ('ip_address', 'phone_number', 'country', 'city', 'browser', 'os')
    readonly_fields = ('ip_address', 'location', 'device_type', 'is_bot', 'browser', 'browser_version', 'os', 'os_version', 
                      'device_family', 'country_short', 'country', 'region', 'city', 
                      'latitude', 'longitude',)
    fieldsets = (
        ('Main Information', {
            'fields': ('ip_address', 'phone_number',)
        }),
        ('Device Information', {
            'fields': ('device_type', 'is_bot')
        }),
        ('Browser Information', {
            'fields': ('browser', 'browser_version', 'os', 'os_version', 'device_family')
        }),
        ('Location Information', {
            'fields': ('location', 'country_short', 'country', 'region', 'city', 'latitude', 'longitude')
        })
    )


class StatsAdmin(admin.ModelAdmin):
    change_list_template = "dashboard/analysis.html"

    def changelist_view(self, request, extra_context=None):
        # Get device statistics
        device_stats = UserInfo.objects.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # Get country statistics
        users_by_country = UserInfo.objects.values('country').annotate(count=Count('id'))
        countries = [entry['country'] for entry in users_by_country]
        counts = [entry['count'] for entry in users_by_country]

        extra_context = {
            'device_stats': device_stats,
            'countries': countries,
            'counts': counts,
        }
        return super().changelist_view(request, extra_context=extra_context)

@register_component
class BuyerMostVerificationsComponent(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        top_buyer = Buyer.objects.annotate(
                    total_checks=Count('product__code_checks') 
                ).order_by('-total_checks').first()

        context["children"] = render_to_string(
            "dashboard/helpers/buyer_list.html",
            {
                "buyer": top_buyer,
                "count": top_buyer.total_checks,
                "name": top_buyer.full_name,
            },
        )
        return context



@register_component
class BuyerNoneVerificationsComponent(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        buyer = Buyer.objects.annotate(
                    total_checks=Count('product__code_checks') 
                ).order_by('-total_checks').last()
        
        context["children"] = render_to_string(
            "dashboard/helpers/buyer_list.html",
            {
                "buyer": buyer,
                "count": buyer.total_checks,
                "name": buyer.full_name,
            },
        )
        return context
    
@register_component
class BuyerMostProductsComponent(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        buyer = buyers_by_product_count = Buyer.objects.annotate(
            num_products=Count('product')
        ).order_by('-num_products').first()
        
        context["children"] = render_to_string(
            "dashboard/helpers/buyer_list.html",
            {
                "buyer": buyer,
                "count": buyer.num_products,
                "name": buyer.full_name,
            },
        )
        return context
    

@register_component
class BuyerLeastProductsComponent(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        buyer = buyers_by_product_count = Buyer.objects.annotate(
            num_products=Count('product')
        ).order_by('-num_products').last()
        
        context["children"] = render_to_string(
            "dashboard/helpers/buyer_list.html",
            {
                "buyer": buyer,
                "count": buyer.num_products,
                "name": buyer.full_name,
            },
        )
        return context
    

@register_component
class DriverSectionChangeComponent(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        WEEKDAYS = [
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
            "Sun",
        ]
        OF_DAYS = 21

        context["data"] = json.dumps(
            {
                "labels": [WEEKDAYS[day % 7] for day in range(1, OF_DAYS)],
                "datasets": [
                    {
                        "data": [
                            [1, random.randrange(8, OF_DAYS)] for i in range(1, OF_DAYS)
                        ],
                        "backgroundColor": "var(--color-primary-600)",
                    }
                ],
            }
        )
        return context