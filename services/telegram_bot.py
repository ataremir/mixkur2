import os
import django
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from asgiref.sync import sync_to_async

# Django setup (must be before importing models if run standalone)
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
# django.setup()

# Import models inside functions or after setup
def get_models():
    from demo_app.models import Siparis, KuryeProfil
    return Siparis, KuryeProfil

async def start_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment.")
        return

    application = Application.builder().token(token).build()

    # Handlers
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Telegram Bot started...")
    await application.initialize()
    await application.start()
    await application.run_polling()

async def send_new_order_notification(siparis_id):
    """
    Django views içinden veya signals üzerinden çağrılabilir.
    """
    Siparis, KuryeProfil = get_models()
    siparis = await sync_to_async(Siparis.objects.select_related('kurye__user').get)(id=siparis_id)
    
    if not siparis.kurye or not siparis.kurye.telegram_chat_id:
        return

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    bot = Application.builder().token(token).build().bot

    text = (
        f"📦 *Yeni Sipariş Atandı!*\n\n"
        f"Sipariş ID: #{siparis.id}\n"
        f"Durum: {siparis.durum}\n\n"
        f"📍 [Müşteri Konumu]({siparis_google_link(siparis)})"
    )

    keyboard = [
        [InlineKeyboardButton("Siparişi Aldım", callback_data=f"aldim_{siparis.id}")],
        [InlineKeyboardButton("Teslim Ettim", callback_data=f"teslim_{siparis.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await bot.send_message(
        chat_id=siparis.kurye.telegram_chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def siparis_google_link(siparis):
    return f"https://www.google.com/maps/dir/?api=1&destination={siparis.musteri_enlem},{siparis.musteri_boylam}"

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    Siparis, KuryeProfil = get_models()

    if data.startswith("aldim_"):
        siparis_id = int(data.split("_")[1])
        siparis = await sync_to_async(Siparis.objects.get)(id=siparis_id)
        siparis.durum = 'Yolda'
        await sync_to_async(siparis.save)()
        await query.edit_message_text(text=f"✅ Sipariş #{siparis_id} alındı. Yoldasınız!")

    elif data.startswith("teslim_"):
        siparis_id = int(data.split("_")[1])
        siparis = await sync_to_async(Siparis.objects.get)(id=siparis_id)
        siparis.durum = 'Teslim Edildi'
        await sync_to_async(siparis.save)()
        await query.edit_message_text(text=f"🏁 Sipariş #{siparis_id} başarıyla teslim edildi. Tebrikler!")

# Standalone execution
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    asyncio.run(start_bot())
