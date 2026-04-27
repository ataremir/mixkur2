from django.contrib import admin
from django.urls import path

# admin.anatoliabox.store için izole edilmiş URL yapısı
urlpatterns = [
    path('', admin.site.urls),
]
