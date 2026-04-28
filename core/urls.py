from django.urls import path
from core.views import home
from pool.views_ui import ShopDashboardView, CourierDashboardView

# anatoliabox.store (Root) için URL yapılandırması
urlpatterns = [
    path('', home, name='home'),
    path('shop/dashboard/', ShopDashboardView.as_view(), name='shop_dashboard'),
    path('courier/dashboard/', CourierDashboardView.as_view(), name='courier_dashboard'),
]
