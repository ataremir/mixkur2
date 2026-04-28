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
                    if user_role == 'SHOP':
                        return redirect('http://anatoliabox.store/shop/dashboard/')
                    elif user_role == 'COURIER':
                        return redirect('http://anatoliabox.store/courier/dashboard/')
                    elif user_role == 'ISLETME':
                        return redirect('http://isletme.anatoliabox.store/')
                    else:
                        raise PermissionDenied("Admin sayfasına erişim yetkiniz yok.")

        response = self.get_response(request)
        return response


class IsletmeAccessMiddleware:
    """
    isletme.anatoliabox.store subdomain koruması.
    - ISLETME ve ADMIN rolleri erişebilir.
    - COURIER rolü KESİNLİKLE giremesin, ana sayfaya yönlendirilsin.
    - SHOP rolü de kendi paneline yönlendirilsin.
    - Giriş yapmamış kullanıcılar login sayfasına yönlendirilir.
    """
    # Login ve kayıt sayfaları middleware'den muaf tutulacak yollar
    EXEMPT_PATHS = ['/giris/', '/kayit/', '/cikis/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()

        if host.startswith('isletme.'):
            # Login/Kayıt sayfalarına herkes erişebilsin (döngüsel yönlendirme önlenir)
            if request.path in self.EXEMPT_PATHS:
                return self.get_response(request)

            # Giriş yapmamış kullanıcıları login'e yönlendir
            if not request.user.is_authenticated:
                return redirect('/giris/?next=' + request.path)

            user_role = getattr(request.user, 'role', None)

            # ADMIN her zaman geçer
            if user_role == 'ADMIN' or request.user.is_staff:
                return self.get_response(request)

            # ISLETME rolü geçer
            if user_role == 'ISLETME':
                return self.get_response(request)

            # COURIER rolü KESİNLİKLE giremez — ana sayfaya at
            if user_role == 'COURIER':
                return redirect('http://anatoliabox.store/')

            # SHOP rolü kendi paneline yönlendirilir
            if user_role == 'SHOP':
                return redirect('http://anatoliabox.store/shop/dashboard/')

            # Bilinmeyen rol — ana sayfaya yönlendir
            return redirect('http://anatoliabox.store/')

        response = self.get_response(request)
        return response


class APIAccessMiddleware:
    """
    api.anatoliabox.store subdomain koruması.
    Sadece ADMIN ve is_staff erişebilir.
    Aksi takdirde ana alan adına (anatoliabox.store) yönlendirilir.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()

        if host.startswith('api.'):
            if not request.user.is_authenticated or not (request.user.is_staff or getattr(request.user, 'role', '') == 'ADMIN'):
                return redirect('http://anatoliabox.store/')

        return self.get_response(request)
