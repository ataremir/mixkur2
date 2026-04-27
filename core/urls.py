from django.urls import path
from django.shortcuts import render

# anatoliabox.store (Root) için Landing Page
def landing_page(request):
    return render(request, 'index.html')

from pool.views_ui import ShopDashboardView, CourierDashboardView

urlpatterns = [
    path('', landing_page, name='landing'),
    path('shop/dashboard/', ShopDashboardView.as_view(), name='shop_dashboard'),
    path('courier/dashboard/', CourierDashboardView.as_view(), name='courier_dashboard'),
]
