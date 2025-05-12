# create url for hello world view

# Path: web\urls.py
from django.urls import path
from . import views

urlpatterns = [
    #create a route for seach page that take pcode as parameter
    # path('<str:pcode>', views.search, name='search'),
    path('', views.index, name='index')
    ]