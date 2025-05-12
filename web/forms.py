from django import forms

class SearchForm(forms.Form):
    pcode = forms.CharField(max_length=64, label='Product Code', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your code here...'}))