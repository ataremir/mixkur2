from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

class AdminAccessMiddleware:
    """
    Subdomain bazlı admin koruması.
    Eğer istek 'admin.anatoliabox.store' üzerinden geliyorsa ve 
    kullanıcının ADMIN rolü veya is_staff yetkisi yoksa, girmesini engeller.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        
        # admin. ile başlıyor mu kontrolü (port içerebilir localhost testi için)
        if host.startswith('admin.'):
            if request.user.is_authenticated:
                user_role = getattr(request.user, 'role', None)
                if not (request.user.is_staff or user_role == 'ADMIN'):
                    # Admin olmayan yetkisiz bir hesap admin subdomainine ulaşmaya çalışıyor
                    # Kendi ana ekranlarına atalım
                    if user_role == 'SHOP':
                        return redirect('http://anatoliabox.store/shop/dashboard/') # Kendi paneli
                    elif user_role == 'COURIER':
                        return redirect('http://anatoliabox.store/courier/dashboard/')
                    else:
                        raise PermissionDenied("Admin sayfasına erişim yetkiniz yok.")
        
        response = self.get_response(request)
        return response
