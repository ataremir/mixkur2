from django.urls import path
from . import views

urlpatterns = [
    path('takip/<int:siparis_id>/', views.harita_view, name='harita_takip'),
    path('api/konum-guncelle/', views.kurye_konum_guncelle, name='api_konum_guncelle'),
]
