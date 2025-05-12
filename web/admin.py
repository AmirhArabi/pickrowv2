# from django.contrib import admin
# from .models import Categorie, Product, GroupModel
# from django.contrib.admin.helpers import ActionForm
# from django import forms
# import csv
# from django.shortcuts import HttpResponse
    

# class ProductAdmin(admin.ModelAdmin):
#     actions = ['export_as_csv']
#     list_display = ('pcode', 'pseen', 'category')

#     def export_as_csv(self, request, queryset):
#         meta = self.model._meta
#         field_names = list(self.list_display)

#         response = HttpResponse(content_type="text/csv")
#         response["Content-Disposition"] = "attachment; filename={}.csv".format(meta)
#         writer = csv.writer(response)

#         writer.writerow(field_names)

#         for obj in queryset:
#             result = []
#             for field in field_names:
#                 attr = getattr(obj, field, 0)
#                 if attr and callable(attr):
#                     result.append(attr())
#                 elif attr:
#                     result.append(attr)
#                 else:
#                     attr = getattr(self, field, 0)
#                     if attr:
#                         result.append(attr(obj))
#                     else:
#                         result.append(attr)
#             row = writer.writerow(result)

#         return response

#     export_as_csv.short_description = "Export Selected Product to CSV file"



# class Form(ActionForm):
#     Count = forms.IntegerField()
#     group = forms.ModelChoiceField(queryset=GroupModel.objects.all(), required=False)

# class CategorieAdmin(admin.ModelAdmin):
#     actions = ["create_bulk_products"]
#     action_form = Form
#     list_display = ('name', 'lot_number', 'prod_date', 'description')


#     @admin.action(description='Create Products for this categorie')
#     def create_bulk_products(self, requests, queryset):
#         Count = int(requests.POST['Count'])
#         group = requests.POST['group']
#         category = queryset[0]
#         for i in range(Count):
#             p = Product(category=category, pseen=0, group_id=group)
#             # p = Product(category=category, pseen=0, group=group)
#             p.save()

# class GroupModelAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description', )
#     # create a action for export products of selected group to csv file
#     actions = ['export_products_to_csv']

#     def export_products_to_csv(self, request, queryset):
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="products_in_group.csv"'

#         writer = csv.writer(response)
#         writer.writerow(['Pcode', 'Category', 'Pseen', 'Group'])

#         for group in queryset:
#             products = Product.objects.filter(group=group)
#             for product in products:
#                 writer.writerow([product.pcode, product.category.name, product.pseen, group.name])

#         return response

#     export_products_to_csv.short_description = "Export products to CSV"

# # Unregister all models from admin
# admin.site.unregister(GroupModel)
# admin.site.unregister(Categorie)
# admin.site.unregister(Product)
