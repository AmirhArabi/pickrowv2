from django.db import models
import random


def generate_unique_pcode():
    return random.randrange(100000000, 1000000000)


class Categorie(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    description = models.CharField(max_length=120, null=False, blank=False)
    packing = models.IntegerField(null=False, blank=False)
    prod_date = models.DateField(null=False, blank=False)
    germanition = models.IntegerField(null=False, blank=False)
    expire_date = models.DateField(null=False, blank=False)
    lot_number = models.IntegerField(null=False, blank=False)
    purity = models.IntegerField(null=False, blank=False)
    treatment = models.CharField(max_length=240, null=True, blank=True)

    def __str__(self):
        return self.name




class Product(models.Model):
    pcode = models.CharField(max_length=64, blank=True)
    category = models.ForeignKey(Categorie, on_delete=models.CASCADE, blank=False)
    pseen = models.IntegerField()
    group = models.ForeignKey('GroupModel', on_delete=models.CASCADE, null=True, blank=True)


    def save(self, *args, **kwargs):
        if not self.pcode:
            unique_pcode = generate_unique_pcode()
            while Product.objects.filter(pcode=unique_pcode).exists():
                unique_pcode = generate_unique_pcode()
            self.pcode = unique_pcode
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.pcode

class GroupModel(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    description = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return self.name