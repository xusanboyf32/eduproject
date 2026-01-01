#!/usr/bin/env python3
"""
Telegram Bot: Ustoz-Talaba Chat Tizimi
Aiogram 3.23.0 versiyasi uchun
Django databasiga ulanadi
"""

import os
import sys
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from urllib.parse import unquote

import psycopg2
from psycopg2.extras import RealDictCursor, DictCursor
from psycopg2 import pool
import redis

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ============================================================================
# 1. KONFIGURATSIYA
# ============================================================================

from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token - .env faylidan o'qiladi
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# PostgreSQL Database Configuration (Django settings.py dan)
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'your_db_name'),
    'user': os.environ.get('DB_USER', 'your_db_user'),
    'password': os.environ.get('DB_PASSWORD', 'your_db_password'),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432')
}

# Admin Configuration
ADMIN_IDS = [int(id.strip()) for id in os.environ.get('ADMIN_IDS', '').split(',') if id.strip()]

# Redis Configuration (FSM storage uchun)
REDIS_CONFIG = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('REDIS_PORT', 6379)),
    'db': int(os.environ.get('REDIS_DB', 0)),
    'decode_responses': True
}

# Logging Configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('aiogram_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# 2. FSM STATES (Holatlar)
# ============================================================================

class Form(StatesGroup):
    """FSM holatlari"""
    selecting_role = State()  # Rol tanlash
    selecting_teacher = State()  # Ustoz tanlash
    writing_message = State()  # Xabar yozish
    viewing_chat = State()  # Chatni ko'rish
    replying_message = State()  # Javob yozish
    admin_assigning = State()  # Admin: bog'lash


# ============================================================================
# 3. DATABASE MANAGER (Django databasiga ulanadi)
# ============================================================================

