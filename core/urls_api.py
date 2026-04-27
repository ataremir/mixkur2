from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# api.anatoliabox.store için izole edilmiş API rotaları
urlpatterns = [
    # JWT Kimlik Doğrulama
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Havuz API Rotaları (prefix olmadan doğrudan api. subdomaininde)
    path('', include('pool.urls')),
]
