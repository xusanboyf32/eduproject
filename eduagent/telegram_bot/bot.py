# telegram_bot/bot.py
import os
import logging
import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Sozlamalar
# BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_TOKEN = '8054478723:AAGchsdcv2VKqLkNuPHVfAAp09CZywN_Ij4'
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Vazifa: User /start bosganda unga telefon raqam so'rash
    Natija: User telefon raqamini yuboradi
    """
    # Telefon raqam so'rash uchun keyboard
    phone_button = KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True)

    await update.message.reply_text(
        "👋 *Saytga kirish uchun telefon raqamingizni yuboring!*\n\n"
        "Quyidagi tugmani bosing yoki telefon raqamingizni yozing:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Vazifa: User telefon raqam yuborganda backendga yuborish
    Natija: Kod olinadi va userga yuboriladi
    """
    # User ma'lumotlari (bot avtomatik oladi)
    user = update.effective_user
    telegram_id = user.id  # ❌ User BILMAYDI bu raqamni!
    telegram_username = user.username

    # Telefon raqamni olish
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text.strip()

    # Telefon raqamni tozalash
    phone_number = phone_number.replace(" ", "").replace("-", "")
    if phone_number.startswith("998"):
        phone_number = "+" + phone_number
    elif not phone_number.startswith("+"):
        phone_number = "+998" + phone_number[-9:]

    logger.info(f"Telefon tasdiqlash: {phone_number} -> {telegram_id}")

    try:
        # Backendga so'rov yuborish
        response = requests.post(
            f"{BACKEND_URL}/api/auth/telegram-login/",
            json={
                'phone_number': phone_number,
                'telegram_id': telegram_id,
                'telegram_username': telegram_username
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            code = data.get('code')

            # Userga kodni yuborish
            await update.message.reply_text(
                f"✅ *Telefon raqamingiz tasdiqlandi!*\n\n"
                f"🔐 *Kirish kodi:* `{code}`\n\n"
                f"⚠️ *Diqqat:*\n"
                f"• Bu kodni brauzerga kiriting\n"
                f"• Kod faqat *1 daqiqa* davomida amal qiladi\n"
                f"• Hech kimga kodingizni bermang!",
                parse_mode='Markdown',
                reply_markup=None  # Keyboardni olib tashlash
            )

        else:
            error = response.json().get('error', 'Xatolik yuz berdi')
            await update.message.reply_text(f"❌ {error}")

    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik")


def main():
    """Botni ishga tushirish"""
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_phone))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone))

    print("🤖 Telegram bot ishga tushdi...")
    # app.run_polling(allowed_updates=Update.ALL_UPDATES)
    app.run_polling()



if __name__ == '__main__':
    main()


