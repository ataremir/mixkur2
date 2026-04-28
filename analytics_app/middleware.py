from .models import VisitorIP

class IPLoggerMiddleware:
    """
    Tüm isteklere giren ziyaretçileri veritabanına kaydeder.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. IP Adresini Al (Proxy arkasındaysa gerçek IP'yi al)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # 2. Kaydı Veritabanına Yaz
        # 'ip.anatoliabox.store' sayfasının kendisini sürekli loglamaması için basit bir filtre
        if not request.get_host().startswith('ip.'):
            try:
                VisitorIP.objects.create(
                    ip_address=ip,
                    host=request.get_host(),
                    path=request.path,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception:
                pass # Hata durumunda site akışını bozma

        response = self.get_response(request)
        return response
