from django.urls import path
from analytics_app.views import ip_dashboard

urlpatterns = [
    path('', ip_dashboard, name='ip_dashboard'),
]
