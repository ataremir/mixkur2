from django.views.generic import TemplateView
from .mixins import RoleRequiredMixin

class ShopDashboardView(RoleRequiredMixin, TemplateView):
    template_name = 'shop/dashboard.html'
    allowed_roles = ['SHOP', 'ADMIN']

class CourierDashboardView(RoleRequiredMixin, TemplateView):
    template_name = 'courier/dashboard.html'
    allowed_roles = ['COURIER', 'ADMIN']
