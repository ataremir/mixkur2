"""
AnatoliaBox - Celery Konfigürasyonu
═══════════════════════════════════

Redis backend ile asenkron görev yönetimi.

Celery, bu projede şu görevleri asenkron olarak çalıştırır:
- Yeni sipariş batch kontrolü (process_new_order)
- Kuryeye batch teklifi gönderme (offer_batch_to_courier)
- 30 saniyelik batch timeout (batch_offer_timeout)
- Sipariş gruba yayınlama (broadcast_order_to_group)

Başlatma:
    celery -A core worker -l info
"""

import os
from celery import Celery

# Django settings modülünü ayarla
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Celery uygulamasını oluştur
app = Celery('anatoliabox')

# Django settings'den CELERY_ prefix'li ayarları otomatik oku
# Örn: settings.CELERY_BROKER_URL → broker_url olarak okunur
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tüm INSTALLED_APPS içindeki tasks.py dosyalarını otomatik keşfet
# Bu sayede pool/tasks.py otomatik olarak bulunur ve yüklenir
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Test amaçlı debug görevi."""
    print(f'İstek: {self.request!r}')
