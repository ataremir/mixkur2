from django.urls import path
from django.shortcuts import render

# anatoliabox.store (Root) için Landing Page
def landing_page(request):
    return render(request, 'index.html')

urlpatterns = [
    path('', landing_page, name='landing'),
]
