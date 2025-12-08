import logging
import sqlite3
from telegram import (KeyboardButton, ReplyKeyboardMarkup,
                      BotCommand)
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, ConversationHandler)

import random
import datetime

logging.basicConfig(level=logging.INFO)

# =============================
#  DATABASE
# =============================

conn = sqlite3.connect("auth.db", check_same_thread=False)
c = conn.cursor()

# Userlarni saqlash
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    phone_number TEXT,
    device_id TEXT,
    last_code TEXT,
    expires_at TEXT
);
""")

conn.commit()

# =============================
#  CONVERSATION STATES
# =============================

PHONE, VERIFY = range(2)


# =============================
#  HELPERS
# =============================

def generate_code():
    return str(random.randint(1000, 9999))

def create_device_id(tg_id):
    return f"dev-{tg_id}-{random.randint(1111,9999)}"


# =============================
#  COMMANDS
# =============================

def start(update, context):
    user = update.message.from_user

    reply_markup = ReplyKeyboardMarkup([
        [KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]
    ], resize_keyboard=True)

    update.message.reply_text(
        f"Assalomu alaykum {user.first_name}!\n\n"
        f"📲 Dasturga kirish uchun telefon raqamingizni yuboring.",
        reply_markup=reply_markup
    )

    return PHONE


def phone_handler(update, context):
    contact = update.message.contact
    phone = contact.phone_number
    tg_id = update.message.from_user.id

    code = generate_code()

    expires_at = (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()

    device_id = create_device_id(tg_id)

    c.execute("""
        INSERT OR REPLACE INTO users (telegram_id, phone_number, device_id, last_code, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (tg_id, phone, device_id, code, expires_at))
    conn.commit()

    update.message.reply_text(
        f"📨 Sizga tasdiqlash kodi yuborildi!\n"
        f"👇 Kod: *{code}*\n\n"
        f"Uni web-dasturga kiritasiz.",
        parse_mode="Markdown"
    )

    return VERIFY


def verify_handler(update, context):
    user_input = update.message.text
    tg_id = update.message.from_user.id

    c.execute("SELECT last_code, expires_at, device_id, phone_number FROM users WHERE telegram_id = ?", (tg_id,))
    result = c.fetchone()

    if not result:
        update.message.reply_text("❌ Siz hali ro‘yxatdan o‘tmagansiz. /start bosing.")
        return ConversationHandler.END

    saved_code, expires_at, device_id, phone_number = result

    if datetime.datetime.now() > datetime.datetime.fromisoformat(expires_at):
        update.message.reply_text("⌛ Kod muddati tugagan! /start dan qayta boshlang.")
        return ConversationHandler.END

    if user_input != saved_code:
        update.message.reply_text("❌ Kod noto‘g‘ri! Qayta kiriting.")
        return VERIFY

    update.message.reply_text(
        f"✅ Kod tasdiqlandi!\n\n"
        f"📱 Sizning DEVICE_ID:\n\n`{device_id}`\n\n"
        f"Bu ID web dasturga yuboriladi va faqat shu qurilmadan kirish mumkin bo‘ladi.",
        parse_mode="Markdown"
    )

    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END


# =============================
# MAIN
# =============================

def main():
    updater = Updater("8054478723:AAGchsdcv2VKqLkNuPHVfAAp09CZywN_Ij4", use_context=True)
    dp = updater.dispatcher

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(Filters.contact, phone_handler)],
            VERIFY: [MessageHandler(Filters.text & ~Filters.command, verify_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    dp.add_handler(conv)

    dp.bot.set_my_commands([
        BotCommand("start", "Avtorizatsiya jarayonini boshlash"),
        BotCommand("cancel", "Bekor qilish"),
    ])

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
