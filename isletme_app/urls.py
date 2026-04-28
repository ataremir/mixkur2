from django.urls import path
from . import views

# isletme.anatoliabox.store subdomain'i için URL yapılandırması
urlpatterns = [
    path('', views.isletme_dashboard, name='isletme_home'),
    path('giris/', views.isletme_giris, name='isletme_giris'),
    path('kayit/', views.isletme_kayit, name='isletme_kayit'),
    path('cikis/', views.isletme_cikis, name='isletme_cikis'),
    path('dashboard/', views.isletme_dashboard, name='isletme_dashboard'),
    path('profil/', views.isletme_profil_duzenle, name='isletme_profil'),
]
