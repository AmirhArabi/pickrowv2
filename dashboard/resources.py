from import_export import resources

from dashboard.models import Product, Buyer


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product


class BuyerResource(resources.ModelResource):
    class Meta:
        model = Buyer
