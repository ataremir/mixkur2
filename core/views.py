from django.shortcuts import render

def home(request):
    """
    Ana domain (anatoliabox.store) için Coming Soon sayfası.
    """
    return render(request, 'index.html')
