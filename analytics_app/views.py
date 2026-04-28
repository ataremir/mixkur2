from django.shortcuts import render
from .models import VisitorIP
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required # Sadece admin/staff üyeleri görebilsin
def ip_dashboard(request):
    logs = VisitorIP.objects.all()[:100] # Son 100 kayıt
    return render(request, 'analytics/dashboard.html', {'logs': logs})
