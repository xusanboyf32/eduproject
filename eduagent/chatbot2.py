#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List
import psycopg2
from celery.bin.upgrade import settings
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

# ************************************************************
import os
import django

# Django settings faylini aniqlaymiz
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Django-ni ishga tushuramiz
django.setup()


# ************************************************************
from django.conf import settings




# from config import DB_CONFIG  # Settings dan olingan
DB_CONFIG = settings.DATABASES['bot_storage']


# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================= FSM HOLATLARI =======================
class BotStates(StatesGroup):
    role_selection = State()
    teacher_selection = State()
    student_selection = State()
    waiting_message = State()
    waiting_reply = State()
    admin_mode = State()

# ======================= DATABASE MANAGER =======================
class Database:
    _connection_pool = None

    @classmethod
    def initialize(cls):
        if cls._connection_pool is None:
            cls._connection_pool = pool.SimpleConnectionPool(1, 20, dbname=DB_CONFIG['NAME'],
                user=DB_CONFIG['USER'],
                password=DB_CONFIG['PASSWORD'],
                host=DB_CONFIG['HOST'],
                port=DB_CONFIG['PORT'])


            cls._create_tables()
            logger.info("Database pool yaratildi ✅")

    @classmethod
    def _create_tables(cls):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                username VARCHAR(100),
                role VARCHAR(20) NOT NULL DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """
            CREATE TABLE IF NOT EXISTS connections (
                id SERIAL PRIMARY KEY,
                student_id BIGINT NOT NULL REFERENCES users(telegram_id),
                teacher_id BIGINT NOT NULL REFERENCES users(telegram_id),
                subject VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender_id BIGINT NOT NULL REFERENCES users(telegram_id),
                receiver_id BIGINT NOT NULL REFERENCES users(telegram_id),
                message_text TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                read_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        conn = cls.get_connection()
        try:
            with conn.cursor() as cur:
                for q in queries:
                    cur.execute(q)
            conn.commit()
            logger.info("Database jadvallari yaratildi ✅")
        finally:
            cls.return_connection(conn)

    @classmethod
    def get_connection(cls):
        if cls._connection_pool is None:
            cls.initialize()
        return cls._connection_pool.getconn()

    @classmethod
    def return_connection(cls, conn):
        cls._connection_pool.putconn(conn)

    @classmethod
    def execute_query(cls, query, params=None, fetch_one=False, fetch_all=False):
        conn = cls.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or ())
                if fetch_one:
                    return cur.fetchone()
                if fetch_all:
                    return cur.fetchall()
                conn.commit()
                return cur.rowcount
        finally:
            cls.return_connection(conn)

    # ===== USER OPERATIONS =====
    @classmethod
    def create_user(cls, telegram_id: int, full_name: str, username: str = None):
        query = """
        INSERT INTO users (telegram_id, full_name, username)
        VALUES (%s, %s, %s)
        ON CONFLICT (telegram_id) DO UPDATE
        SET full_name = EXCLUDED.full_name,
            username = EXCLUDED.username,
            updated_at = CURRENT_TIMESTAMP
        RETURNING *
        """
        return cls.execute_query(query, (telegram_id, full_name, username), fetch_one=True)

    @classmethod
    def update_user_role(cls, telegram_id: int, role: str):
        query = "UPDATE users SET role=%s, updated_at=CURRENT_TIMESTAMP WHERE telegram_id=%s RETURNING *"
        return cls.execute_query(query, (role, telegram_id), fetch_one=True)

    @classmethod
    def get_user(cls, telegram_id: int):
        return cls.execute_query("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,), fetch_one=True)

    @classmethod
    def get_users_by_role(cls, role: str):
        return cls.execute_query("SELECT * FROM users WHERE role=%s ORDER BY full_name", (role,), fetch_all=True)

    # ===== CONNECTION OPERATIONS =====
    @classmethod
    def create_connection(cls, student_id: int, teacher_id: int, subject: str = None):
        query = """
        INSERT INTO connections (student_id, teacher_id, subject)
        VALUES (%s, %s, %s)
        ON CONFLICT (student_id, teacher_id) DO UPDATE SET is_active=TRUE, created_at=CURRENT_TIMESTAMP
        RETURNING *
        """
        return cls.execute_query(query, (student_id, teacher_id, subject), fetch_one=True)

    @classmethod
    def get_student_teachers(cls, student_id: int):
        query = """
        SELECT u.*, c.subject
        FROM users u
        JOIN connections c ON u.telegram_id = c.teacher_id
        WHERE c.student_id=%s AND c.is_active=TRUE
        ORDER BY u.full_name
        """
        return cls.execute_query(query, (student_id,), fetch_all=True)

    @classmethod
    def get_teacher_students(cls, teacher_id: int):
        query = """
        SELECT u.*, c.subject
        FROM users u
        JOIN connections c ON u.telegram_id = c.student_id
        WHERE c.teacher_id=%s AND c.is_active=TRUE
        ORDER BY u.full_name
        """
        return cls.execute_query(query, (teacher_id,), fetch_all=True)

    # ===== MESSAGE OPERATIONS =====
    @classmethod
    def save_message(cls, sender_id: int, receiver_id: int, message_text: str):
        query = "INSERT INTO messages (sender_id, receiver_id, message_text) VALUES (%s,%s,%s) RETURNING *"
        return cls.execute_query(query, (sender_id, receiver_id, message_text), fetch_one=True)

    @classmethod
    def get_chat_messages(cls, user1_id: int, user2_id: int, limit: int = 50):
        query = """
        SELECT m.*, s.full_name as sender_name, r.full_name as receiver_name
        FROM messages m
        JOIN users s ON m.sender_id = s.telegram_id
        JOIN users r ON m.receiver_id = r.telegram_id
        WHERE (m.sender_id=%s AND m.receiver_id=%s) OR (m.sender_id=%s AND m.receiver_id=%s)
        ORDER BY m.created_at DESC
        LIMIT %s
        """
        return cls.execute_query(query, (user1_id, user2_id, user2_id, user1_id, limit), fetch_all=True)

    @classmethod
    def mark_as_read(cls, message_id: int):
        query = "UPDATE messages SET is_read=TRUE, read_at=CURRENT_TIMESTAMP WHERE id=%s"
        return cls.execute_query(query, (message_id,))

    @classmethod
    def get_unread_messages(cls, user_id: int):
        query = """
        SELECT m.*, u.full_name as sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.telegram_id
        WHERE m.receiver_id=%s AND m.is_read=FALSE
        ORDER BY m.created_at DESC
        """
        return cls.execute_query(query, (user_id,), fetch_all=True)
