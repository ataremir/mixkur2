"""
AnatoliaBox Telegram Botunu başlatmak için Django Management Komutu.

Kullanım:
    python manage.py run_bot

Bu komut, Telegram Bot API'ye long polling ile bağlanır
ve gelen mesajları/callback'leri işler. Ctrl+C ile durur.

Not:
    - Bot başlamadan önce TELEGRAM_BOT_TOKEN ayarlanmış olmalıdır.
    - Redis ve Celery worker'ın çalışır durumda olması gerekir
      (batch ve broadcast görevleri için).
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram.ext import ApplicationBuilder

from telegram_bot.handlers import register_handlers

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'AnatoliaBox Telegram Botunu başlatır (long polling modu)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Detaylı log çıktısı gösterir.',
        )

    def handle(self, *args, **options):
        # ── Bot token kontrolü ──
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)

        if not bot_token:
            self.stderr.write(self.style.ERROR(
                "\n❌ TELEGRAM_BOT_TOKEN ayarlanmamış!\n"
                "   .env dosyasına şu satırı ekleyin:\n"
                "   TELEGRAM_BOT_TOKEN=your_bot_token_here\n"
            ))
            return

        # ── Grup ID kontrolü ──
        group_id = getattr(settings, 'TELEGRAM_COURIER_GROUP_ID', None)
        if not group_id:
            self.stderr.write(self.style.WARNING(
                "\n⚠️  TELEGRAM_COURIER_GROUP_ID ayarlanmamış!\n"
                "   Sipariş yayınlama özelliği çalışmayacak.\n"
                "   .env dosyasına ekleyin:\n"
                "   TELEGRAM_COURIER_GROUP_ID=-100XXXXXXXXXX\n"
            ))

        # ── Loglama ayarı ──
        if options['verbose']:
            logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=logging.DEBUG
            )
        else:
            logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=logging.INFO
            )

        self.stdout.write(self.style.SUCCESS(
            "\n"
            "╔══════════════════════════════════════════╗\n"
            "║  🤖 AnatoliaBox Telegram Botu            ║\n"
            "║  Versiyon: 1.0                           ║\n"
            "║  Mod: Long Polling                       ║\n"
            "╚══════════════════════════════════════════╝\n"
        ))

        # ── Bot uygulamasını oluştur ──
        application = ApplicationBuilder().token(bot_token).build()

        # ── Handler'ları kaydet ──
        register_handlers(application)

        self.stdout.write(self.style.SUCCESS(
            "✅ Handler'lar yüklendi:\n"
            "   • /siparis  → Esnaf sipariş girişi\n"
            "   • İşi Al   → Kurye iş alma (atomik)\n"
            "   • Batch    → Sipariş birleştirme\n"
            "\n"
            "📡 Polling başlıyor... (Ctrl+C ile durdurun)\n"
        ))

        # ── Botu başlat ──
        application.run_polling(
            drop_pending_updates=True,  # Eski bekleyen mesajları atla
        )
