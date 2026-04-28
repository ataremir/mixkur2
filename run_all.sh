#!/bin/bash

# AnatoliaBox - Tüm Servisleri Başlatma Betiği
# -------------------------------------------

echo "🚀 AnatoliaBox servisleri başlatılıyor..."

# 1. Sanal ortamı kontrol et
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Sanal ortam aktif."
else
    echo "❌ venv bulunamadı! Lütfen sanal ortamı kurun."
    exit 1
fi

# 2. Veritabanı Migrationları
echo "🔄 Veritabanı güncelleniyor..."
python manage.py migrate

# 3. Celery Worker (Arka Plan Görevleri ve Batch Algoritması)
echo "📦 Celery Worker başlatılıyor..."
# -D parametresi arka planda (daemon) çalıştırır. Loglar celery.log'a yazılır.
celery -A core worker -l info --detach --logfile=logs/celery.log

# 4. Telegram Bot
echo "🤖 Telegram Bot başlatılıyor..."
# Arka planda çalıştır ve çıktıyı bot.log'a yönlendir
nohup python manage.py run_bot > logs/bot.log 2>&1 &
echo $! > logs/bot.pid

# 5. Django Web Sunucusu (API ve Admin Paneli)
echo "🌐 Django sunucusu başlatılıyor..."
python manage.py runserver 0.0.0.0:8000

# Betik durdurulduğunda (Ctrl+C), arka plan işlemlerini kapatmak için:
trap "kill $(cat logs/bot.pid); celery -A core multi stop worker; exit" INT
