# Celery uygulamasını Django başlatıldığında otomatik yükle.
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery henüz kurulu değilse hata verme, sistemin geri kalanı çalışsın
    pass
