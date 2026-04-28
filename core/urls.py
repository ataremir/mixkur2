from django.urls import path
from django.shortcuts import render

# anatoliabox.store (Root) için Landing Page
from core.views import LandingPageView
from pool.views_ui import ShopDashboardView, CourierDashboardView

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing'),
    path('shop/dashboard/', ShopDashboardView.as_view(), name='shop_dashboard'),
    path('courier/dashboard/', CourierDashboardView.as_view(), name='courier_dashboard'),
]
