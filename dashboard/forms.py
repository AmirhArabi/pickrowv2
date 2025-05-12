from django import forms
from django.utils import timezone

class SearchForm(forms.Form):
    pcode = forms.CharField(max_length=64, label='Product Code', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your code here...'}))
    phone_number = forms.CharField(max_length=15, label='Phone Number', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number here...'}))



class MapFilterForm(forms.Form):
    date_from = forms.DateField(
        label="From Date",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}))
    
    date_to = forms.DateField(
        label="To Date",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}))
    
    product_code = forms.CharField(
        label="Product Code",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Filter by product code'}))