class DatabaseManager:
    """PostgreSQL database bilan ishlash"""

    _connection_pool = None

    @classmethod
    def initialize(cls):
        """Database connection pool ni yaratish"""
        try:
            if cls._connection_pool is None:
                cls._connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1,  # min connections
                    20,  # max connections
                    **DB_CONFIG
                )
                logger.info("✅ Database connection pool initialized")
                cls._setup_tables()
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            sys.exit(1)

    @classmethod
    def _setup_tables(cls):
        """Kerakli jadvallarni yaratish (agar mavjud bo'lmasa)"""
        queries = [
            # Bot users jadvali
            """
            CREATE TABLE IF NOT EXISTS bot_users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                username VARCHAR(100),
                phone VARCHAR(20),
                role VARCHAR(50) CHECK (role IN ('student', 'teacher', 'head_teacher', 'admin')),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,

            # Student-teacher assignments (bog'lanishlar)
            """
            CREATE TABLE IF NOT EXISTS student_teacher (
                id SERIAL PRIMARY KEY,
                student_id BIGINT NOT NULL REFERENCES bot_users(telegram_id),
                teacher_id BIGINT NOT NULL REFERENCES bot_users(telegram_id),
                subject VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, teacher_id, subject)
            )
            """,

            # Messages jadvali
            """
            CREATE TABLE IF NOT EXISTS bot_messages (
                id SERIAL PRIMARY KEY,
                message_uid VARCHAR(100) UNIQUE NOT NULL,
                sender_id BIGINT NOT NULL REFERENCES bot_users(telegram_id),
                receiver_id BIGINT NOT NULL REFERENCES bot_users(telegram_id),
                message_text TEXT,
                message_type VARCHAR(20) DEFAULT 'text',
                is_read BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                replied_at TIMESTAMP
            )
            """,

            # Indexlar
            """
            CREATE INDEX IF NOT EXISTS idx_messages_sender ON bot_messages(sender_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_messages_receiver ON bot_messages(receiver_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_messages_status ON bot_messages(status)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_messages_created ON bot_messages(created_at DESC)
            """
        ]

        conn = cls.get_connection()
        cursor = conn.cursor()
        try:
            for query in queries:
                cursor.execute(query)
            conn.commit()
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Table creation failed: {e}")
            raise
        finally:
            cursor.close()
            cls.return_connection(conn)

    @classmethod
    def get_connection(cls):
        """Connection pool dan connection olish"""
        if cls._connection_pool is None:
            cls.initialize()
        return cls._connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        """Connection ni pool ga qaytarish"""
        cls._connection_pool.putconn(connection)

    @classmethod
    def execute_query(cls, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
        """Query ni execute qilish"""
        conn = None
        cursor = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(query, params or ())

            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount

            return result

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Query error: {e}\nQuery: {query[:100]}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                cls.return_connection(conn)

    # ========== USER OPERATIONS ==========

    @classmethod
    def get_or_create_user(cls, telegram_id: int, full_name: str, username: str = None) -> Dict:
        """User ni topish yoki yaratish"""
        query = "SELECT * FROM bot_users WHERE telegram_id = %s"
        user = cls.execute_query(query, (telegram_id,), fetch_one=True)

        if user:
            if user['full_name'] != full_name or user['username'] != username:
                query = """
                UPDATE bot_users 
                SET full_name = %s, username = %s, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = %s
                RETURNING *
                """
                user = cls.execute_query(query, (full_name, username, telegram_id), fetch_one=True)
            return user

        query = """
        INSERT INTO bot_users (telegram_id, full_name, username)
        VALUES (%s, %s, %s)
        RETURNING *
        """
        return cls.execute_query(query, (telegram_id, full_name, username), fetch_one=True)

    @classmethod
    def update_user_role(cls, telegram_id: int, role: str) -> Dict:
        """User role ni yangilash"""
        query = """
        UPDATE bot_users 
        SET role = %s, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = %s
        RETURNING *
        """
        return cls.execute_query(query, (role, telegram_id), fetch_one=True)

    @classmethod
    def get_user(cls, telegram_id: int) -> Dict:
        """User ni ID bo'yicha olish"""
        query = "SELECT * FROM bot_users WHERE telegram_id = %s"
        return cls.execute_query(query, (telegram_id,), fetch_one=True)

    @classmethod
    def get_teachers_for_student(cls, student_id: int) -> List[Dict]:
        """Talabaning ustozlarini olish"""
        query = """
        SELECT u.*, st.subject
        FROM bot_users u
        JOIN student_teacher st ON u.telegram_id = st.teacher_id
        WHERE st.student_id = %s AND st.is_active = TRUE
        ORDER BY u.full_name
        """
        return cls.execute_query(query, (student_id,), fetch_all=True)

    @classmethod
    def get_students_for_teacher(cls, teacher_id: int) -> List[Dict]:
        """Ustozning talabalarini olish"""
        query = """
        SELECT u.*, st.subject
        FROM bot_users u
        JOIN student_teacher st ON u.telegram_id = st.student_id
        WHERE st.teacher_id = %s AND st.is_active = TRUE
        ORDER BY u.full_name
        """
        return cls.execute_query(query, (teacher_id,), fetch_all=True)

    @classmethod
    def assign_student_to_teacher(cls, student_id: int, teacher_id: int, subject: str = None) -> Dict:
        """Talabani ustozga bog'lash"""
        query = """
        INSERT INTO student_teacher (student_id, teacher_id, subject)
        VALUES (%s, %s, %s)
        ON CONFLICT (student_id, teacher_id, subject) 
        DO UPDATE SET is_active = TRUE, assigned_at = CURRENT_TIMESTAMP
        RETURNING *
        """
        return cls.execute_query(query, (student_id, teacher_id, subject), fetch_one=True)

    # ========== MESSAGE OPERATIONS ==========

    @classmethod
    def save_message(cls, sender_id: int, receiver_id: int, message_text: str, message_type: str = 'text') -> Dict:
        """Xabarni saqlash"""
        message_uid = f"msg_{sender_id}_{receiver_id}_{datetime.now().timestamp()}"

        query = """
        INSERT INTO bot_messages (message_uid, sender_id, receiver_id, message_text, message_type)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """
        return cls.execute_query(query, (message_uid, sender_id, receiver_id, message_text, message_type),
                                 fetch_one=True)

    @classmethod
    def get_chat_messages(cls, user1_id: int, user2_id: int, limit: int = 50) -> List[Dict]:
        """Ikki user orasidagi xabarlarni olish"""
        query = """
        SELECT m.*, 
               sender.full_name as sender_name,
               receiver.full_name as receiver_name
        FROM bot_messages m
        JOIN bot_users sender ON m.sender_id = sender.telegram_id
        JOIN bot_users receiver ON m.receiver_id = receiver.telegram_id
        WHERE (m.sender_id = %s AND m.receiver_id = %s)
           OR (m.sender_id = %s AND m.receiver_id = %s)
        ORDER BY m.created_at ASC
        LIMIT %s
        """
        return cls.execute_query(query, (user1_id, user2_id, user2_id, user1_id, limit), fetch_all=True)

    @classmethod
    def get_unread_messages_for_teacher(cls, teacher_id: int) -> List[Dict]:
        """Ustozga kelgan o'qilmagan xabarlar"""
        query = """
        SELECT m.*, u.full_name as sender_name
        FROM bot_messages m
        JOIN bot_users u ON m.sender_id = u.telegram_id
        WHERE m.receiver_id = %s 
          AND m.is_read = FALSE
          AND m.status = 'pending'
        ORDER BY m.created_at DESC
        """
        return cls.execute_query(query, (teacher_id,), fetch_all=True)

    @classmethod
    def mark_message_as_read(cls, message_id: int) -> None:
        """Xabarni o'qilgan deb belgilash"""
        query = """
        UPDATE bot_messages 
        SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        cls.execute_query(query, (message_id,))

    @classmethod
    def mark_message_as_replied(cls, message_id: int) -> None:
        """Xabarga javob berilgan deb belgilash"""
        query = """
        UPDATE bot_messages 
        SET status = 'replied', replied_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        cls.execute_query(query, (message_id,))

    @classmethod
    def get_message_by_id(cls, message_id: int) -> Dict:
        """Xabarni ID bo'yicha olish"""
        query = "SELECT * FROM bot_messages WHERE id = %s"
        return cls.execute_query(query, (message_id,), fetch_one=True)


# ============================================================================
# 4. KEYBOARD MANAGER
# ============================================================================

class KeyboardManager:
    """Keyboardlar generatori"""

    @staticmethod
    def get_role_keyboard() -> InlineKeyboardMarkup:
        """Rol tanlash uchun keyboard"""
        keyboard = [
            [
                InlineKeyboardButton(text="👨‍🎓 Talaba", callback_data="role_student"),
                InlineKeyboardButton(text="👩‍🏫 O'qituvchi", callback_data="role_teacher")
            ],
            [
                InlineKeyboardButton(text="👨‍🏫 Bosh o'qituvchi", callback_data="role_head_teacher")
            ],
            [
                InlineKeyboardButton(text="👨‍💼 Administrator", callback_data="role_admin")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_main_menu(role: str, user_id: int) -> InlineKeyboardMarkup:
        """Asosiy menu - role ga qarab"""
        keyboard = []

        if role == 'student':
            keyboard = [
                [InlineKeyboardButton(text="👨‍🏫 Ustozga xabar yuborish", callback_data="student_send_message")],
                [InlineKeyboardButton(text="📨 Kelgan xabarlar", callback_data="student_view_messages")],
                [InlineKeyboardButton(text="👥 Mening ustozlarim", callback_data="student_my_teachers")],
                [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings")]
            ]

        elif role == 'teacher':
            keyboard = [
                [InlineKeyboardButton(text="📨 Talabalardan xabarlar", callback_data="teacher_view_messages")],
                [InlineKeyboardButton(text="👨‍🎓 Mening talabalarim", callback_data="teacher_my_students")],
                [InlineKeyboardButton(text="💬 Faol chatlar", callback_data="teacher_active_chats")],
                [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings")]
            ]

        elif role == 'head_teacher':
            keyboard = [
                [InlineKeyboardButton(text="📨 Barcha xabarlar", callback_data="head_all_messages")],
                [InlineKeyboardButton(text="👨‍🏫 O'qituvchilar", callback_data="head_teachers_list")],
                [InlineKeyboardButton(text="👨‍🎓 Talabalar", callback_data="head_students_list")],
                [InlineKeyboardButton(text="⚙️ Boshqaruv", callback_data="admin_settings")]
            ]

        elif role == 'admin':
            keyboard = [
                [InlineKeyboardButton(text="👥 Barcha foydalanuvchilar", callback_data="admin_all_users")],
                [InlineKeyboardButton(text="🔗 Bog'lanishlar", callback_data="admin_assignments")],
                [InlineKeyboardButton(text="📊 Tizim statistikasi", callback_data="admin_system_stats")],
                [InlineKeyboardButton(text="⚙️ Tizim sozlamalari", callback_data="admin_system_settings")]
            ]

        # Har doim yordam va chiqish
        keyboard.append([
            InlineKeyboardButton(text="❓ Yordam", callback_data="help"),
            InlineKeyboardButton(text="🚪 Chiqish", callback_data="logout")
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_teachers_for_student(student_id: int) -> Optional[InlineKeyboardMarkup]:
        """Talaba uchun ustozlar ro'yxati"""
        teachers = DatabaseManager.get_teachers_for_student(student_id)

        if not teachers:
            return None

        keyboard = []
        for teacher in teachers:
            icon = "👨‍🏫" if teacher.get('role') == 'head_teacher' else "👩‍🏫"
            text = f"{icon} {teacher['full_name']}"
            if teacher.get('subject'):
                text += f" ({teacher['subject']})"

            keyboard.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"select_teacher_{teacher['telegram_id']}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_students_for_teacher(teacher_id: int) -> Optional[InlineKeyboardMarkup]:
        """Ustoz uchun talabalar ro'yxati"""
        students = DatabaseManager.get_students_for_teacher(teacher_id)

        if not students:
            return None

        keyboard = []
        for student in students:
            text = f"👨‍🎓 {student['full_name']}"
            if student.get('subject'):
                text += f" - {student['subject']}"

            keyboard.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"select_student_{student['telegram_id']}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_chat_messages_keyboard(student_id: int, teacher_id: int, page: int = 0) -> InlineKeyboardMarkup:
        """Chat xabarlari uchun pagination keyboard"""
        keyboard = []

        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="◀️ Oldingi",
                    callback_data=f"chat_page_{student_id}_{teacher_id}_{page - 1}"
                )
            )

        nav_buttons.append(
            InlineKeyboardButton(text=f"📄 {page + 1}", callback_data="noop")
        )

        nav_buttons.append(
            InlineKeyboardButton(
                text="Keyingi ▶️",
                callback_data=f"chat_page_{student_id}_{teacher_id}_{page + 1}"
            )
        )

        keyboard.append(nav_buttons)

        # Action buttons
        keyboard.append([
            InlineKeyboardButton(
                text="💬 Yangi xabar",
                callback_data=f"new_message_{teacher_id}"
            ),
            InlineKeyboardButton(
                text="🔙 Orqaga",
                callback_data="back_to_teachers"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """Bekor qilish keyboard"""
        keyboard = [[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_confirmation_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
        """Tasdiqlash keyboard"""
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=f"confirm_{action}_{data}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="cancel")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ============================================================================
# 5. BOT HANDLERS
# ============================================================================

router = Router()
db = DatabaseManager
kb = KeyboardManager


# ========== START COMMAND ==========

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Start command handler"""
    user = message.from_user
    logger.info(f"🚀 Start from user {user.id} - {user.full_name}")

    # User ni bazaga qo'shish
    db_user = db.get_or_create_user(
        telegram_id=user.id,
        full_name=user.full_name,
        username=user.username
    )

    # Agar user roli bo'lsa, main menu ko'rsatish
    if db_user.get('role'):
        await show_main_menu(message, db_user)
        await state.clear()
        return

    # Rol tanlash
    welcome_text = (
        f"Assalomu alaykum {user.full_name}! 👋\n\n"
        "🏫 O'quvchi-O'qituvchi Aloqa Platformasiga xush kelibsiz!\n\n"
        "Platformadan to'liq foydalanish uchun iltimos, "
        "o'zingizni rolingizni tanlang:"
    )

    await message.answer(
        welcome_text,
        reply_markup=kb.get_role_keyboard()
    )

    await state.set_state(Form.selecting_role)


@router.callback_query(F.data.startswith("role_"))
async def role_selection_handler(callback: CallbackQuery, state: FSMContext):
    """Rol tanlash handler"""
    await callback.answer()

    user = callback.from_user
    role = callback.data.replace('role_', '')

    # Role ni saqlash
    db_user = db.update_user_role(user.id, role)

    if not db_user:
        await callback.message.edit_text("❌ Xatolik yuz berdi. Iltimos, qaytadan urunib ko'ring.")
        await state.clear()
        return

    # Role nomlari
    role_names = {
        'student': "👨‍🎓 Talaba",
        'teacher': "👩‍🏫 O'qituvchi",
        'head_teacher': "👨‍🏫 Bosh o'qituvchi",
        'admin': "👨‍💼 Administrator"
    }

    await callback.message.edit_text(
        f"✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!\n"
        f"📋 Sizning rolingiz: {role_names.get(role, role)}\n\n"
        f"🎉 Endi platformaning barcha imkoniyatlaridan foydalanishingiz mumkin."
    )

    await show_main_menu(callback.message, db_user)
    await state.clear()


# ========== STUDENT FUNCTIONS ==========

@router.callback_query(F.data == "student_send_message")
async def student_send_message(callback: CallbackQuery, state: FSMContext):
    """Talaba: Ustozga xabar yuborishni boshlash"""
    await callback.answer()

    student_id = callback.from_user.id

    # Talabaning ustozlarini olish
    teachers_keyboard = kb.get_teachers_for_student(student_id)

    if not teachers_keyboard:
        await callback.message.edit_text(
            "❌ Sizga hali ustoz bog'lanmagan.\n"
            "Iltimos, administrator yoki bosh o'qituvchiga murojaat qiling.",
            reply_markup=kb.get_main_menu('student', student_id)
        )
        return

    await callback.message.edit_text(
        "✍️ Xabar yuborish\n\n"
        "Qaysi ustozga xabar yubormoqchisiz? Iltimos, ustozni tanlang:",
        reply_markup=teachers_keyboard
    )

    await state.set_state(Form.selecting_teacher)


@router.callback_query(F.data.startswith("select_teacher_"))
async def select_teacher_handler(callback: CallbackQuery, state: FSMContext):
    """Talaba: Ustozni tanlash"""
    await callback.answer()

    student_id = callback.from_user.id

    if callback.data == 'back_to_main':
        db_user = db.get_user(student_id)
        await show_main_menu(callback.message, db_user)
        await state.clear()
        return

    if callback.data == 'cancel':
        await callback.message.edit_text(
            "❌ Xabar yuborish bekor qilindi.",
            reply_markup=kb.get_main_menu('student', student_id)
        )
        await state.clear()
        return

    # Ustoz ID sini olish
    teacher_id = int(callback.data.replace('select_teacher_', ''))

    # Ustoz ma'lumotlarini olish
    teacher = db.get_user(teacher_id)

    if not teacher:
        await callback.message.edit_text("❌ Ustoz topilmadi. Iltimos, qaytadan urunib ko'ring.")
        return

    # State data ga saqlash
    await state.update_data(
        selected_teacher_id=teacher_id,
        selected_teacher_name=teacher['full_name']
    )

    await callback.message.edit_text(
        f"✅ Ustoz tanlandi: {teacher['full_name']}\n\n"
        f"📝 Endi xabaringizni yozing:\n"
        f"(Matn, rasm, fayl yoki ovozli xabar yuborishingiz mumkin)\n\n"
        f"❌ Bekor qilish uchun /cancel",
        reply_markup=kb.get_cancel_keyboard()
    )

    await state.set_state(Form.writing_message)


@router.message(Form.writing_message)
async def student_write_message(message: Message, state: FSMContext):
    """Talaba: Xabar yozish"""
    student = message.from_user
    data = await state.get_data()

    teacher_id = data.get('selected_teacher_id')
    teacher_name = data.get('selected_teacher_name')

    if not teacher_id:
        await message.answer("❌ Xatolik: Ustoz tanlanmagan!")
        await state.clear()
        return

    # Xabar turini aniqlash
    if message.text:
        message_content = message.text
        message_type = 'text'
    elif message.photo:
        message_content = "📷 Rasm"
        message_type = 'photo'
    elif message.document:
        message_content = f"📄 {message.document.file_name}"
        message_type = 'document'
    elif message.voice:
        message_content = "🎤 Ovozli xabar"
        message_type = 'voice'
    else:
        message_content = "📎 Media xabar"
        message_type = 'media'

    # Xabarni bazaga saqlash
    saved_message = db.save_message(
        sender_id=student.id,
        receiver_id=teacher_id,
        message_text=message_content,
        message_type=message_type
    )

    # USTOZGA XABAR YUBORISH
    try:
        teacher_message = (
            f"📨 YANGI XABAR\n"
            f"──────────────\n"
            f"👨‍🎓 Talaba: {student.full_name}\n"
            f"📱 Username: @{student.username if student.username else 'yoq'}\n"
            f"⏰ Vaqt: {datetime.now().strftime('%H:%M, %d.%m.%Y')}\n"
            f"──────────────\n"
            f"📝 Xabar: {message_content}\n"
            f"──────────────\n"
            f"💬 Javob berish uchun quyidagi tugmani bosing:"
        )

        # Ustozga xabarni yuborish
        await message.bot.send_message(
            chat_id=teacher_id,
            text=teacher_message,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="📝 Javob berish",
                    callback_data=f"reply_{saved_message['id']}"
                )
            ]])
        )

        # Talabaga tasdiq
        await message.answer(
            f"✅ Xabaringiz {teacher_name} ustozga yuborildi!\n\n"
            f"🕐 Javobni kuting. Ustoz tez orada javob beradi.",
            reply_markup=kb.get_main_menu('student', student.id)
        )

        logger.info(f"📤 Message sent: Student {student.id} -> Teacher {teacher_id}")

    except Exception as e:
        logger.error(f"❌ Failed to send message to teacher: {e}")
        await message.answer(
            "❌ Xabar yuborishda xatolik yuz berdi. Iltimos, keyinroq urunib ko'ring."
        )

    await state.clear()


# ========== CHAT FUNCTIONS ==========

@router.callback_query(F.data == "student_view_messages")
async def student_view_messages(callback: CallbackQuery, state: FSMContext):
    """Talaba: Kelgan xabarlarni ko'rish"""
    await callback.answer()

    student_id = callback.from_user.id

    # Talabaning ustozlarini olish
    teachers_keyboard = kb.get_teachers_for_student(student_id)

    if not teachers_keyboard:
        await callback.message.edit_text(
            "❌ Sizga hali ustoz bog'lanmagan yoki xabar yo'q.",
            reply_markup=kb.get_main_menu('student', student_id)
        )
        return

    await callback.message.edit_text(
        "📨 Kelgan xabarlar\n\n"
        "Qaysi ustoz bilan suhbatni ko'rmoqchisiz?",
        reply_markup=teachers_keyboard
    )

    await state.set_state(Form.viewing_chat)


@router.callback_query(F.data.startswith("chat_page_"))
async def view_chat_page(callback: CallbackQuery, state: FSMContext):
    """Chat xabarlarini ko'rish (pagination)"""
    await callback.answer()

    parts = callback.data.split('_')
    student_id = int(parts[2])
    teacher_id = int(parts[3])
    page = int(parts[4])

    await show_chat_page(callback, student_id, teacher_id, page)


async def show_chat_page(callback: CallbackQuery, student_id: int, teacher_id: int, page: int = 0):
    """Chat xabarlarini ko'rsatish"""
    # Xabarlarni olish
    messages = db.get_chat_messages(student_id, teacher_id, limit=10)

    if not messages:
        await callback.message.edit_text(
            "💭 Hozircha xabarlar yo'q. Birinchi xabarni siz yuboring!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="💬 Yangi xabar",
                    callback_data=f"new_message_{teacher_id}"
                ),
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="back_to_teachers"
                )
            ]])
        )
        return

    # Xabarlarni formatlash
    chat_text = "💬 Suhbat tarixi:\n\n"

    # Pagination
    page_size = 10
    total_pages = (len(messages) + page_size - 1) // page_size
    page = min(page, total_pages - 1)
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(messages))

    for i in range(start_idx, end_idx):
        msg = messages[i]

        # Vaqt formatlash
        time_str = msg['created_at'].strftime('%H:%M') if isinstance(msg['created_at'], datetime) else msg['created_at']

        # Xabar formatlash
        if msg['sender_id'] == student_id:
            # Talaba yuborgan
            chat_text += f"👨‍🎓 <b>Siz</b> ({time_str}):\n{msg['message_text']}\n\n"
        else:
            # Ustoz yuborgan
            sender_name = msg.get('sender_name', 'Ustoz')
            chat_text += f"👨‍🏫 <b>{sender_name}</b> ({time_str}):\n{msg['message_text']}\n\n"

    chat_text += f"\n📄 Sahifa: {page + 1}/{total_pages}"

    await callback.message.edit_text(
        chat_text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_chat_messages_keyboard(student_id, teacher_id, page)
    )


# ========== TEACHER FUNCTIONS ==========

@router.callback_query(F.data == "teacher_view_messages")
async def teacher_view_messages(callback: CallbackQuery, state: FSMContext):
    """Ustoz: Talabalardan kelgan xabarlarni ko'rish"""
    await callback.answer()

    teacher_id = callback.from_user.id

    # O'qilmagan xabarlarni olish
    unread_messages = db.get_unread_messages_for_teacher(teacher_id)

    if not unread_messages:
        # Talabalar ro'yxatini ko'rsatish
        students_keyboard = kb.get_students_for_teacher(teacher_id)

        if not students_keyboard:
            await callback.message.edit_text(
                "📭 Hozircha yangi xabarlar yo'q.\n"
                "Talabalar sizga xabar yuborganda bu yerda ko'rinadi.",
                reply_markup=kb.get_main_menu('teacher', teacher_id)
            )
            return

        await callback.message.edit_text(
            "👨‍🎓 Talabalar bilan suhbatlar\n\n"
            "Qaysi talaba bilan suhbatni ko'rmoqchisiz?",
            reply_markup=students_keyboard
        )

        await state.set_state(Form.viewing_chat)
        return

    # O'qilmagan xabarlarni ko'rsatish
    message_text = "📨 Yangi kelgan xabarlar:\n\n"

    for msg in unread_messages[:5]:  # Faqat 5 tasini ko'rsatish
        time_str = msg['created_at'].strftime('%H:%M') if isinstance(msg['created_at'], datetime) else msg['created_at']
        message_text += f"👨‍🎓 {msg.get('sender_name', 'Talaba')} ({time_str}):\n"
        message_text += f"{msg['message_text'][:100]}...\n\n"

    if len(unread_messages) > 5:
        message_text += f"\n... va yana {len(unread_messages) - 5} ta xabar"

    keyboard = []
    for msg in unread_messages[:3]:  # Faqat 3 tasiga button
        keyboard.append([
            InlineKeyboardButton(
                text=f"👨‍🎓 {msg.get('sender_name', 'Talaba')} - {msg['message_text'][:30]}...",
                callback_data=f"reply_{msg['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="👥 Barcha talabalar", callback_data="all_students"),
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_main")
    ])

    await callback.message.edit_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("reply_"))
async def reply_to_message(callback: CallbackQuery, state: FSMContext):
    """Xabarga javob berish"""
    await callback.answer()

    if not callback.data.startswith('reply_'):
        return

    message_id = int(callback.data.replace('reply_', ''))
    teacher_id = callback.from_user.id

    # Xabarni olish
    message = db.get_message_by_id(message_id)

    if not message:
        await callback.message.edit_text("❌ Xabar topilmadi.")
        return

    # Xabarni o'qilgan deb belgilash
    db.mark_message_as_read(message_id)

    # Student ma'lumotlarini olish
    student = db.get_user(message['sender_id'])

    # State data ga saqlash
    await state.update_data(
        replying_message_id=message_id,
        replying_student_id=student['telegram_id'],
        replying_student_name=student['full_name'],
        original_message=message['message_text']
    )

    await callback.message.edit_text(
        f"📝 Javob yozish\n\n"
        f"👨‍🎓 Talaba: {student['full_name']}\n"
        f"📩 Original xabar: {message['message_text'][:100]}...\n\n"
        f"💬 Javobingizni yozing:",
        reply_markup=kb.get_cancel_keyboard()
    )

    await state.set_state(Form.replying_message)


@router.message(Form.replying_message)
async def send_reply(message: Message, state: FSMContext):
    """Javob yuborish"""
    teacher = message.from_user
    reply_text = message.text

    data = await state.get_data()

    message_id = data.get('replying_message_id')
    student_id = data.get('replying_student_id')
    student_name = data.get('replying_student_name')

    if not message_id:
        await message.answer("❌ Xatolik: Javob berilayotgan xabar topilmadi!")
        await state.clear()
        return

    # Javobni bazaga saqlash (bu yangi xabar sifatida)
    saved_message = db.save_message(
        sender_id=teacher.id,
        receiver_id=student_id,
        message_text=reply_text,
        message_type='text'
    )

    # Original xabarni "replied" deb belgilash
    db.mark_message_as_replied(message_id)

    # STUDENTGA JAVOBNI YUBORISH
    try:
        reply_message = (
            f"📬 Ustozdan javob!\n"
            f"──────────────\n"
            f"👨‍🏫 Ustoz: {teacher.full_name}\n"
            f"📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"──────────────\n"
            f"💬 Javob: {reply_text}\n"
            f"──────────────\n"
            f"Boshqa savolingiz bo'lsa, yozishingiz mumkin."
        )

        await message.bot.send_message(
            chat_id=student_id,
            text=reply_message
        )

        # Ustozga tasdiq
        await message.answer(
            f"✅ Javobingiz {student_name} ga yuborildi!",
            reply_markup=kb.get_main_menu('teacher', teacher.id)
        )

        logger.info(f"📨 Reply sent: Teacher {teacher.id} -> Student {student_id}")

    except Exception as e:
        logger.error(f"❌ Failed to send reply: {e}")
        await message.answer(
            "❌ Javob yuborishda xatolik. Talaba botni bloklagan bo'lishi mumkin."
        )

    await state.clear()


# ========== YORDAMCHI FUNCTIONS ==========

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await callback.answer()

    user_id = callback.from_user.id
    db_user = db.get_user(user_id)

    if db_user:
        await show_main_menu(callback.message, db_user)
    else:
        await callback.message.edit_text(
            "Iltimos, avval /start ni bosing.",
            reply_markup=ReplyKeyboardRemove()
        )

    await state.clear()


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Bekor qilish"""
    await callback.answer()

    user_id = callback.from_user.id
    db_user = db.get_user(user_id)

    if db_user:
        await show_main_menu(callback.message, db_user)
    else:
        await callback.message.edit_text(
            "❌ Amal bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )

    await state.clear()


@router.callback_query(F.data == "logout")
async def logout_handler(callback: CallbackQuery, state: FSMContext):
    """Chiqish"""
    await callback.answer()

    await callback.message.edit_text(
        "👋 Xayr! Yana kerak bo'lsa, /start ni bosing.\n\n"
        "Botdan chiqdingiz."
    )

    await state.clear()


@router.message(Command("help"))
async def help_command(message: Message):
    """Help command"""
    help_text = (
        "🤖 *Botdan foydalanish qo'llanmasi*\n\n"
        "👨‍🎓 *Talabalar uchun:*\n"
        "1. 'Ustozga xabar yuborish' - ustozingizga xabar yuboring\n"
        "2. 'Kelgan xabarlar' - ustozdan kelgan javoblarni ko'ring\n"
        "3. 'Mening ustozlarim' - bog'langan ustozlaringizni ko'ring\n\n"
        "👩‍🏫 *Ustozlar uchun:*\n"
        "1. 'Talabalardan xabarlar' - yangi xabarlarni ko'ring\n"
        "2. 'Mening talabalarim' - o'z talabalaringiz bilan suhbat\n"
        "3. 'Faol chatlar' - barcha suhbatlarni ko'ring\n\n"
        "👨‍🏫 *Bosh o'qituvchilar:*\n"
        "1. 'Barcha xabarlar' - tizimdagi barcha xabarlar\n"
        "2. 'O'qituvchilar' - o'qituvchilarni boshqarish\n"
        "3. 'Talabalar' - talabalarni boshqarish\n\n"
        "👨‍💼 *Administratorlar:*\n"
        "1. 'Barcha foydalanuvchilar' - userlarni boshqarish\n"
        "2. 'Bog'lanishlar' - talaba-ustoz bog'lash\n"
        "3. 'Tizim statistikasi' - tizim monitoringi\n\n"
        "⚙️ *Sozlamalar:* /settings\n"
        "🚪 *Chiqish:* Menyudan 'Chiqish' tugmasi"
    )

    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("settings"))
async def settings_command(message: Message):
    """Settings command"""
    user = message.from_user
    db_user = db.get_user(user.id)

    if not db_user:
        await message.answer("Iltimos, avval /start ni bosing.")
        return

    settings_text = (
        f"⚙️ *Sozlamalar*\n\n"
        f"👤 *Shaxsiy ma'lumotlar:*\n"
        f"• Ism: {db_user['full_name']}\n"
        f"• Username: @{db_user.get('username', 'yoq')}\n"
        f"• Rol: {db_user['role']}\n"
        f"• Ro'yxatdan o'tgan: {db_user['created_at'].strftime('%d.%m.%Y')}\n\n"
        f"🔔 *Bildirishnomalar:* Yoqilgan\n"
        f"🌐 *Til:* O'zbekcha\n\n"
        f"🛠 *Boshqaruv:*\n"
        f"/help - Yordam\n"
        f"/settings - Sozlamalar"
    )

    await message.answer(settings_text, parse_mode=ParseMode.MARKDOWN)


async def show_main_menu(message: Union[Message, CallbackQuery], db_user: Dict):
    """Asosiy menyuni ko'rsatish"""
    menu_text = get_main_menu_text(db_user)
    keyboard = kb.get_main_menu(db_user['role'], db_user['telegram_id'])

    if isinstance(message, CallbackQuery):
        await message.message.edit_text(menu_text, reply_markup=keyboard)
    else:
        await message.answer(menu_text, reply_markup=keyboard)


def get_main_menu_text(db_user: Dict) -> str:
    """Asosiy menu matni"""
    role_texts = {
        'student': "Siz talaba sifatida ro'yxatdan o'tdingiz.",
        'teacher': "Siz o'qituvchi sifatida ro'yxatdan o'tdingiz.",
        'head_teacher': "Siz bosh o'qituvchi sifatida ro'yxatdan o'tdingiz.",
        'admin': "Siz administrator sifatida ro'yxatdan o'tdingiz."
    }

    return (
        f"🏠 *Asosiy menyu*\n\n"
        f"👤 {db_user['full_name']}\n"
        f"📊 {role_texts.get(db_user['role'], '')}\n\n"
        f"Quyidagi tugmalardan birini tanlang:"
    )


# ============================================================================
# 6. MAIN FUNCTION
# ============================================================================

async def main():
    """Botni ishga tushirish"""

    # Database initialization
    DatabaseManager.initialize()
    logger.info("🚀 Aiogram Bot starting...")

    # Storage setup (Redis yoki Memory)
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        storage = RedisStorage.from_url(f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}")
        logger.info("✅ Redis storage connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis not available, using memory storage: {e}")
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()

    # Bot yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Dispatcher yaratish
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    # Start message
    print("=" * 50)
    print("🤖 AIOGRAM BOT ISHGA TUSHIRILDI")
    print(f"📊 Database: {DB_CONFIG['dbname']}")
    print(f"👤 Admin IDs: {ADMIN_IDS}")
    print("=" * 50)
    print("📝 Log fayli: aiogram_bot.log")
    print("🛑 To'xtatish uchun: Ctrl+C")
    print("=" * 50)

    # Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    # ✅ TOKEN QAYERGA YOZILISHI:
    # 1. .env faylida: TELEGRAM_BOT_TOKEN=your_token_here
    # 2. Agar .env bo'lmasa, yuqoridagi BOT_TOKEN o'zgaruvchisiga to'g'ridan-to'g'ri yozing:
    #    BOT_TOKEN = "1234567890:AAHabcdefghijklmnopqrstuvwxyz-ABCDEF"
    BOT_TOKEN="7880598816:AAEoO4-vBWuKnoZre1oYr1H2y9gYgeppSiI"
    # Token tekshirish
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ XATO: Bot token kiritilmagan!")
        print("Iltimos, .env faylida TELEGRAM_BOT_TOKEN ni to'ldiring yoki")
        print("kodda BOT_TOKEN o'zgaruvchisiga to'g'ridan-to'g'ri token yozing.")
        print("\nToken olish uchun: @BotFather -> /newbot")
        sys.exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot to'xtatildi.")
        print("\n👋 Bot to'xtatildi.")
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        print(f"❌ Bot failed to start: {e}")

