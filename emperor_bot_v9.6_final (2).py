# =================================================================================================
# =================================================================================================
# ||                                                                                             ||
# ||      بسم الله الرحمن الرحيم - بوت الإمبراطور لإدارة حسابات التليجرام (الإصدار المطور)        ||
# ||                                                                                             ||
# =================================================================================================
# =================================================================================================
# ||                                                                                             ||
# ||   الإصدار: 9.5 (إصلاحات شاملة وتحسين الاستقرار)                                             ||
# ||   المطور: Gemini AI & User Suggestions                                                       ||
# ||   تاريخ التحديث: 19-06-2025                                                                  ||
# ||                                                                                             ||
# ||   الوصف: هذا الإصدار يقوم بإصلاح شامل لمشاكل استدعاء دوال الترجمة، ويوحد معالجات المحادثات   ||
# ||   المتشابهة لمنع التداخل، ويحسن من منطق الأزرار واستجابتها، ويضيف مخرج طوارئ للمحادثات.      ||
# ||                                                                                             ||
# =================================================================================================
# =================================================================================================


# ==============================================================================
# ==============================================================================
# ==============================================================================
# ==============================================================================
# ||                      أولاً: استيراد المكتبات الضرورية                       ||
# ==============================================================================
# --- مكتبات أساسية في بايثون ---
import os
import logging
import sqlite3
import asyncio
import re
import sys
import csv
import io
import shutil
import json
from datetime import datetime, timedelta
from unittest.mock import Mock
import math
import pytz
import uuid
from PIL import Image
from collections import deque, defaultdict
import time # لاستخدام time.monotonic() في تجمعات الاتصال

# --- التحقق من وجود psutil ---
try:
    import psutil
except ImportError:
    psutil = None
# --- مكتبات أساسية في بايثون ---
# ... (imports)
import random
import string
import imaplib # <== [إضافة جديدة] للتعامل مع بريد Gmail
import email # <== [إضافة جديدة] لتحليل رسائل البريد
from email.header import decode_header
import base64

# --- مكتبة التشفير ---
try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    print("مكتبة 'cryptography' غير مثبتة. يرجى تشغيل: pip install cryptography")
    sys.exit(1)

# --- مكتبة تيليثون (Telethon) ---
from telethon.sync import TelegramClient
from telethon.sessions import StringSession, SQLiteSession
from telethon.tl.types import Channel, Chat, User, ChannelParticipantsRecent
from telethon.tl import functions, types
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError,
    PhoneNumberBannedError, UserDeactivatedBanError, RpcCallFailError,
    ApiIdInvalidError, PasswordHashInvalidError, UsernameOccupiedError,
    UsernameInvalidError, UserNotParticipantError, UserAlreadyParticipantError,
    ChannelPrivateError, InviteHashExpiredError, InviteHashInvalidError,
    AuthKeyUnregisteredError, EmailUnconfirmedError, AuthKeyDuplicatedError
)
from telethon import events # تم التأكد من استيراد events بشكل صريح

# --- مكتبة بوت تيليجرام (python-telegram-bot) ---
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants, CallbackQuery
from telegram.ext import (
    Application, CommandHandler, ContextTypes, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters,
)
from telegram.helpers import escape_markdown as markdown_v2
from telegram.error import TelegramError, BadRequest

# --- مكتبة جدولة المهام (APScheduler) ---
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- إعداد نظام تسجيل المعلومات (Logging) ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Damascus")

# ==============================================================================
# ||                      ثانياً: الإعدادات والمعلومات الأساسية                   ||
# ==============================================================================
# --- معلومات المصادقة (Authentication) ---
TOKEN = "7650705319:AAGr_F1DEURsmodGT2ECAppXZlEjyRIc3kk"  # توكن البوت من @BotFather
API_ID = 21669021                                      # API ID من my.telegram.org
API_HASH = "bcdae25b210b2cbe27c03117328648a2"           # API Hash من my.telegram.org

# --- معلومات الأدمن والمطور ---
ADMIN_IDS = [6831264078]
DEV_USERNAME = "K_6_3"

# --- [إضافة جديدة] إعدادات التشفير والميزات الجديدة ---
# هام: يجب إنشاء هذا المفتاح مرة واحدة فقط والاحتفاظ به. إذا غيرته، ستفقد الوصول للبيانات المشفرة القديمة.
# لتوليد مفتاح جديد بنفسك، شغل هذا الأمر في بايثون: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
# ... (الكود الموجود لديك) ...
ENCRYPTION_KEY = b'p3uGZ_iYx9qA8s7v5bB2eD_fG-hJ1kM4nO6rT3wXzCg=' # <== هذا هو المفتاح بالصيغة الصحيحة
cipher_suite = Fernet(ENCRYPTION_KEY)
DEFAULT_2FA_HINT = "@K_6_3"

# دوال الترميز/فك الترميز لـ Base64 (مستخدمة خصيصاً لكلمات مرور الإيميل)
def encrypt_email_password_base64(password: str) -> str:
    """يقوم بترميز كلمة مرور الإيميل باستخدام Base64.
    ملاحظة: هذا ليس تشفيراً آمناً، مجرد ترميز.
    """
    return base64.b64encode(password.encode('utf-8')).decode('utf-8')

def decrypt_email_password_base64(encrypted_password: str) -> str:
    """يفك ترميز كلمة مرور الإيميل من Base64.
    ملاحظة: هذا ليس تشفيراً آمناً، مجرد فك ترميز.
    """
    try:
        return base64.b64decode(encrypted_password.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.error(f"خطأ أثناء فك ترميز كلمة مرور الإيميل Base64: {e}")
        return "DECRYPTION_FAILED"

# ... (بقية الكود الموجود لديك) ...        


# --- إعدادات المجلدات وقاعدة البيانات ---
SESSIONS_DIR = 'sessions'
BACKUP_DIR = 'backups'
DB_NAME = 'bot_database_v9.db'
for a_dir in [SESSIONS_DIR, BACKUP_DIR]:
    if not os.path.exists(a_dir):
        os.makedirs(a_dir)

# --- تعريف مراحل المحادثات (Conversation States) ---
# ... (الكود الموجود لديك) ...
(
    # Management & Main Flow
    SELECT_ACCOUNT, GET_NEW_VALUE, CONFIRM_ACTION, GET_TARGET_LINK, GET_MESSAGE_CONTENT,
    GET_PHOTO, GET_BIO, VIEW_LOGS, ADD_AWAIT_INPUT, ADD_CODE, ADD_PASSWORD,
    MANAGE_ACCOUNT, SET_NEW_USERNAME, SET_NEW_PASSWORD, CONFIRM_NEW_PASSWORD,

    # 2FA Flow (تم دمج كل الحالات هنا)
    TFA_START, TFA_GET_NEW_PASS, TFA_GET_HINT, TFA_GET_RECOVERY_EMAIL, TFA_GET_EMAIL_CODE,
    TFA_MENU, TFA_CHANGE_EMAIL_GET, TFA_DISABLE_GET_PASS,

    # Proxies Flow
    MANAGE_PROXIES, ADD_PROXY, SELECT_PROXY_ACTION, ASSIGN_PROXY_SELECT_ACCOUNT,

    # Bulk Actions Base
    SELECT_ACCOUNTS_FOR_ACTION, GET_LINK_FOR_BULK_ACTION, CONFIRM_BULK_ACTION,
    CONFIRM_BULK_NO_LINK_ACTION, BULK_DELETE_OPTIONS,

    # Scraper Flow
    SCRAPER_SELECT_TYPE, SCRAPER_GET_LIMIT,

    # Admin Panel
    BOT_ADMIN_MENU, SUB_GET_ID, SUB_GET_DAYS, SUB_DEACTIVATE_GET_ID, ADMIN_RESTORE_CONFIRM,
    ADMIN_RESTART_CONFIRM, ADMIN_CANCEL_TASKS_CONFIRM,

    # Broadcast Flow
    BROADCAST_START, BROADCAST_GET_TARGET_TYPE, BROADCAST_GET_TARGET_PARAMS,
    BROADCAST_GET_MESSAGE, BROADCAST_CONFIRM,

    # Auto-Reply Flow
    AUTOREPLY_MENU, AUTOREPLY_GET_KEYWORD, AUTOREPLY_GET_RESPONSE,

    # Cleaner Flow
    CLEANER_MENU, CLEANER_OPTIONS, CLEANER_CONFIRM,
    CLEANER_MENU_SINGLE, CLEANER_CONFIRM_SINGLE,

    # Scheduler Flow
    SCHEDULER_MENU, SCHEDULER_SELECT_TYPE, SCHEDULER_SELECT_ACCOUNTS,
    SCHEDULER_GET_TARGET, SCHEDULER_GET_CONTENT, SCHEDULER_GET_CRON,

    # Session Export
    BULK_EXPORT_SELECT_ACCOUNTS, BULK_EXPORT_CONFIRM,

    # Language Selection
    LANG_SELECT,

    # Story Flow
    STORY_MENU, STORY_GET_FILE, STORY_GET_CAPTION, STORY_ASK_PRIVACY, STORY_ASK_PERIOD,

    # Bulk Story Flow
    BULK_STORY_GET_FILE, BULK_STORY_GET_CAPTION, BULK_STORY_ASK_PRIVACY,
    BULK_STORY_ASK_PERIOD, BULK_STORY_CONFIRM,

    # Bulk Actions Specifics
    BULK_GET_BIO, BULK_GET_NAME, BULK_GET_PHOTO, BULK_SELECT_PROXY,
    BULK_CONTACTS_GET_LIST, BULK_CONTACTS_CONFIRM, BULK_CONTACTS_EXECUTE,

    # Single Contact Management
    SINGLE_CONTACT_MENU, SINGLE_CONTACT_GET_LIST, SINGLE_CONTACT_CONFIRM_DELETE, SINGLE_CONTACT_GET_FILE,

    # Email Management
    MANAGE_EMAILS_MENU, EMAILS_GET_ADDRESS, EMAILS_GET_APP_PASS,
    FETCH_EMAIL_SELECT, # <== أضف هذا السطر الجديد

    # Bulk 2FA
    BULK_2FA_CHOOSE_MODE, BULK_2FA_GET_UNIFIED_PASS

) = range(90) # <== قم بتغيير هذا الرقم من 89 إلى 90
# ... (بقية الكود الموجود لديك) ...

# ==============================================================================
# ||                   [إضافة] دعم اللغات المتعددة                              ||
# ==============================================================================

# ملاحظة هامة: من الأفضل وضع هذا القاموس الضخم في ملفات منفصلة (مثل ar.json و en.json)
# وجعل الكود يقوم بتحميلها عند بدء التشغيل. هذا يجعل الملف الرئيسي أكثر نظافة وسهولة في الصيانة.
LANGUAGE_DATA = {
    'ar': {
        "welcome_message": "👋 أهلاً بك يا {user_mention} في **بوت الإمبراطور (الإصدار 9.5)**.\n\nاختر أحد الخيارات من القائمة للبدء.",
        "choose_language": "الرجاء اختيار اللغة:",
        "language_set_success": "✅ تم تعيين اللغة إلى العربية.",
        "language_set_fail": "❌ حدث خطأ أثناء تعيين اللغة.",
        "not_authorized": "⛔️ عذراً، هذا البوت متاح فقط للمستخدمين المشتركين.\n\nقد تكون غير مشترك أو أن اشتراكك قد انتهى!",
"manage_import_emails_button_main": "📧 إدارة إيميلات الاستيراد",
"manage_emails_title": "📧 **إدارة إيميلات الاستيراد** 📧\n\nهذه الإيميلات تُستخدم لجلب أكواد التحقق تلقائياً.",
"no_import_emails": "لم تقم بإضافة أي إيميلات استيراد بعد.",
"add_email_button": "➕ إضافة إيميل جديد",
"email_status_checking": "⏳ جارٍ فحص الحالة...",
"email_status_ok": "✅ يعمل",
"email_status_fail": "❌ فشل الدخول",
"check_status_button": "🔬 فحص",
"enter_gmail_address": "الرجاء إرسال عنوان بريد Gmail.",
"enter_app_password": "الآن، يرجى إرسال **كلمة مرور التطبيقات** المكونة من 16 حرفاً الخاصة بهذا الإيميل.",
"email_added_success": "✅ تم إضافة الإيميل بنجاح.",
"email_already_exists": "⚠️ هذا الإيميل موجود بالفعل.",
"email_deleted_success": "✅ تم حذف الإيميل بنجاح.",
"invalid_email_format": "❌ صيغة البريد الإلكتروني غير صحيحة.",
"bulk_2fa_button": "🔐 تعيين 2FA جماعي",
"bulk_2fa_menu_title": "🔐 **تعيين التحقق بخطوتين (2FA) جماعي**\n\nاختر طريقة تعيين كلمة المرور للحسابات المحددة ({count} حساب):",
"returned_to_main_menu": "🏠 تم الرجوع إلى القائمة الرئيسية.", # <== أضف هذا السطر
"2fa_mode_unified_user": "🔑 موحدة (أنا سأدخلها)",
"2fa_mode_random_unique": "🎲 عشوائية (لكل حساب كلمة)",
"2fa_mode_random_unified": "🎲 موحدة (عشوائية من البوت)",
"enter_unified_2fa_pass": "أرسل كلمة المرور الموحدة التي تريد تطبيقها على كل الحسابات.",
"bulk_2fa_report_title": "📋 **تقرير تعيين 2FA الجماعي**",
"bulk_2fa_starting": "⏳ **بدء عملية تعيين 2FA لـ {count} حساب...**\nالعملية قد تكون طويلة، يرجى الانتظار.",
"bulk_2fa_no_emails_error": "❌ **خطأ:** لا يمكنك المتابعة. يجب عليك إضافة إيميل استيراد واحد على الأقل من القائمة الرئيسية أولاً.",
"2fa_set_success": "نجاح",
"2fa_set_fail": "فشل",
"account_already_exists_for_user": "⚠️ هذا الرقم مسجل بالفعل في حسابك. يمكنك إدارته من قسم 'إدارة حساباتك'.",
"2fa_pass_gen_and_saved": "تم إنشاء كلمة المرور وحفظها",
"2fa_email_verify_auto_attempt": "محاولة جلب كود التحقق من الإيميل تلقائياً...",
"2fa_email_verify_auto_success": "تم جلب الكود وتأكيد البريد بنجاح!",
"2fa_email_verify_auto_fail": "فشل الجلب التلقائي، يرجى المتابعة يدوياً.",
        "check_sub_status_button": "💳 التحقق من حالة الاشتراك",
        "contact_dev_button": "🧑‍💻 التواصل مع المطور",
        "main_menu_return": "🏠 تم الرجوع إلى القائمة الرئيسية.",
        "back_to_main_menu": "🏠 رجوع للقائمة الرئيسية",
        "action_cancelled": "👍 تم إلغاء العملية.",
"login_code_error_generic": "❌ حدث خطأ\n\nإما أن الكود الذي أدخلته غير صحيح، أو أن صلاحيته قد انتهت.\n\n**💡 حاول مجدداً، وجرب إرسال الكود مع فراغات بين الأرقام (مثال: `1 2 3 4 5`)**",
        "no_accounts_to_check": "❌ لا توجد حسابات لفحصها.",
        "checking_accounts": "⏳ **جاري فحص {count} حساب...**\n\nهذه العملية قد تستغرق بعض الوقت.",
        "check_accounts_report_header": "📋 **تقرير حالة حساباتك:**\n",
        "check_accounts_summary_header": "**ملخص:**",
        "status_active": "نشط",
        "status_banned": "محظور",
        "status_needs_login": "يحتاج تسجيل",
        "status_unknown": "غير معروف",
        "check_account_quick_action": "إجراءات لـ {phone}",
        "delete_account_button": "🗑️ حذف الحساب",
        "ignore_button": "✖️ تجاهل",
        "login_account_button": "🔑 تسجيل الدخول",
        "add_account_instructions": "الرجاء إرسال:\n- **رقم هاتف** مع رمز الدولة (مثال: `+963...`).\n- **جلسة Telethon** نصية.\n- **ملف جلسة** بامتداد `.session`.",
        "go_back_button": "🔙 رجوع",
        "invalid_input_format": "❌ صيغة الإدخال غير صحيحة. يرجى إرسال رقم هاتف صالح أو جلسة نصية.",
        "session_file_received": "⏳ تم استلام ملف الجلسة، جاري المعالجة والتحقق...",
        "invalid_session_file": "❌ الملف غير صالح. أرسل ملف جلسة ينتهي بـ `.session`.",
        "session_processing_failed": "❌ فشلت معالجة ملف الجلسة.\n**السبب:** الجلسة منتهية الصلاحية أو غير صالحة. يرجى إنشاء جلسة جديدة.",
        "unexpected_error": "❌ حدث خطأ غير متوقع: {error}",
        "phone_code_sent": "✅ تم إرسال الكود إلى حسابك في تيليجرام، يرجى إرساله هنا.",
        "flood_wait_error": "❌ تم حظرك مؤقتاً. انتظر لمدة {seconds} ثانية.",
        "phone_banned_error": "❌ هذا الرقم محظور من قبل تيليجرام.",
        "account_banned_admin_alert": "⚠️ *تنبيه حظر حساب* ⚠️\nتم اكتشاف أن الحساب `{phone}` محظور أثناء محاولة إضافته.",
        "string_session_checking": "⏳ جاري التحقق من الجلسة النصية...",
        "string_session_invalid": "❌ الجلسة النصية غير صالحة أو منتهية الصلاحية.",
        "string_session_success": "✅ تم التحقق من الجلسة وحفظها بنجاح للحساب: `{phone}`",
        "account_needs_password": "🔒 الحساب محمي بكلمة مرور التحقق بخطوتين. يرجى إرسالها.",
        "invalid_code": "❌ الكود غير صحيح. يرجى المحاولة مجدداً.",
        "login_success": "✅ تم تسجيل الدخول بنجاح للحساب: {first_name}",
        "invalid_password": "❌ كلمة المرور غير صحيحة. حاول مجدداً.",
        "dashboard_title": "📊 **لوحة معلوماتك** 📊",
        "loading_dashboard": "⏳ جاري تحميل لوحة المعلومات...",
        "account_stats_header": "👤 **إحصائيات حساباتك:** (الإجمالي: `{total}`)",
        "proxy_stats_header": "🌐 **إحصائيات البروكسي (العامة):**",
        "admin_stats_header": "👑 **إحصائيات إدارية:**",
        "active_subs_count": "المشتركون النشطون: {active_subs}",
        "refresh_button": "🔄 تحديث",
        "add_account_button_main": "➕ إضافة حساب",
        "remove_account_button_main": "➖ إزالة حساب",
        "manage_accounts_button_main": "👤 إدارة حساباتك",
        "scheduled_tasks_button_main": "⏰ المهام المجدولة",
        "manage_proxies_button_main": "🌐 إدارة البروكسيات",
        "check_accounts_button_main": "✔️ فحص حساباتك",
        "dashboard_button_main": "📊 لوحة معلوماتك",
        "automation_section_button_main": "🤖 قسم المهام الآلية 🤖",
        "extraction_section_button_main": "⚙️ قسم الاستخراج",
        "export_csv_button_main": "📤 تصدير (CSV)",
        "bulk_export_button_main": "🔑 /أستخراج جلسات جماعي",
        "contact_dev_button_main": "📞 التواصل مع المطور",
        "admin_panel_button_main": "👑 إدارة البوت",
        "automation_menu_title": "🤖 قسم المهام الآلية 🤖\n\nاختر مهمة لتنفيذها بشكل جماعي على حساباتك النشطة.",
        "join_bulk_button": "🚀 انضمام جماعي",
        "leave_bulk_button": "👋 مغادرة جماعية",
        "cleaner_button": "🧹 منظف الحسابات",
        "logout_bulk_button": "↪️ تسجيل خروج جماعي",
        "scraper_menu_title": "⚙️ قسم استخراج البيانات ⚙️\n\nاختر أداة لاستخراج المعلومات.",
        "extract_members_button": "👥 استخراج أعضاء مجموعة",
        "account_management_title": "👤 **إدارة حساباتك** 👤\n\nاختر حسابًا من القائمة لعرض خيارات الإدارة:",
        "error_account_not_found": "❌ خطأ: الحساب غير موجود أو لا تملكه.",
        "proxy_not_set": "لم يتم التعيين",
        "last_check_not_available": "لم يتم",
        "add_method_unknown": "غير معروف",
"yes_button": "✅ نعم",
"no_button": "❌ لا",
        "account_details_header": "⚙️ **إدارة الحساب:** `{phone}`",
        "account_name": "الاسم:",
        "account_id": "المعرف:",
        "account_status": "الحالة:",
        "account_last_check": "آخر فحص:",
        "account_add_method": "طريقة الإضافة:",
        "bulk_proxy_assign_button": "🌐 تعيين بروكسي جماعي",
"select_proxy_for_bulk_assign": "اختر البروكسي الذي تريد تعيينه للحسابات المحددة:",
        "account_session_date": "تاريخ الجلسة:",
        "session_age": "عمر الجلسة:",
        "account_proxy": "البروكسي:",
        "update_data_button": "🔄 تحديث البيانات",
        "extract_session_button": "🔑 استخراج جلسة",
        "change_name_button": "📝 تغيير الاسم",
        "change_bio_button": "✍️ تغيير النبذة",
        "change_photo_button": "🖼️ تغيير الصورة",
        "change_username_button": "تغيير اليوزر 🆔",
        "manage_2fa_button": "🔐 إدارة 2FA",
        "clean_account_button": "🧹 تنظيف الحساب",
        "auto_replies_button": "📨 الردود الآلية",
"tfa_menu_title": "🔐 **إدارة التحقق بخطوتين (2FA)**",
"tfa_status_header": "📊 **الحالة الحالية للحساب `{phone}`:**",
"tfa_is_enabled": "✅ مفعلة",
"tfa_is_disabled": "❌ معطلة",
"tfa_recovery_email": "بريد الاسترداد:",
"tfa_no_recovery_email": "غير معين",
"tfa_view_status_button": "⚙️ عرض الحالة",
"tfa_change_password_button": "🔑 تعيين | تغيير كلمة المرور",
"tfa_change_email_button": "✉️ إضافة/تغيير بريد الاسترداد",
"tfa_disable_button": "🔓 إزالة الحماية (تعطيل)",
"tfa_enter_new_recovery_email": "✉️ يرجى إرسال بريد الاسترداد الجديد.",
"tfa_email_change_success": "✅ تم تغيير بريد الاسترداد بنجاح.",
"tfa_email_change_failed": "❌ فشل تغيير بريد الاسترداد: {error}",
"tfa_disable_prompt": "⚠️ **تأكيد** ⚠️\nلتعطيل الحماية، يرجى إدخال كلمة المرور الحالية.",
"tfa_disable_success": "✅ تم تعطيل التحقق بخطوتين بنجاح.",
"tfa_disable_failed": "❌ فشل تعطيل الحماية: {error}",
        "active_sessions_button": "🛡️ الجلسات النشطة",
        "all_other_sessions_deleted_success": "✅ تم حذف جميع الجلسات الأخرى بنجاح.",
        "reset_auths_warning": "⚠️ **تحذير** ⚠️\nأنت على وشك إنهاء جميع الجلسات الأخرى النشطة لهذا الحساب باستثناء جلسة البوت الحالية. هل أنت متأكد من المتابعة؟",
        "yes_delete_now": "‼️ نعم، احذف الآن",
        "logging_out_account": "⏳ جاري تسجيل الخروج من الحساب `{phone}`...",
        "get_last_message_button": "📥 آخر رسالة",
        "assign_proxy_button": "🌐 تعيين بروكسي",
        "activity_log_button": "📜 سجل النشاط",
        "logout_account_button": "🚪 تسجيل الخروج",
        "delete_account_final_button": "🗑️ مسح وتسجيل خروج",
        "extracting_session": "⏳ جاري استخراج الجلسة...", "extract_session_failed_login_needed": "⚠️ لا يمكن استخراج الجلسة، الحساب يحتاج لتسجيل الدخول.",
        "extract_session_failed_error": "❌ خطأ: {error}",
        "session_code_header": "🔑 **كود جلسة للحساب `{phone}`:**\n\n`{session_string}`",
        "updating_account_data": "⏳ جاري تحديث بيانات الحساب `{phone}`...",
        "account_needs_login_alert": "⚠️ الحساب يحتاج لتسجيل دخول.",
        "enter_new_first_name": "📝 يرجى إرسال الاسم الأول الجديد. لإضافة اسم أخير، استخدم الصيغة: `الاسم الأول | الاسم الأخير`\n\nلإلغاء العملية، أرسل /cancel",
        "enter_new_bio": "✍️ يرجى إرسال النبذة التعريفية (البايو) الجديدة (بحد أقصى 70 حرف).\n\nلإلغاء العملية، أرسل /cancel",
        "enter_new_username": "🆔 يرجى إرسال اسم المستخدم الجديد (بدون @).\n\nلإلغاء العملية، أرسل /cancel",
        "send_new_photo": "🖼️ يرجى إرسال الصورة التي تريد تعيينها كصورة شخصية.\n\nلإلغاء العملية، أرسل /cancel",
        "updating_name": "⏳ جاري تحديث الاسم...",
        "name_update_success": "✅ تم تحديث الاسم بنجاح.",
        "updating_bio": "⏳ جاري تحديث النبذة...",
        "bio_update_success": "✅ تم تحديث النبذة بنجاح.",
        "updating_username": "⏳ جاري محاولة تغيير اسم المستخدم إلى @{username}...",
        "username_occupied": "❌ هذا المعرف مستخدم بالفعل. يرجى اختيار معرف آخر.",
        "username_invalid": "❌ صيغة المعرف غير صالحة. يجب أن يكون طوله 5 أحرف على الأقل.",
        "username_update_success": "✅ تم تغيير اسم المستخدم بنجاح.",
        "uploading_photo": "⏳ جاري تحميل وتعيين الصورة الجديدة...",
        "photo_update_success": "✅ تم تغيير الصورة الشخصية بنجاح.",
        "activity_log_title": "📜 **سجل نشاط الحساب `{phone}`**",
        "no_activity_log": "لا توجد أي أنشطة مسجلة.",
        "log_page": "صفحة {current_page}/{total_pages}",
        "quick_action_message": "اختر إجراءً سريعاً للحساب `{phone}`:",
        "admin_account_banned_alert": "🔴 *تنبيه حظر حساب* 🔴\nتم اكتشاف أن الحساب `{phone}` (المالك: `{owner_id}`) قد تم حظره.",
        "security_alert_new_login": "🔒 *تنبيه أمني: تسجيل دخول جديد* 🔒\n\nتم اكتشاف جلسة جديدة على الحساب: `{phone}` (المالك: `{owner_id}`)\n**التفاصيل:**\n- الجهاز: `{device_model}`\n- الموقع: `{ip}` (`{country}`)\n- التطبيق: `{app_name}`",
        "session_key_unregistered": "Session key is invalid or expired.",
        "single_cleaner_start_title": "**🧹 منظف الحساب المتقدم `{phone}`**\n\nاختر مهمة التنظيف. هذا الإجراء نهائي ولا يمكن التراجع عنه.",
        "leave_all_channels": "👋 مغادرة كل القنوات",
        "leave_all_groups": "🚶‍♂️ مغادرة كل المجموعات",
        "delete_bot_chats": "🤖 حذف محادثات البوتات",
        "delete_private_no_contact_chats": "👤 حذف الخاص (بدون جهات اتصال)",
        "delete_deleted_contacts": "🗑️ حذف جهات الاتصال المحذوفة",
        "full_clean": "💥 تنظيف شامل (كل ما سبق)",
        "back_to_account_management": "🔙 رجوع لإدارة الحساب",
        "confirm_single_cleaner": "**‼️ تأكيد نهائي للحساب `{phone}` ‼️**\n\nهل أنت متأكد من تنفيذ مهمة **'{action_text}'**؟\nهذا الإجراء لا يمكن التراجع عنه.",
        "yes_clean_now": "‼️ نعم، قم بالتنظيف",
        "cancel_button": "🔙 إلغاء",
        "cleaner_error_missing_info": "❌ حدث خطأ، معلومات المهمة مفقودة.",
        "starting_single_cleaner": "⏳ **بدء التنظيف للحساب `{phone}`...**\nجارٍ الاتصال وإحصاء العناصر...",
        "checking_contacts": "⏳ جارٍ فحص جهات الاتصال...",
        "no_deleted_contacts": "✅ لا توجد أي جهات اتصال بحسابات محذوفة.",
        "deleted_contacts_success": "✅ تم بنجاح حذف `{count}` من جهات الاتصال المحذوفة.",
        "starting_cleaner_found_dialogs": "⏳ **بدء التنظيف...** تم العثور على `{total_items}` محادثة.",
        "cleaning_in_progress": "**🧹 جاري التنظيف للحساب `{phone}`...**",
        "cleaner_completed": "✅ **اكتمل التنظيف للحساب `{phone}`**\n\n**النتائج:**\n",
        "channels_left": "- القنوات التي تم مغادرتها",
        "groups_left": "- المجموعات التي تم مغادرتها",
        "bot_chats_deleted": "- محادثات البوتات المحذوفة",
        "private_chats_deleted": "- المحادثات الخاصة المحذوفة",
        "errors_occurred": "- الأخطاء التي حدثت",
        "cleaner_failed_error": "❌ فشل التنظيف: `{error}`",
        "getting_active_sessions": "⏳ جاري جلب الجلسات النشطة...",
        "current_bot_session": "📍 جلسة البوت الحالية",
        "device": "📱 الجهاز",
        "platform": "💻 النظام",
        "application": "🚀 التطبيق",
        "ip_address": "📍 الآيبي",
        "country": "الدولة",
        "creation_date": "🗓️ تاريخ الإنشاء",
        "session_age_detail": "{days} يوم و {hours} ساعة",
        "bulk_photo_button": "🖼️ تغيير الصورة جماعي",
"enter_bulk_photo": "🖼️ يرجى إرسال الصورة الجديدة التي سيتم تطبيقها على كل الحسابات.",
"bulk_reset_sessions_button": "🛡️ حذف الجلسات الأخرى",
"confirm_bulk_reset_sessions": "⚠️ **تأكيد** ⚠️\nأنت على وشك إنهاء جميع الجلسات الأخرى (باستثناء جلسة البوت) لـ **{count}** حساب. هل أنت متأكد؟",
        "last_activity": "⚡ آخر نشاط",
"relogin_button_account_menu": "🔑 إعادة تسجيل الدخول",
        "delete_other_sessions_button": "🗑️ حذف جميع الجلسات الأخرى",
        "tfa_checking_status": "⏳ جاري التحقق من حالة التحقق بخطوتين (2FA)...",
        "tfa_account_protected": "🔐 الحساب محمي بالفعل بكلمة مرور.\nللتغيير، يرجى إرسال كلمة المرور **الحالية**.\n\nلإلغاء العملية، أرسل /cancel",
        "tfa_account_not_protected": "🔓 الحساب غير محمي.\nلتفعيل الحماية، يرجى إرسال كلمة مرور **جديدة** لتعيينها.\n\nلإلغاء العملية، أرسل /cancel",
        "tfa_enter_current_password": "🔑 حسناً، الآن أرسل كلمة المرور **الجديدة**.",
        "tfa_changing_password": "⏳ جاري تغيير كلمة المرور...",
        "tfa_password_change_success": "✅ تم تغيير كلمة مرور التحقق بخطوتين بنجاح.",
        "tfa_invalid_current_password": "❌ كلمة المرور الحالية غير صحيحة. تم إلغاء العملية.",
        "tfa_fatal_error": "❌ خطأ فادح: {error}",
        "tfa_enter_new_password": "💡 حسناً. الآن أرسل **تلميحاً (hint)** لكلمة المرور (اختياري، يمكنك إرسال /skip للتخطي).",
        "tfa_hint_skipped": "👍 تم تخطي التلميح. الآن أرسل **بريداً إلكترونياً للاسترداد**.",
        "tfa_enter_recovery_email": "📧 ممتاز. الآن أرسل **بريداً إلكترونياً للاسترداد**. هذا مهم جداً لاستعادة حسابك.",
        "tfa_enabling_2fa": "⏳ جاري محاولة تفعيل التحقق بخطوتين...",
        "tfa_email_unconfirmed": "✉️ أرسل تيليجرام كوداً إلى `{email}`. يرجى إرسال الكود هنا لإتمام العملية.",
        "tfa_confirming_code": "⏳ جاري تأكيد الكود وتفعيل الحماية...",
        "tfa_email_confirmed_success": "✅ تم تغيير كلمة مرور التحقق بخطوتين بنجاح.",
        "tfa_code_confirmation_failed": "❌ حدث خطأ أثناء تأكيد الكود: {error}",
        "autoreply_menu_title": "📨 **إدارة الردود الآلية للحساب `{phone}`**\n\n",
        "add_new_reply_button": "➕ إضافة رد جديد",
        "no_auto_replies": "لا توجد ردود آلية مضافة حالياً.",
        "replies_list": "قائمة الردود المسجلة:",
        "delete_button": "🗑️ حذف",
        "bulk_add_contacts_button": "➕ إضافة جهات اتصال",
"bulk_delete_contacts_button": "🗑️ حذف كل جهات الاتصال",
"export_contacts_button": "📄 تصدير جهات الاتصال",
# السطر القديم: "enter_contacts_to_add": "..."
# السطر الجديد:
"enter_contacts_to_add": "✍️ أرسل قائمة بأرقام الهواتف أو أسماء المستخدمين (بينها مسافة أو سطر جديد)، **أو أرسل ملف .txt يحتوي عليها**.",
"restart_bot_button": "🔄 إعادة تشغيل البوت",
"cancel_all_tasks_button": "🛑 إلغاء كل المهام النشطة",
"confirm_restart_prompt": "⚠️ **تأكيد إعادة التشغيل** ⚠️\nهل أنت متأكد من أنك تريد إعادة تشغيل البوت؟ سيتم إيقاف كل العمليات الحالية.",
"confirm_cancel_all_tasks_prompt": "⚠️ **تأكيد الإلغاء** ⚠️\nهل أنت متأكد من أنك تريد إلغاء **جميع** المهام المجدولة؟",
"bot_restarting_message": "✅ جارٍ إعادة تشغيل البوت الآن...",
"all_tasks_cancelled_message": "✅ تم إلغاء جميع المهام المجدولة بنجاح.",
"add_from_file_button": "➕ إضافة من ملف",
"confirm_bulk_delete_contacts": "⚠️ **تحذير خطير** ⚠️\nأنت على وشك **حذف جميع جهات الاتصال** من **{count}** حساب محدد. هذا الإجراء لا يمكن التراجع عنه. هل أنت متأكد؟",

"export_contacts_caption": "✅ تم تصدير جهات اتصال {count} حساب بنجاح.",
        "enter_keyword": "✍️ يرجى إرسال **الكلمة المفتاحية** التي سيتم الرد عليها (غير حساسة لحالة الأحرف).",
        "enter_response_message": "💬 حسناً، الآن أرسل **رسالة الرد** التي سيتم إرسالها عند العثور على الكلمة المفتاحية.",
        "autoreply_add_success": "✅ تم إضافة الرد الآلي بنجاح.",
        "autoreply_already_exists": "⚠️ هذا الرد موجود بالفعل لهذا الحساب.",
        "autoreply_deleted": "✅ تم حذف الرد الآلي.",
        "manage_proxies_title": "🌐 **إدارة البروكسيات** 🌐\n\n",
        "no_proxies_added": "لا توجد بروكسيات مضافة حالياً.",
        "available_proxies_list": "قائمة البروكسيات المتاحة:",
        "assign_proxy_to_account": "اختر بروكسي لربطه بالحساب `{phone}` أو قم بإلغاء الربط.",
        "unassign_proxy_button": "🚫 إلغاء ربط البروكسي",
        "add_new_proxy_button": "➕ إضافة بروكسي جديد",
        "proxy_input_instructions": "يرجى إرسال البروكسي بالصيغة:\n`protocol://user:pass@host:port`\nأو\n`protocol://host:port`\n\nالبروتوكولات المدعومة: `http`, `socks4`, `socks5`",
        "proxy_add_success": "تمت إضافة البروكسي بنجاح.",
        "proxy_already_exists": "هذا البروكسي موجود بالفعل.",
        "proxy_invalid_format": "صيغة البروكسي غير صحيحة.",
        "proxy_not_found": "❌ لم يتم العثور على البروكسي.",
        "proxy_details_title": "**تفاصيل البروكسي 🆔 {id}**\n\n",
        "proxy_usage": "**الاستخدام:** مرتبط بـ `{count}` حساب.\n",
        "proxy_deleted": "✅ تم حذف البروكسي وفك ارتباطه بالحسابات.",
        "proxy_assign_success": "✅ تم تحديث ربط البروكسي بنجاح.",
        "error_account_not_selected": "❌ خطأ، لم يتم تحديد الحساب.",
        "select_accounts_for_task": "**مهمة جماعية: {action_title}**\n\nالرجاء تحديد الحسابات التي ستنفذ المهمة:",
        "select_all_button": "✅ تحديد الكل",
        "invert_selection_button": "🔄 عكس التحديد",
        "clear_selection_button": "🗑️ مسح الكل",
        "continue_button": "🚀 متابعة ({count})",
        "cancel_and_return_button": "🏠 إلغاء والرجوع",
        "no_accounts_selected_cancel": "❌ لم تختر أي حسابات. تم إلغاء العملية.",
        "enter_group_link": "🔗 يرجى إرسال رابط القناة أو المجموعة (عامة أو خاصة).",
        "warning_bulk_delete": "‼️ **تحذير خطير** ‼️\nأنت على وشك **'{delete_type_text}'** لـ **{count}** حساب.",
        "warning_bulk_logout": "⚠️ **تأكيد** ⚠️\nأنت على وشك تسجيل الخروج من **{count}** حساب. ستحتاج إلى إعادة تسجيل الدخول إليها لاحقاً.",
        "yes_im_sure": "✅ نعم، أنا متأكد",
        "starting_bulk_task": "⏳ **بدء تنفيذ مهمة '{action_type}' على {count} حساب...**",
        "bulk_task_report_header": "📋 **تقرير مهمة '{action_type}' للرابط: {link}**\n",
        "bulk_task_report_header_no_link": "📋 **تقرير مهمة '{action_type}'**\n",
        "task_success": "نجح",
        "account_already_member": "الحساب عضو بالفعل",
        "account_not_member": "الحساب ليس عضواً",
        "task_failure": "فشل - {error}",
        "session_age_full_detail": "{d}ي و{h}س و{m}د و{s}ث",
        "task_completed_summary": "\n**انتهت المهمة.**\n- **نجاح:** {success_count}\n- **فشل/تحذير:** {failure_count}",
        "deleting_account_type_full": "حذف مع تسجيل الخروج",
        "deleting_account_type_local": "حذف من البوت فقط",
        "deleting_account_progress": "⏳ جاري حذف الحساب `{phone}`...",
        "delete_step_logout": "**الخطوة 1/2:** تسجيل الخروج من الجلسة.",
        "delete_step_local_data": "**الخطوة 2/2:** حذف البيانات المحلية.",
        "delete_success": "✅ تم حذف الحساب بنجاح.",
        "logout_success": "تم تسجيل الخروج",
        "already_logged_out": "الحساب غير مسجل دخول بالفعل",
        "scraper_options_title": "⚙️ **خيارات الاستخراج**\n\nأي نوع من الأعضاء تريد استخراجه؟",
        "all_members": "👥 كافة الأعضاء",
        "recent_active_members": "⚡️ الأعضاء النشطون مؤخراً",
        "enter_scraper_limit": "🔢 ما هو عدد الأعضاء الذي تريد استخراجه؟\nأرسل '0' لاستخراج الجميع (قد يكون بطيئاً للمجموعات الكبيرة).",
        "invalid_number_input": "❌ يرجى إرسال رقم صحيح (0 أو أكبر).",
        "enter_group_link_scraper": "🔗 حسناً، الآن أرسل رابط المجموعة المراد استخراج أعضائها.",
        "extracting_members_from": "⏳ جاري استخراج الأعضاء من {link} باستخدام الحساب {phone}...",
        "scraper_account_needs_login": "الحساب المحدد للاستخراج يحتاج لتسجيل دخول",
        "extracting_progress": "⏳ تم استخراج {count} عضو حتى الآن...",
        "no_members_found": "ℹ️ لم يتم العثور على أعضاء أو لا يمكن الوصول للمجموعة.",
        "extraction_success_caption": "✅ تم استخراج {count} عضو بنجاح.",
        "extraction_failed": "❌ فشل استخراج الأعضاء: {error}",
        "exporting_sessions_start": "⏳ **بدء تصدير {count} جلسة...**",
        "exporting_sessions_in_progress": "**🔑 جارٍ تصدير الجلسات...**",
        "export_success_summary": "✅ اكتمل التصدير!\n\n- نجاح: {success_count}\n- فشل: {failure_count}",
        "no_sessions_exported": "ℹ️ لم يتم تصدير أي جلسات.",
        "security_warning_export_sessions": "⚠️ **تحذير أمني** ⚠️\nأنت على وشك تصدير **{count}** جلسة نصية.\nالجلسات النصية حساسة جداً ويمكن استخدامها للوصول الكامل لحساباتك. لا تشاركها مع أي شخص.\n\nهل تريد المتابعة؟",
        "choose_delete_method": "**اختر طريقة الحذف الجماعي:**\n\n**- حذف مع تسجيل الخروج:** إنهاء الجلسات من سيرفرات تيليجرام وحذف الحسابات من البوت. (آمن وموصى به)\n**- حذف من البوت فقط:** حذف الحسابات من قائمة البوت فقط وترك الجلسات نشطة في تيليجرام.",
        "confirm_delete_full_logout": "🗑️ حذف مع تسجيل الخروج",
        "confirm_delete_local_only": "🔪 حذف من البوت فقط",
        "cleaning_accounts_bulk": "**🧹 منظف الحسابات الجماعي ({count} حساب)**\n\nاختر مهمة التنظيف. هذا الإجراء نهائي ولا يمكن التراجع عنه.",
        "confirm_bulk_cleaner": "**‼️ تأكيد نهائي ‼️**\n\nهل أنت متأكد من تنفيذ مهمة **'{action_text}'** على كل الحسابات المحددة؟",
        "starting_bulk_cleaner": "⏳ **بدء التنظيف الجماعي (`{clean_type}`) على {count} حساب...**\nالعملية قد تستغرق وقتاً طويلاً.",
        "working_on_account": "⏳ **يعمل على الحساب {current}/{total} (`{phone}`)**",
        "bulk_cleaner_report_header": "**📋 تقرير منظف الحسابات الجماعي (`{clean_type}`)**\n",
        "bulk_cleaner_success": "✅ `{phone}`: تم بنجاح ({details})",
        "export_csv_preparing": "⏳ جاري تجهيز الملف...",
        "no_accounts_to_export": "❌ لا توجد حسابات لديك لتصديرها.",
        "export_csv_success": "✅ تم تصدير بيانات {count} حساب بنجاح.",
        "scheduled_tasks_menu_title": "⏰ **المهام المجدولة** ⏰\n\n",
        "add_new_task_button": "➕ إضافة مهمة جديدة",
        "no_scheduled_tasks": "لا توجد مهام مجدولة حالياً.",
        "task_join": "انضمام",
        "task_message": "رسالة",
        "task_check": "فحص",
        "task_next_run": "تالي:",
        "task_pause_button": "⏸️",
        "task_resume_button": "▶️",
        "task_delete_button": "🗑️",
        "choose_task_type": "1️⃣ اختر نوع المهمة المجدولة:",
        "task_type_join": "🚀 انضمام لقناة/مجموعة",
        "task_type_message": "✉️ إرسال رسالة مجدولة",
        "task_type_check": "✔️ فحص تلقائي للحسابات",
        "select_task_accounts": "2️⃣ الرجاء تحديد الحسابات التي ستنفذ المهمة:",
        "enter_task_target": "3️⃣ أرسل رابط القناة/المجموعة العامة أو الخاصة.",
        "enter_message_target": "3️⃣ أرسل معرف/رابط القناة أو المستخدم الذي سترسل له الرسالة.",
        "enter_message_content": "4️⃣ الآن أرسل محتوى الرسالة التي تريد جدولتها.",
        "enter_cron_schedule": "5️⃣ أخيراً، أرسل توقيت المهمة بصيغة Cron.\n\n{cron_examples}",
        "cron_examples": "**أمثلة على صيغة Cron:**\n- `* * * * *` (كل دقيقة)\n- `0 * * * *` (كل ساعة على رأس الساعة)\n- `0 8 * * 5` (كل يوم جمعة الساعة 8:00 صباحاً)\nالصيغة: `دقيقة ساعة يوم شهر يوم_بالأسبوع`",
        "invalid_cron_format": "❌ صيغة Cron غير صالحة، يرجى المحاولة مجدداً.",
        "task_scheduled_success": "✅ تم جدولة المهمة بنجاح.\nوقت التشغيل التالي: {next_run_time}",
        "task_scheduling_failed": "❌ فشلت إضافة المهمة للجدولة: {error}",
        "task_not_found": "❌ لم يتم العثور على المهمة، ربما تم حذفها.",
        "task_deleted": "✅ تم حذف المهمة المجدولة.",
        "task_paused": "⏸️ تم إيقاف المهمة مؤقتاً.",
        "task_resumed": "▶️ تم استئناف المهمة.",
        "admin_panel_title": "👑 **لوحة تحكم الأدمن** 👑\n\nاختر أحد الإجراءات:",
        "add_subscription_button": "➕ تفعيل اشتراك",
        "remove_subscription_button": "➖ إلغاء تفعيل اشتراك",
        "view_subscribers_button": "👥 عرض المشتركين",
        "custom_broadcast_button": "📢 إذاعة رسالة (مخصصة)",
        "monitor_resources_button": "📊 مراقبة الموارد",
        "backup_db_button": "💾 نسخ احتياطي",
        "restore_db_button": "🔄 استعادة",
        "no_subscribers": "ℹ️ لا يوجد أي مشتركين حالياً.",
        "subscribers_list_title": "👥 **قائمة المشتركين**\n\nاضغط على مشترك لعرض تفاصيله:\n",
        "subscriber_info_card_title": "💳 **بطاقة معلومات المشترك**\n\n",
        "subscriber_name": "👤 **الاسم:** {name}",
        "story_ask_privacy": "🔒 من يمكنه رؤية هذه القصة؟",
"privacy_all": "👤 الجميع",
"privacy_contacts": "👥 جهات الاتصال فقط",
"story_ask_period": "⏳ كم مدة بقاء القصة؟",
"period_6h": "6 ساعات",
"period_12h": "12 ساعة",
"period_24h": "24 ساعة",
"period_48h": "48 ساعة",
"bulk_bio_button": "✍️ تغيير البايو جماعي",
"enter_bulk_bio": "✍️ يرجى إرسال النبذة التعريفية (البايو) الجديدة التي سيتم تطبيقها على كل الحسابات المحددة.",
"story_post_another_button": "➕ نشر قصة أخرى",
"back_to_stories_menu_button": "📖 قائمة القصص",
"story_final_status": "✅ تم تنفيذ طلب نشر القصة بنجاح!\n\n**الحالة:** {status}",
        "subscriber_id": "🆔 **ID:** `{id}`",
        "subscription_period": "📅 **الاشتراك:** من `{start_date}` إلى `{end_date}`",
        "current_accounts_count": "💼 **عدد الحسابات الحالي:** `{count}`",
        "last_account_add": "➕ **آخر إضافة حساب:** `{date}`",
        "monitoring_title": "📊 **مراقبة موارد النظام**\n\n",
        "psutil_not_installed": "❌ **خطأ:** مكتبة `psutil` غير مثبتة.\n",
        "cpu_usage": "💻 **استهلاك المعالج (CPU):** `{percent}%`",
        # السطر القديم
"ram_usage": "🧠 **استهلاك الذاكرة (RAM):** `{percent}%` ({used:.1f}MB / {total:.1f}MB)",
# السطر الجديد (بدون .1f)
"ram_usage": "🧠 **استهلاك الذاكرة (RAM):** `{percent}%` ({used} / {total})",
        "active_scheduled_tasks": "⏰ **المهام المجدولة:** `{count}` مهمة نشطة",
        "backup_preparing": "⏳ جاري إنشاء نسخة احتياطية...",
        "backup_success": "✅ تم إنشاء نسخة احتياطية من قاعدة البيانات بنجاح.",
        "backup_failed": "❌ فشل إنشاء نسخة احتياطية: {error}",
        "restore_warning": "⚠️ **تحذير خطير:**\nأنت على وشك استبدال قاعدة البيانات الحالية. سيتم حذف جميع البيانات الحالية.\n\nالرجاء إرسال ملف النسخة الاحتياطية (`.db`) للمتابعة.",
        "invalid_db_file": "❌ الملف غير صالح. أرسل ملف قاعدة بيانات بامتداد `.db`.",
        "restore_in_progress": "⏳ تم استلام الملف، جاري الاستعادة...",
        "restore_success_restart": "✅ **تمت استعادة قاعدة البيانات بنجاح.**\n\n**‼️ هام جداً: ‼️**\nيجب عليك **إعادة تشغيل البوت يدوياً الآن** لتطبيق التغييرات وتجنب أي مشاكل.",
        "enter_user_id_for_sub": "📝 يرجى إرسال **ID** المستخدم الذي تريد تفعيل الاشتراك له.",
        "invalid_id_input": "❌ الإدخال غير صالح. يرجى إرسال ID رقمي صحيح.",
        "enter_sub_days": "🗓️ حسناً، الآن أرسل **عدد أيام** الاشتراك (مثال: 30).",
        "sub_activation_success": "✅ تم تفعيل الاشتراك للمستخدم `{target_user_id}` لمدة `{days}` يوم.\nينتهي في: `{end_date}`",
        "sub_activation_notification_to_user": "🎉 تم تفعيل/تجديد اشتراكك في البوت!\n\n⏳ **مدة الاشتراك:** {days} أيام\n⌛ **ينتهي:** {end_date}\n\nشكراً لاستخدامك البوت! ✨",
        "failed_to_notify_user": "⚠️ لم أتمكن من إرسال رسالة للمستخدم. الخطأ: {error}",
        "invalid_days_input": "❌ الإدخال غير صالح. يرجى إرسال عدد أيام رقمي صحيح.",
        "choose_user_to_deactivate_sub": "اختر المستخدم لإلغاء اشتراكه:",
        "sub_deactivation_success": "✅ تم إلغاء اشتراك المستخدم `{user_id}` بنجاح.",
        "sub_deactivation_notification_to_user": "ℹ️ نأسف لإعلامك، لقد تم إلغاء اشتراكك في البوت.",
        "sub_not_found_to_deactivate": "❌ لم يتم العثور على المستخدم لإلغاء اشتراكه.",
        "broadcast_menu_title": "**إذاعة مخصصة**\n\nاختر الفئة التي تريد إرسال الرسالة إليها:",
        "broadcast_to_all": "📢 للكل",
        "broadcast_by_sub_date": "📅 حسب تاريخ الاشتراك",
        "broadcast_by_accounts_count": "💼 حسب عدد الحسابات",
        "broadcast_to_specific_ids": "🆔 لمستخدمين محددين",
        "enter_date_range": "يرجى إرسال تاريخ البدء والانتهاء، مفصولين بـ |.\nالصيغة: `YYYY-MM-DD | YYYY-MM-DD`",
        "invalid_date_format": "❌ صيغة التاريخ خاطئة.",
        "enter_account_count_range": "يرجى إرسال أقل وأقصى عدد للحسابات، مفصولين بـ |.\nمثال: `0 | 5` (للمستخدمين الذين لديهم من 0 إلى 5 حسابات)",
        "invalid_number_range_format": "❌ صيغة الأرقام خاطئة.",
        "enter_user_ids": "يرجى إرسال IDs المستخدمين، مفصولين بمسافة أو سطر جديد.",
        "no_users_match_criteria": "❌ لم يتم العثور على أي مستخدمين يطابقون هذه المعايير.",
        # السطر القديم: "users_selected_prompt_message": "تم تحديد `{count}` مستخدم.\n\nالآن، أرسل الرسالة التي تود إذاعتها..."
# السطر الجديد:
"users_selected_prompt_message": "✅ تم تحديد `{count}` مستخدم.\n\nالآن، قم **بإعادة توجيه (Forward)** الرسالة التي تود إذاعتها إلى هنا.",
"manage_contacts_button": "📇 إدارة جهات الاتصال",
"single_contact_menu_title": "📇 **إدارة جهات اتصال الحساب {phone}**",
"add_contacts_single_button": "➕ إضافة جهات اتصال",
"delete_all_contacts_single_button": "🗑️ حذف كل جهات الاتصال",
# السطر القديم
"disk_usage": "💾 استخدام القرص",
# السطر الجديد (أكثر تفصيلاً)
"disk_usage": "💾 **استخدام القرص:** `{percent}%` ({used} / {total})",
"total_accounts": "إجمالي الحسابات",
"active_clients_in_pool": "الجلسات النشطة بالذاكرة",
"system_uptime": "⏱️ مدة تشغيل النظام",
"cpu_details": "⚙️ المعالج",
"cpu_cores": "{physical} أنوية فعلية / {logical} وهمية",
"uptime_format": "{days} أيام, {hours:02}:{minutes:02}:{seconds:02}",
"export_contacts_single_button": "📄 تصدير جهات الاتصال",
"confirm_delete_all_contacts": "⚠️ **تأكيد** ⚠️\nهل أنت متأكد من حذف **جميع** جهات الاتصال من الحساب `{phone}`؟ لا يمكن التراجع عن هذا الإجراء.",
        # السطر القديم: "confirm_broadcast": "هل أنت متأكد من أنك تريد إرسال هذه الرسالة...معاينة:..."
# السطر الجديد:
"confirm_broadcast": "هل أنت متأكد من أنك تريد إذاعة الرسالة التي قمت بإعادة توجيهها إلى **{count}** مشترك؟",
        "yes_send_now_button": "✅ نعم، أرسل الآن ({count})",
        "broadcast_error_no_data": "❌ خطأ: لم يتم العثور على رسالة أو مستهدفين. تم الإلغاء.",
        "broadcast_sending": "⏳ جاري إرسال الإذاعة...",
        "broadcast_sending_progress": "**📢 جارٍ الإرسال...**",
        "broadcast_completed": "✅ **اكتملت الإذاعة**\n\n- تم الإرسال بنجاح إلى: {success_count}\n- فشل الإرسال إلى: {fail_count}",
        "daily_admin_alerts": "**⚠️ تنبيهات يومية للأدمن ⚠️**\n\n",
        "expiring_soon_subscriptions": "**الاشتراكات التي ستنتهي قريباً:**\n",
        "user_account_needs_login_notification_title": "🚨 **تنبيه: حسابات تحتاج تسجيل دخول!** 🚨",
        "user_account_needs_login_notification_body": "يا {user_mention}،\n\nلدينا بعض الحسابات الخاصة بك التي تحتاج إلى إعادة تسجيل دخول لتستمر في العمل بشكل صحيح:\n",
        "account_needs_login_list_item": "- `{phone}`",
        "relogin_instructions": "\nيرجى الذهاب إلى **إدارة حساباتك** ثم اختيار الحساب المعني وتسجيل الدخول مرة أخرى.",
        "bot_restarted_message": "تم إعادة تشغيل البوت بنجاح!",
        "next": "التالي",
        "previous": "السابق",
        "unknown_name": "غير محدد",
        "not_available": "لا يوجد",
        "not_specified": "غير محدد",
"email_check_report_title": "📊 **تقرير فحص إيميل الاستيراد** 📊",
        "email_check_status_label": "الحالة:",
        "email_check_used_by_label": "يستخدم كبريد استرداد لـ:",
        "email_check_no_accounts_found": "لا يوجد حسابات تستخدم هذا الإيميل كبريد استرداد.",
        "email_check_account_list_item": "  - `{phone}` ({name})",
        "back_to_email_management_button": "🔙 رجوع لإدارة الإيميلات",
        "session_file_add_method": "ملف جلسة",
"relogin_success": "✅ تم إعادة تسجيل الدخول بنجاح للحساب: `{phone}`",
"relogin_flow_new_account_added": "✅ تم تسجيل الدخول بنجاح للحساب الجديد: `{new_phone}`.\n\n⚠️ لكن الحساب `{old_phone}` ما زال بحاجة لإعادة تسجيل الدخول.",
        "add_account": "إضافة حساب",
        "add_via_session_file_success": "تمت الإضافة بنجاح عبر ملف جلسة.",
        "phone_number_add_method": "رقم الهاتف",
        "string_session_add_method": "جلسة نصية",
        "add_via_string_session_success": "تمت الإضافة بنجاح عبر جلسة نصية.",
        "success": "نجح",
        "failed": "فشل",
        "error": "خطأ",
        "security_alert": "تنبيه أمني",
        "new_login_from": "تسجيل دخول جديد من",
        "account_banned_alert": "تنبيه حظر",
        "update_data_log": "تحديث البيانات",
        "manual_update_requested": "تم طلب تحديث يدوي.",
        "getting_last_message": "⏳ جاري جلب آخر رسالة...",
        "no_messages_in_account": "ℹ️ لا توجد أي رسائل في هذا الحساب.",
        "last_message_header": "📥 **آخر رسالة في حساب `{phone}`**",
        "from": "من",
        "date": "التاريخ",
        # ... (الرسائل الموجودة لديك) ...
        "fetch_email_button": "📥 جلب آخر رسالة",
        "select_email_to_fetch": "اختر الإيميل الذي تريد جلب آخر رسالة منه:",
        "fetching_email": "⏳ جارٍ جلب آخر رسالة من {email_address}...",
        "email_fetch_success": "✅ آخر رسالة من {email_address}:\n\n**المرسل:** {from_}\n**الموضوع:** {subject}\n**التاريخ:** {date}\n\n**المحتوى (أول 500 حرف):**\n```\n{body}\n```",
        "email_fetch_no_messages": "ℹ️ لا توجد رسائل في صندوق الوارد لهذا الإيميل.",
        "email_fetch_failed": "❌ فشل جلب الرسالة: {error}",
        "decryption_failed": "❌ فشل فك ترميز كلمة المرور. (ملاحظة: هذا ليس تشفيراً آمناً، مجرد ترميز).",
        # ... (بقية الرسائل الموجودة لديك) ...

        "content": "المحتوى",
        "message_no_text": "[رسالة بدون نص]",
        "get_last_message_log": "جلب آخر رسالة",
        "deleting_sessions": "⏳ جاري حذف الجلسات...",
        "delete_sessions_log": "حذف الجلسات",
        "all_other_sessions_deleted": "تم حذف جميع الجلسات الأخرى.",
        "logout_account_log": "تسجيل الخروج",
        "logout_success_update_list": "✅ تم تسجيل الخروج بنجاح. سيتم الآن تحديث القائمة.",
        "logout_confirmation_message": "⚠️ **تأكيد تسجيل الخروج** ⚠️\nهل أنت متأكد من أنك تريد تسجيل الخروج من الحساب `{phone}`؟ ستحتاج إلى إعادة تسجيل الدخول لاحقاً.",
        "yes_logout_now": "‼️ نعم، قم بتسجيل الخروج",
        "end_session_full_delete": "إنهاء الجلسة عند الحذف الكامل",
        "warning_logout_failed_continue_local_delete": "⚠️ تحذير: لم نتمكن من تسجيل الخروج ({error}). سنستمر بالحذف المحلي.",
        "change_name_log": "تغيير الاسم",
        "to": "إلى",
        "change_bio_log": "تغيير النبذة",
        "change_username_log": "تغيير اليوزر",
        "change_photo_log": "تغيير الصورة",
        "new_photo_uploaded": "تم رفع صورة جديدة بنجاح.",
        "details": "التفاصيل",
        "single_cleaner_log": "منظف فردي",
        "deleted": "تم حذف",
        "contacts": "جهة اتصال",
        "change_2fa_log": "تغيير 2FA",
        "password_change_success_log": "تم تغيير كلمة المرور بنجاح.",
        "enable_2fa_log": "تفعيل 2FA",
        "protection_enabled_success_log": "تم تفعيل الحماية بنجاح.",
        "waiting_email_code_log": "ينتظر كود تأكيد البريد.",
        "email_confirmed_protection_enabled_log": "تم تأكيد البريد وتفعيل الحماية.",
        "failed_code_confirmation": "فشل تأكيد الكود",
        "auto_reply": "رد آلي",
        "replied_to": "رد على",
"tfa_select_email_title": "✉️ اختر بريد استرداد من قائمتك المحفوظة:",
"tfa_no_import_emails_error": "❌ ليس لديك أي إيميلات محفوظة في قسم 'إدارة إيميلات الاستيراد'.\n\nيرجى إضافة إيميل واحد على الأقل من القائمة الرئيسية أولاً.",
        "for_user": "للمستخدم",
        "bulk_name_button": "📝 تغيير الاسم جماعي",
"enter_bulk_name": "📝 يرجى إرسال الاسم الجديد. لإضافة اسم أخير، استخدم الصيغة: `الاسم الأول | الاسم الأخير`",
        "add_autoreply_log": "إضافة رد آلي",
        "keyword": "الكلمة",
        "back_to_proxies_list": "🔙 رجوع لقائمة البروكسيات",
        "back_to_subscribers_list": "🔙 رجوع لقائمة المشتركين",
        "are_you_sure_to_proceed": "هل أنت متأكد من المتابعة؟",
        "bulk_join_log": "انضمام جماعي",
        "success_in_joining": "نجح في الانضمام إلى",
        "bulk_leave_log": "مغادرة جماعية",
        "success_in_leaving": "نجح في المغادرة من",
        "bulk_task": "مهمة جماعية",
        "for_link": "للرابط",
        "session_24h_mark": "عمر الجلسة 24 ساعة:",
"time_left": "الوقت المتبقي:",
        "start_member_extraction_log": "بدء استخراج أعضاء",
        "success_member_extraction_log": "نجاح استخراج أعضاء",
        "extracted": "تم استخراج",
        "failed_member_extraction_log": "فشل استخراج أعضاء",
        "bulk_export_session_log": "تصدير جلسة جماعي",
        "bulk_cleaner_log": "منظف جماعي",
        "no_change": "لا تغيير",
        "accounts_count": "حساب",
        "bulk_post_story_button": "📖 نشر قصص جماعي",
        "scheduled_task_report_header": "**تقرير المهمة المجدولة `{job_id}`**",
        "scheduled_task": "مهمة مجدولة",
        "target": "الهدف",
        "loading_scheduled_tasks": "تحميل المهام المجدولة والذكية من قاعدة البيانات...",
"session_key_duplicated_error": "❌ خطأ فادح: تم إبطال هذه الجلسة من قبل تيليجرام لأنه تم استخدامها من مكانين في نفس الوقت. الرجاء إنشاء جلسة جديدة والتأكد من إيقاف أي برامج أخرى تستخدمها قبل إرسالها.",
        "failed_to_load_scheduled_task": "فشل تحميل المهمة المجدولة {job_id}: {error}",
        "loaded_scheduled_tasks_count": "تم تحميل {count} مهمة مجدولة.",
        "scheduled_daily_smart_notifications": "تمت جدولة مهمة الإشعارات الذكية اليومية.",
        "failed_to_schedule_smart_notifications": "فشل جدولة مهمة الإشعارات الذكية: {error}",
        "scheduled_client_pool_cleanup": "تمت جدولة مهمة تنظيف تجمع العملاء.",
        "failed_to_schedule_client_pool_cleanup": "فشل جدولة مهمة تنظيف تجمع العملاء: {error}",
        "auto_reply_listeners_info": "Auto-reply listeners will be started on demand (not at startup).",
        "failed_to_send_admin_notification": "فشل إرسال إشعار للأدمن {admin_id}: {error}",
        "unknown": "غير معروف",
        "expires": "ينتهي",
        "expires_on": "ينتهي في",
        "total_proxies": "إجمالي البروكسيات",
        "management_options_title": "اختر نوع الإدارة:",
"single_management_button": "👤 إدارة فردية",
"bulk_management_button": "👥 إدارة جماعية",
"bulk_actions_menu_title": "اختر المهمة الجماعية التي تريد تنفيذها على الحسابات المحددة:",
        "used_proxies": "المستخدم منها",
        "active_sessions_header": "🔒 **الجلسات النشطة للحساب** `{phone} ({account_name})`:",
        "error_getting_sessions": "❌ خطأ في جلب الجلسات: {error}",
        "not_subscribed": "❌ أنت غير مشترك في البوت.",
        "subscription_active": "✅ اشتراكك فعال وينتهي في {end_date}.",
        "subscription_expired": "❌ اشتراكك منتهي.",
        "no_accounts_registered": "❌ لا توجد أي حسابات مسجلة باسمك.",
        "choose_language_prompt": "الرجاء اختيار اللغة:",
        "subscriber_not_found": "❌ لم يتم العثور على المشترك.",
        "before": "قبل {age}",
        "login_success_code": "نجاح تسجيل الدخول (كود)",
        "login_success_password": "نجاح تسجيل الدخول (كلمة مرور)",
        "failed_needs_login": "فشل - يحتاج تسجيل دخول",
        "cleaner_delete_deleted_contacts_log": "منظف - حذف جهات الاتصال المحذوفة",
        "delete_proxy_button": "🗑️ حذف البروكسي",
"manage_stories_button": "📖 إدارة القصص",
        "story_menu_title": "📖 **إدارة قصص الحساب `{phone}`**",
        "story_post_now_button": "🚀 نشر قصة الآن",
        "story_schedule_button": "⏰ جدولة قصة",
        "story_view_active_button": "👀 عرض القصص النشطة",
        "story_delete_button": "🗑️ حذف قصة",
        "story_under_development": "⚠️ هذه الميزة قيد التطوير حالياً.",
        "story_send_file_prompt": "🖼️ يرجى إرسال **الصورة** أو **الفيديو** لنشرها كقصة.",
        "story_send_caption_prompt": "✍️ ممتاز. الآن أرسل **النص المرافق** للقصة.\n\nيمكنك إرسال /skip لتجاوز إضافة النص.",
        "story_posting_now": "⏳ جاري نشر القصة، يرجى الانتظار...",
        "story_post_success": "✅ تم نشر القصة بنجاح!",
        "story_post_failed": "❌ فشل نشر القصة: {error}",
"back_to_email_selection_button": "🔙 رجوع لاختيار إيميل",
        "task_story": "قصة مجدولة",
"email_add_failed_credentials": "❌ فشل التحقق. كلمة المرور أو الإيميل غير صحيح. لم يتم إضافة الإيميل.",
        "bulk_task_final_report": "✅ اكتملت مهمة '{action_title}'.\n\n- **نجاح:** {success_count}\n- **فشل/تحذير:** {failure_count}",
"back_to_bulk_menu": "🔙 رجوع لقائمة الإدارة الجماعية",
    },
    'en': {
        "welcome_message": "👋 Welcome {user_mention} to **Emperor Bot (v9.5)**.\n\nPlease choose an option from the menu to get started.",
        "choose_language": "Please choose your language:",
        "language_set_success": "✅ Language set to English.",
        "language_set_fail": "❌ Error setting language.",
        "not_authorized": "⛔️ Sorry, this bot is only available for subscribed users.\n\nYou might not be subscribed or your subscription has expired!",
        "check_sub_status_button": "💳 Check Subscription Status",
        "contact_dev_button": "🧑‍💻 Contact Developer",
        "main_menu_return": "🏠 Returned to main menu.",
        "bulk_photo_button": "🖼️ Bulk Photo Change",
"enter_bulk_photo": "🖼️ Please send the new photo that will be applied to all accounts.",
"bulk_reset_sessions_button": "🛡️ Reset Other Sessions",
"confirm_bulk_reset_sessions": "⚠️ **Confirmation** ⚠️\nYou are about to terminate all other active sessions (except for this bot's session) for **{count}** account(s). Are you sure?",
        "back_to_main_menu": "🏠 Back to Main Menu",
        "action_cancelled": "👍 Operation cancelled.",
        "no_accounts_to_check": "❌ No accounts to check.",
        "checking_accounts": "⏳ **Checking {count} account(s)...**\n\nThis operation may take some time.",
        "check_accounts_report_header": "📋 **Your Account Status Report:**\n",
        "check_accounts_summary_header": "**Summary:**",
        "status_active": "Active",
        "status_banned": "Banned",
        "status_needs_login": "Needs Login",
        "status_unknown": "Unknown",
        "check_account_quick_action": "Actions for {phone}",
        "delete_account_button": "🗑️ Delete Account",
        "ignore_button": "✖️ Ignore",
        "login_account_button": "🔑 Login",
        "add_account_instructions": "Please send:\n- **Phone number** with country code (e.g., `+123...`).\n- **Telethon session string**.\n- **Session file** with `.session` extension.",
        "go_back_button": "🔙 Back",
        "story_ask_privacy": "🔒 Who can see this story?",
"privacy_all": "👤 Everyone",
"privacy_contacts": "👥 Contacts Only",
"story_ask_period": "⏳ For how long should the story be visible?",
"period_6h": "6 Hours",
"period_12h": "12 Hours",
"period_24h": "24 Hours",
"period_48h": "48 Hours",
"session_24h_mark": "Session 24h Mark:",
"time_left": "Time Left:",
"story_post_another_button": "➕ Post Another Story",
"back_to_stories_menu_button": "📖 Stories Menu",
"story_final_status": "✅ Story posting request has been processed successfully!\n\n**Status:** {status}",
        "invalid_input_format": "❌ Invalid input format. Please send a valid phone number or session string.",
        "session_file_received": "⏳ Session file received, processing and verifying...",
        "invalid_session_file": "❌ Invalid file. Send a session file ending with `.session`.",
        "session_processing_failed": "❌ Failed to process session file.\n**Reason:** Session expired or invalid. Please create a new session.",
        "unexpected_error": "❌ An unexpected error occurred: {error}",
        "phone_code_sent": "✅ Code sent to your Telegram account, please send it here.",
        "flood_wait_error": "❌ You are temporarily flood-waited. Wait for {seconds} seconds.",
        "phone_banned_error": "❌ This number is banned by Telegram.",
        "account_banned_admin_alert": "⚠️ *Account Ban Alert* ⚠️\nAccount `{phone}` detected as banned during add attempt.",
        "string_session_checking": "⏳ Checking session string...",
        "string_session_invalid": "❌ Invalid or expired session string.",
        "string_session_success": "✅ Session verified and saved successfully for account: `{phone}`",
        "account_needs_password": "🔒 Account is protected by two-step verification password. Please send it.",
        "invalid_code": "❌ Invalid code. Please try again.",
        "login_success": "✅ Login successful for account: {first_name}",
        "invalid_password": "❌ Incorrect password. Try again.",
        "dashboard_title": "📊 **Your Dashboard** 📊",
        "loading_dashboard": "⏳ Loading Dashboard...",
        "account_stats_header": "👤 **Your Account Statistics:** (Total: `{total}`)",
        "proxy_stats_header": "🌐 **Proxy Statistics (Overall):**",
        "admin_stats_header": "👑 **Admin Statistics:**",
        "active_subs_count": "Active Subscribers: {active_subs}",
        "refresh_button": "🔄 Refresh",
        "add_account_button_main": "➕ Add Account",
        "remove_account_button_main": "➖ Remove Account",
        "manage_accounts_button_main": "👤 Manage Your Accounts",
        "scheduled_tasks_button_main": "⏰ Scheduled Tasks",
        "manage_proxies_button_main": "🌐 Manage Proxies",
        "check_accounts_button_main": "✔️ Check Your Accounts",
        "dashboard_button_main": "📊 Your Dashboard",
        "automation_section_button_main": "🤖 Automation Section 🤖",
        "extraction_section_button_main": "⚙️ Extraction Section",
        "export_csv_button_main": "📤 Export (CSV)",
        "bulk_export_button_main": "🔑 Bulk Session Extract",
        "contact_dev_button_main": "📞 Contact Developer",
"relogin_button_account_menu": "🔑 Relogin",
"tfa_select_email_title": "✉️ Select a recovery email from your saved list:",
"tfa_no_import_emails_error": "❌ You have no saved emails in the 'Manage Import Emails' section.\n\nPlease add at least one email from the main menu first.",
        "admin_panel_button_main": "👑 Bot Admin Panel",
"restart_bot_button": "🔄 Restart Bot",
"cancel_all_tasks_button": "🛑 Cancel All Active Tasks",
"confirm_restart_prompt": "⚠️ **Confirm Restart** ⚠️\nAre you sure you want to restart the bot? All current processes will be stopped.",
"confirm_cancel_all_tasks_prompt": "⚠️ **Confirm Cancellation** ⚠️\nAre you sure you want to cancel **all** scheduled tasks?",
"bot_restarting_message": "✅ The bot is restarting now...",
"all_tasks_cancelled_message": "✅ All scheduled tasks have been successfully cancelled.",
        "automation_menu_title": "🤖 Automation Section 🤖\n\nPlease select a task to perform it in bulk on your active accounts.",
        "join_bulk_button": "🚀 Bulk Join",
        "leave_bulk_button": "👋 Bulk Leave",
        "cleaner_button": "🧹 Account Cleaner",
        "logout_bulk_button": "↪️ Bulk Logout",
        "scraper_menu_title": "⚙️ Data Extraction Section ⚙️\n\nPlease choose a tool to extract information.",
        "extract_members_button": "👥 Extract Group Members",
        "account_management_title": "👤 **Manage Your Accounts** 👤\n\nPlease select an account from the list to view management options:",
        "error_account_not_found": "❌ Error: Account not found or you do not own it.",
        "proxy_not_set": "Not Set",
        "session_age_full_detail": "{d}d, {h}h, {m}m, {s}s",
        "last_check_not_available": "N/A",
        "bulk_add_contacts_button": "➕ Bulk Add Contacts",
"bulk_delete_contacts_button": "🗑️ Bulk Delete All Contacts",
"export_contacts_button": "📄 Export Contacts",
# السطر القديم: "enter_contacts_to_add": "..."
# السطر الجديد:
"enter_contacts_to_add": "✍️ Send a list of phone numbers or usernames (separated by space or new line), **or send a .txt file containing them**.",
"add_from_file_button": "➕ Add from File",
"confirm_bulk_delete_contacts": "⚠️ **Critical Warning** ⚠️\nYou are about to **delete all contacts** from **{count}** selected account(s). This action cannot be undone. Are you sure?",
"export_contacts_caption": "✅ Successfully exported contacts for {count} account(s).",
        "add_method_unknown": "Unknown",
        "account_details_header": "⚙️ **Account Management:** `{phone}`",
        "account_name": "Name:",
        "management_options_title": "Choose management type:",
"single_management_button": "👤 Single Management",
"bulk_management_button": "👥 Bulk Management",
"bulk_actions_menu_title": "Choose the bulk task you want to perform on the selected accounts:",
        "account_id": "UserName:",
        "account_status": "Status:",
        "account_last_check": "Last Check:",
        "bulk_proxy_assign_button": "🌐 Bulk Proxy Assign",
"select_proxy_for_bulk_assign": "Select the proxy you want to assign to the selected accounts:",
        "account_add_method": "Add Method:",
        "account_session_date": "Session Date:",
        "session_age": "Session Age:",
"account_already_exists_for_user": "⚠️ This number is already registered to your account. You can manage it from the 'Manage Your Accounts' section.",
        "account_proxy": "Proxy:",
        "update_data_button": "🔄 Update Data",
        "extract_session_button": "🔑 Extract Session",
        "change_name_button": "📝 Change Name",
        "change_bio_button": "✍️ Change Bio",
        "change_photo_button": "🖼️ Change Photo",
        "change_username_button": "🆔 Change Username",
        "manage_2fa_button": "🔐 Manage 2FA",
        "clean_account_button": "🧹 Clean Account",
        "auto_replies_button": "📨 Auto Replies",
        "active_sessions_button": "🛡️ Active Sessions",
        "get_last_message_button": "📥 Get Last Message",
        "assign_proxy_button": "🌐 Assign Proxy",
        "activity_log_button": "📜 Activity Log",
        "logout_account_button": "🚪 Logout Account",
        "delete_account_final_button": "🗑️ Wipe & Logout",
"email_check_report_title": "📊 **Import Email Check Report** 📊",
        "email_check_status_label": "Status:",
        "email_check_used_by_label": "Used as recovery email by:",
        "email_check_no_accounts_found": "No accounts currently use this email as a recovery email.",
        "email_check_account_list_item": "  - `{phone}` ({name})",
        "back_to_email_management_button": "🔙 Back to Email Management",
"manage_import_emails_button_main": "📧 Manage Import Emails",
"manage_emails_title": "📧 **Manage Import Emails** 📧\n\nThese emails are used to automatically fetch verification codes.",
"no_import_emails": "You haven't added any import emails yet.",
"add_email_button": "➕ Add New Email",
"email_status_checking": "⏳ Checking status...",
"email_status_ok": "✅ Working",
"email_status_fail": "❌ Login Failed",
"check_status_button": "🔬 Check",
"enter_gmail_address": "Please send the Gmail address.",
"enter_app_password": "Now, please send the 16-character **App Password** for this email.",
"email_added_success": "✅ Email added successfully.",
"email_already_exists": "⚠️ This email already exists.",
"email_deleted_success": "✅ Email deleted successfully.",
"invalid_email_format": "❌ Invalid email format.",
"bulk_2fa_button": "🔐 Bulk Set 2FA",
"bulk_2fa_menu_title": "🔐 **Bulk Set Two-Factor Authentication (2FA)**\n\nChoose the password setting method for the selected {count} accounts:",
"2fa_mode_unified_user": "🔑 Unified (I will provide it)",
"2fa_mode_random_unique": "🎲 Random (Unique per account)",
"2fa_mode_random_unified": "🎲 Unified (Random from bot)",
"enter_unified_2fa_pass": "Send the unified password you want to apply to all accounts.",
"bulk_2fa_report_title": "📋 **Bulk 2FA Setup Report**",
"bulk_2fa_starting": "⏳ **Starting 2FA setup process for {count} accounts...**\nThis might take a while, please wait.",
"bulk_2fa_no_emails_error": "❌ **Error:** You cannot proceed. You must add at least one import email from the main menu first.",
"2fa_set_success": "Success",
"2fa_set_fail": "Failure",
"2fa_pass_gen_and_saved": "Password generated and saved",
"2fa_email_verify_auto_attempt": "Attempting to fetch verification code from email automatically...",
"2fa_email_verify_auto_success": "Successfully fetched code and verified email!",
"2fa_email_verify_auto_fail": "Auto-fetch failed, please proceed manually.",
"yes_button": "✅ Yes",
"no_button": "❌ No",
        "extracting_session": "⏳ Extracting session...",
        "extract_session_failed_login_needed": "⚠️ Cannot extract session, account needs login.",
        "extract_session_failed_error": "❌ Error: {error}",
        "session_code_header": "🔑 **Session code for account `{phone}`:**\n\n`{session_string}`",
        "updating_account_data": "⏳ Updating account data for `{phone}`...",
        "account_needs_login_alert": "⚠️ Account needs login.",
        "enter_new_first_name": "📝 Please send the new first name. To add a last name, use the format: `First Name | Last Name`\n\nTo cancel, send /cancel",
        "enter_new_bio": "✍️ Please send the new bio (max 70 characters).\n\nTo cancel, send /cancel",
        "enter_new_username": "🆔 Please send the new username (without @).\n\nTo cancel, send /cancel",
        "bulk_post_story_button": "📖 Bulk Story Post",
        "send_new_photo": "🖼️ Please send the photo you want to set as profile picture.\n\nTo cancel, send /cancel",
        "updating_name": "⏳ Updating name...",
        "name_update_success": "✅ Name updated successfully.",
        "updating_bio": "⏳ Updating bio...",
        "bio_update_success": "✅ Bio updated successfully.",
        "updating_username": "⏳ Attempting to change username to @{username}...",
        "username_occupied": "❌ This username is already taken. Please choose another one.",
        "username_invalid": "❌ Invalid username format. Must be at least 5 characters long.",
        "username_update_success": "✅ Username changed successfully.",
        "uploading_photo": "⏳ Uploading and setting new photo...",
        "photo_update_success": "✅ Profile picture changed successfully.",
        "activity_log_title": "📜 **Activity Log for account `{phone}`**",
        "no_activity_log": "No activities recorded.",
        "log_page": "Page {current_page}/{total_pages}",
# السطر القديم
"disk_usage": "💾 Disk Usage",
# السطر الجديد (أكثر تفصيلاً)
"disk_usage": "💾 **Disk Usage:** `{percent}%` ({used} / {total})","total_accounts": "Total Accounts",
"active_clients_in_pool": "Active Clients in Pool",
"system_uptime": "⏱️ System Uptime",
"cpu_details": "⚙️ CPU",
"cpu_cores": "{physical} physical / {logical} logical cores",
"uptime_format": "{days} days, {hours:02}:{minutes:02}:{seconds:02}",
        "quick_action_message": "Choose a quick action for account `{phone}`:",
        "admin_account_banned_alert": "🔴 *Account Ban Alert* 🔴\nAccount `{phone}` (Owner: `{owner_id}`) has been banned.",
        "security_alert_new_login": "🔒 *Security Alert: New Login* 🔒\n\nNew session detected on account: `{phone}` (Owner: `{owner_id}`)\n**Details:**\n- Device: `{device_model}`\n- Location: `{ip}` (`{country}`)\n- App: `{app_name}`",
        "session_key_unregistered": "Session key is invalid or expired.",
        "single_cleaner_start_title": "**🧹 Advanced Account Cleaner `{phone}`**\n\nPlease choose a cleaning task. This action is final and cannot be undone.",
        "leave_all_channels": "👋 Leave all Channels",
        "leave_all_groups": "🚶‍♂️ Leave all Groups",
        "delete_bot_chats": "🤖 Delete Bot Chats",
        "delete_private_no_contact_chats": "👤 Delete Private Chats (Excluding Contacts)",
        "delete_deleted_contacts": "🗑️ Delete Deleted Contacts",
        "full_clean": "💥 Full Clean (All of the Above)",
        "back_to_account_management": "🔙 Back to Account Management",
        "confirm_single_cleaner": "**‼️ Final Confirmation for account `{phone}` ‼️**\n\nAre you sure you want to perform **'{action_text}'**?\nThis action cannot be undone.",
        "yes_clean_now": "‼️ Yes, Clean Now",
        "cancel_button": "🔙 Cancel",
        "cleaner_error_missing_info": "❌ Error, missing task information.",
        "starting_single_cleaner": "⏳ **Starting Cleaner for account `{phone}`...**\nConnecting and counting items...",
"login_code_error_generic": "❌ An error occurred\n\nEither the code you entered is incorrect, or its validity has expired.\n\n**💡 Try again, and attempt to send the code with spaces between the numbers (example: `1 2 3 4 5`)**",
        "checking_contacts": "⏳ Checking contacts...",
        "no_deleted_contacts": "✅ No deleted contacts found.",
        "deleted_contacts_success": "✅ Successfully deleted `{count}` contacts.",
        "starting_cleaner_found_dialogs": "⏳ **Starting Cleaner...** Found `{total_items}` chats.",
        "cleaning_in_progress": "**🧹 Cleaning in progress for account `{phone}`...**",
        "cleaner_completed": "✅ **Cleaning completed for account `{phone}`**\n\n**Results:**\n",
        "channels_left": "- Channels left",
        "groups_left": "- Groups left",
        "bot_chats_deleted": "- Bot chats deleted",
        "private_chats_deleted": "- Private chats deleted",
        "errors_occurred": "- Errors occurred",
        "cleaner_failed_error": "❌ Cleaning failed: {error}`",
        "getting_active_sessions": "⏳ Getting active sessions...",
        "current_bot_session": "📍 Current Bot Session",
        "device": "📱 Device",
        "platform": "💻 System",
        "application": "🚀 App",
        "ip_address": "📍 IP",
        "country": "Country",
        "creation_date": "🗓️ Creation Date",
        "bulk_name_button": "📝 Bulk Name Change",
"enter_bulk_name": "📝 Please send the new name. To add a last name, use the format: `First Name | Last Name`",
        "bulk_bio_button": "✍️ Bulk Bio Change",
"enter_bulk_bio": "✍️ Please send the new bio that will be applied to all selected accounts.",
        "session_age_detail": " {days} days and {hours} hours",
        "last_activity": "⚡ Last Activity",
        "delete_other_sessions_button": "🗑️ Delete All Other Sessions",
        "tfa_checking_status": "⏳ Checking Two-Factor Authentication (2FA) status...",
        "tfa_account_protected": "🔐 Account is already protected by a password.\nTo change, please send the **current** password.\n\nTo cancel, send /cancel",
        "tfa_account_not_protected": "🔓 Account is not protected.\nTo enable protection, please send a **new** password to set.\n\nTo cancel, send /cancel",
        "tfa_enter_current_password": "🔑 Okay, now send the **new** password.",
        "tfa_changing_password": "⏳ Changing password...",
        "tfa_password_change_success": "✅ Two-step verification password changed successfully.",
        "tfa_invalid_current_password": "❌ Incorrect current password. Operation cancelled.",
        "tfa_fatal_error": "❌ Fatal error: {error}",
        "tfa_enter_new_password": "💡 Okay. Now send a **hint** for the password (optional, you can send /skip to skip).",
        "tfa_hint_skipped": "👍 Hint skipped. Now send a **recovery email**.",
        "tfa_enter_recovery_email": "📧 Excellent. Now send a **recovery email**. This is very important for account recovery.",
        "tfa_enabling_2fa": "⏳ Attempting to enable two-factor authentication...",
        "tfa_email_unconfirmed": "✉️ Telegram sent a code to `{email}`. Please send the code here to complete the process.",
        "tfa_confirming_code": "⏳ Confirming code and enabling protection...",
        "tfa_email_confirmed_success": "✅ Email confirmed and protection enabled successfully!",
        "tfa_code_confirmation_failed": "❌ Error confirming code: {error}",
        "autoreply_menu_title": "📨 **Auto-Replies Management for account `{phone}`**\n\n",
        "add_new_reply_button": "➕ Add New Reply",
        "no_auto_replies": "No auto-replies added yet.",
# ... (الرسائل الموجودة لديك) ...
        "fetch_email_button": "📥 Fetch Latest Email",
"back_to_email_selection_button": "🔙 Back to Email Selection",
        "select_email_to_fetch": "Select the email to fetch the latest message from:",
        "fetching_email": "⏳ Fetching latest message from {email_address}...",
        "email_fetch_success": "✅ Latest message from {email_address}:\n\n**From:** {from_}\n**Subject:** {subject}\n**Date:** {date}\n\n**Content (first 500 chars):**\n```\n{body}\n```",
        "email_fetch_no_messages": "ℹ️ No messages in the inbox for this email.",
        "email_fetch_failed": "❌ Failed to fetch message: {error}",
        "decryption_failed": "❌ Failed to decode password. (Note: This is not secure encryption, just encoding).",
        # ... (بقية الرسائل الموجودة لديك) ...
        "replies_list": "Registered replies:",
 "returned_to_main_menu": "🏠 Returned to main menu.", # <== أضف هذا السطر
        "delete_button": "🗑️ Delete",
        "enter_keyword": "✍️ Please send the **keyword** to reply to (case-insensitive).",
        "enter_response_message": "💬 Okay, now send the **response message** to be sent when the keyword is found.",
        "autoreply_add_success": "✅ Auto-reply added successfully.",
        "autoreply_already_exists": "⚠️ This reply already exists for this account.",
        "autoreply_deleted": "✅ Auto-reply deleted.",
        "manage_proxies_title": "🌐 **Proxy Management** 🌐\n\n",
        "no_proxies_added": "No proxies added yet.",
        "available_proxies_list": "Available proxies list:",
        "assign_proxy_to_account": "Choose a proxy to link to account `{phone}` or unlink it.",
        "unassign_proxy_button": "🚫 Unlink Proxy",
        "add_new_proxy_button": "➕ Add New Proxy",
        "proxy_input_instructions": "Please send the proxy in the format:\n`protocol://user:pass@host:port`\nOr\n`protocol://host:port`\n\nSupported protocols: `http`, `socks4`, `socks5`",
        "proxy_add_success": "Proxy added successfully.",
        "proxy_already_exists": "This proxy already exists.",
        "proxy_invalid_format": "Invalid proxy format.",
        "proxy_not_found": "❌ Proxy not found.",
        "proxy_details_title": "**Proxy Details 🆔 {id}**\n\n",
        "proxy_usage": "**Usage:** Linked to `{count}` account(s).\n",
        "proxy_deleted": "✅ Proxy deleted and unlinked from accounts.",
        "proxy_assign_success": "✅ Proxy linkage updated successfully.",
        "error_account_not_selected": "❌ Error, account not selected.",
        "select_accounts_for_task": "**Bulk Task: {action_title}**\n\nPlease select the accounts that will perform the task:",
        "select_all_button": "✅ Select All",
        "invert_selection_button": "🔄 Invert Selection",
"manage_stories_button": "📖 Manage Stories",
        "story_menu_title": "📖 **Story Management for `{phone}`**",
        "story_post_now_button": "🚀 Post Story Now",
        "story_schedule_button": "⏰ Schedule Story",
        "story_view_active_button": "👀 View Active Stories",
        "story_delete_button": "🗑️ Delete Story",
        "story_under_development": "⚠️ This feature is currently under development.",
        "story_send_file_prompt": "🖼️ Please send the **photo** or **video** to post as a story.",
        "story_send_caption_prompt": "✍️ Excellent. Now send the **caption** for the story.\n\nYou can send /skip to skip adding a caption.",
        "story_posting_now": "⏳ Posting story, please wait...",
        "story_post_success": "✅ Story posted successfully!",
        "story_post_failed": "❌ Failed to post story: {error}",
        "task_story": "Scheduled Story",
        "clear_selection_button": "🗑️ Clear All",
        "continue_button": "🚀 Continue ({count})",
        "cancel_and_return_button": "🏠 Cancel and Return",
"manage_contacts_button": "📇 Manage Contacts",
"single_contact_menu_title": "📇 **Contact Management for {phone}**",
"add_contacts_single_button": "➕ Add Contacts",
"delete_all_contacts_single_button": "🗑️ Delete All Contacts",
"export_contacts_single_button": "📄 Export Contacts",
"confirm_delete_all_contacts": "⚠️ **Confirmation** ⚠️\nAre you sure you want to delete **all** contacts from account `{phone}`? This action cannot be undone.",
        "no_accounts_selected_cancel": "❌ No accounts selected. Operation cancelled.",
        "enter_group_link": "🔗 Please send the public or private channel/group link.",
        "warning_bulk_delete": "‼️ **Serious Warning** ‼️\nYou are about to **'{delete_type_text}'** **{count}** account(s).",
        "warning_bulk_logout": "⚠️ **Confirmation** ⚠️\nYou are about to log out from **{count}** account(s). You will need to log in again later.",
        "yes_im_sure": "✅ Yes, I'm sure",
        "starting_bulk_task": "⏳ **Starting '{action_type}' task on {count} account(s)...**",
        "bulk_task_report_header": "📋 **'{action_type}' Task Report for Link: {link}**\n",
        "bulk_task_report_header_no_link": "📋 **'{action_type}' Task Report**\n",
        "task_success": "Success",
        "account_already_member": "Account is already a member",
"session_key_duplicated_error": "❌ Fatal Error: This session key was invalidated by Telegram for being used in two places at once. Please generate a new session file and ensure any other scripts using it are stopped before sending.",
        "account_not_member": "Account is not a member",
        "task_failure": "Failed - {error}",
        "task_completed_summary": "\n**Task completed.**\n- **Success:** {success_count}\n- **Failed/Warning:** {failure_count}",
        "deleting_account_type_full": "Delete with Logout",
        "deleting_account_type_local": "Delete from Bot Only",
        "deleting_account_progress": "⏳ Deleting account `{phone}`...",
        "delete_step_logout": "**Step 1/2:** Logging out session.",
        "delete_step_local_data": "**Step 2/2:** Deleting local data.",
        "delete_success": "✅ Account deleted successfully.",
        "logout_success": "Logged out",
        "already_logged_out": "Account already logged out",
        "scraper_options_title": "⚙️ **Extraction Options**\n\nWhich type of members do you want to extract?",
        "all_members": "👥 All Members",
        "recent_active_members": "⚡️ Recently Active Members",
        "enter_scraper_limit": "🔢 What is the number of members you want to extract?\nSend '0' to extract all (may be slow for large groups).",
        "invalid_number_input": "❌ Please send a valid number (0 or greater).",
        "enter_group_link_scraper": "🔗 Okay, now send the group link from which to extract members.",
        "extracting_members_from": "⏳ Extracting members from {link} using account {phone}...",
        "scraper_account_needs_login": "The account selected for extraction needs login",
        "extracting_progress": "⏳ Extracted {count} members so far...",
        "no_members_found": "ℹ️ No members found or group is inaccessible.",
        "extraction_success_caption": "✅ Extracted {count} members successfully.",
        "extraction_failed": "❌ Member extraction failed: {error}",
        "exporting_sessions_start": "⏳ **Starting export of {count} sessions...**",
        "exporting_sessions_in_progress": "**🔑 Exporting sessions...**",
        "security_warning_export_sessions": "⚠️ **Security Warning** ⚠️\nYou are about to export **{count}** session strings.\nSession strings are highly sensitive and can be used for full access to your accounts. Do not share them with anyone.\n\nDo you want to proceed?",
        "choose_delete_method": "**Choose bulk deletion method:**\n\n**- Delete with Logout:** Terminates sessions from Telegram servers and deletes accounts from the bot. (Safe and Recommended)\n**- Delete from Bot Only:** Deletes accounts from the bot's list only and leaves sessions active on Telegram.",
        "confirm_delete_full_logout": "🗑️ Delete with Logout",
        "confirm_delete_local_only": "🔪 Delete from Bot Only",
        "cleaning_accounts_bulk": "**🧹 Bulk Account Cleaner ({count} accounts)**\n\nPlease choose a cleaning task. This action is final and cannot be undone.",
        "confirm_bulk_cleaner": "**‼️ Final Confirmation ‼️**\n\nAre you sure you want to perform **'{action_text}'** on all selected accounts?",
        "starting_bulk_cleaner": "⏳ **Starting bulk cleaning (`{clean_type}`) on {count} accounts...**\nThis operation may take a long time.",
        "working_on_account": "⏳ **Working on account {current}/{total} (`{phone}`)**",
        "bulk_cleaner_report_header": "**📋 Bulk Account Cleaner Report (`{clean_type}`)**\n",
        "bulk_cleaner_success": "✅ `{phone}`: Success ({details})",
        "export_csv_preparing": "⏳ Preparing file...",
        "no_accounts_to_export": "❌ You have no accounts to export.",
        "export_csv_success": "✅ Exported {count} account(s) data successfully.",
        "scheduled_tasks_menu_title": "⏰ **Scheduled Tasks** ⏰\n\n",
        "add_new_task_button": "➕ Add New Task",
        "no_scheduled_tasks": "No scheduled tasks currently.",
                "task_join": "Join",
        "task_message": "Message",
        "task_check": "Check",
        "task_next_run": "Next:",
        "task_pause_button": "⏸️",
        "task_resume_button": "▶️",
        "task_delete_button": "🗑️",
        "choose_task_type": "1️⃣ Choose scheduled task type:",
        "task_type_join": "🚀 Join Channel/Group",
        "task_type_message": "✉️ Send Scheduled Message",
        "task_type_check": "✔️ Auto Account Check",
        "select_task_accounts": "2️⃣ Please select the accounts that will perform the task:",
        "enter_task_target": "3️⃣ Send the public or private channel/group link.",
        "enter_message_target": "3️⃣ Send the channel/user ID or link to send the message to.",
        "enter_message_content": "4️⃣ Now send the message content you want to schedule.",
        "enter_cron_schedule": "5️⃣ Finally, send the task schedule in Cron format.\n\n{cron_examples}",
        "cron_examples": "**Cron Examples:**\n- `* * * * *` (Every minute)\n- `0 * * * *` (Every hour on the hour)\n- `0 8 * * 5` (Every Friday at 8:00 AM)\nFormat: `minute hour day month day_of_week`",
        "invalid_cron_format": "❌ Invalid Cron format, please try again.",
        "task_scheduled_success": "✅ Task scheduled successfully.\nNext run time: {next_run_time}",
        "task_scheduling_failed": "❌ Failed to add task to scheduler: {error}",
        "task_not_found": "❌ Task not found, perhaps it was deleted.",
        "task_deleted": "✅ Scheduled task deleted.",
        "task_paused": "⏸️ Task paused.",
        "task_resumed": "▶️ Task resumed.",
        "admin_panel_title": "👑 **Admin Control Panel** 👑\n\nChoose an action:",
        "add_subscription_button": "➕ Activate Subscription",
        "remove_subscription_button": "➖ Deactivate Subscription",
        "view_subscribers_button": "👥 View Subscribers",
        "custom_broadcast_button": "📢 Custom Broadcast",
        "monitor_resources_button": "📊 Monitor Resources",
        "backup_db_button": "💾 Backup",
        "restore_db_button": "🔄 Restore",
        "no_subscribers": "ℹ️ No subscribers currently.",
        "subscribers_list_title": "👥 **Subscribers List**\n\nClick on a subscriber to view details:\n",
        "subscriber_info_card_title": "💳 **Subscriber Info Card**\n\n",
        "subscriber_name": "👤 **Name:** {name}",
        "subscriber_id": "🆔 **ID:** `{id}`",
        "subscription_period": "📅 **Subscription:** From `{start_date}` to `{end_date}`",
        "current_accounts_count": "💼 **Current Accounts Count:** `{count}`",
        "last_account_add": "➕ **Last Account Added:** `{date}`",
        "monitoring_title": "📊 **System Resource Monitoring**\n\n",
        "psutil_not_installed": "❌ **Error:** `psutil` library not installed.\n",
        "cpu_usage": "💻 **CPU Usage:** `{percent}%`",
        # السطر القديم
"ram_usage": "🧠 **RAM Usage:** `{percent}%` ({used:.1f}MB / {total:.1f}MB)",
# السطر الجديد (بدون .1f)
"ram_usage": "🧠 **RAM Usage:** `{percent}%` ({used} / {total})",
        "active_scheduled_tasks": "⏰ **Scheduled Tasks:** `{count}` active tasks",
        "backup_preparing": "⏳ Creating backup...",
        "backup_success": "✅ Database backup created successfully.",
        "backup_failed": "❌ Failed to create backup: {error}",
        "restore_warning": "⚠️ **Serious Warning:**\nYou are about to replace the current database. All current data will be deleted.\n\nPlease send the backup file (`.db`) to proceed.",
        "invalid_db_file": "❌ Invalid file. Send a database file with `.db` extension.",
        "restore_in_progress": "⏳ File received, restoring...",
        "restore_success_restart": "✅ **Database restored successfully.**\n\n**‼️ Very Important: ‼️**\nYou must **restart the bot manually now** to apply changes and avoid any issues.",
        "enter_user_id_for_sub": "📝 Please send the **ID** of the user you want to activate the subscription for.",
        "invalid_id_input": "❌ Invalid input. Please send a valid numeric ID.",
        "enter_sub_days": "🗓️ Okay, now send the **number of days** for the subscription (e.g., 30).",
        "sub_activation_success": "✅ Subscription activated for user `{target_user_id}` for `{days}` days.\nExpires on: `{end_date}`",
        "sub_activation_notification_to_user": "🎉 Your bot subscription has been activated/renewed!\n\n⏳ **Subscription Duration:** {days} days\n⌛ **Expires:** {end_date}\n\nThank you for using the bot! ✨",
        "failed_to_notify_user": "⚠️ Could not send message to user. Error: {error}",
        "invalid_days_input": "❌ Invalid input. Please send a valid numeric number of days.",
        "choose_user_to_deactivate_sub": "Choose user to deactivate subscription for:",
        "sub_deactivation_success": "✅ Subscription for user `{target_user_id}` deactivated successfully.",
        "sub_deactivation_notification_to_user": "ℹ️ We regret to inform you, your bot subscription has been cancelled.",
        "sub_not_found_to_deactivate": "❌ User not found for subscription deactivation.",
        "broadcast_menu_title": "**Custom Broadcast**\n\nChoose the category you want to send the message to:",
        "broadcast_to_all": "📢 To All",
        "broadcast_by_sub_date": "📅 By Subscription Date",
        "broadcast_by_accounts_count": "💼 By Account Count",
        "broadcast_to_specific_ids": "🆔 To Specific Users",
        "enter_date_range": "Please send start and end dates, separated by |.\nFormat: `YYYY-MM-DD | YYYY-MM-DD`",
        "invalid_date_format": "❌ Invalid date format.",
        "enter_account_count_range": "Please send min and max account count, separated by |.\nExample: `0 | 5` (for users with 0 to 5 accounts)",
        "invalid_number_range_format": "❌ Invalid number format.",
        "enter_user_ids": "Please send user IDs, separated by space or new line.",
        "no_users_match_criteria": "❌ No users found matching these criteria.",
        # السطر القديم: "users_selected_prompt_message": "Selected `{count}` user(s).\n\nNow, send the message you want to broadcast..."
# السطر الجديد:
"users_selected_prompt_message": "✅ Selected `{count}` user(s).\n\nNow, **forward** the message you want to broadcast here.",
        # السطر القديم: "confirm_broadcast": "Are you sure you want to send this message...Preview:..."
# السطر الجديد:
"confirm_broadcast": "Are you sure you want to broadcast the forwarded message to **{count}** subscriber(s)?",
        "yes_send_now_button": "✅ Yes, Send Now ({count})",
        "broadcast_error_no_data": "❌ Error: No message or targets found. Cancelled.",
        "broadcast_sending": "⏳ Sending broadcast...",
        "broadcast_sending_progress": "**📢 Sending...**",
        "broadcast_completed": "✅ **Broadcast Completed**\n\n- Sent successfully to: {success_count}\n- Failed to send to: {fail_count}",
        "daily_admin_alerts": "**⚠️ Daily Admin Alerts ⚠️**\n\n",
"relogin_success": "✅ Successfully re-logged into account: `{phone}`",
"relogin_flow_new_account_added": "✅ Successfully logged into new account: `{new_phone}`.\n\n⚠️ However, account `{old_phone}` still needs to be logged in.",
        "expiring_soon_subscriptions": "**Subscriptions expiring soon:**\n",
        "user_account_needs_login_notification_title": "🚨 **Alert: Accounts need login!** 🚨",
        "user_account_needs_login_notification_body": "Hello {user_mention},\n\nWe have some of your accounts that need to be re-logged in to function correctly:\n",
        "account_needs_login_list_item": "- `{phone}`",
        "relogin_instructions": "\nPlease go to **Manage Your Accounts** then select the relevant account and log in again.",
        "bot_restarted_message": "Bot restarted successfully!",
        "next": "Next",
        "previous": "Previous",
        "unknown_name": "Undefined",
        "not_available": "N/A",
        "not_specified": "Not specified",
        "session_file_add_method": "session file",
        "add_account": "Add account",
        "add_via_session_file_success": "Added successfully via session file.",
        "phone_number_add_method": "phone number",
        "string_session_add_method": "session string",
        "add_via_string_session_success": "Added successfully via session string.",
        "success": "Success",
        "failed": "Failed",
        "error": "Error",
        "security_alert": "Security Alert",
        "new_login_from": "new login from",
        "account_banned_alert": "Account Ban Alert",
        "update_data_log": "Data Update",
        "manual_update_requested": "Manual update requested.",
        "getting_last_message": "⏳ Getting last message...",
        "no_messages_in_account": "ℹ️ No messages in this account.",
        "last_message_header": "📥 **Last Message in account `{phone}`**",
        "from": "From",
        "date": "Date",
        "content": "Content",
        "message_no_text": "[Message without text]",
        "get_last_message_log": "Get last message",
        "deleting_sessions": "⏳ Deleting sessions...",
        "delete_sessions_log": "Delete Sessions",
        "all_other_sessions_deleted": "All other sessions deleted.",
        "all_other_sessions_deleted_success": "✅ All other sessions deleted successfully.",
"email_add_failed_credentials": "❌ Verification Failed. The password or email is incorrect. The email was not added.",
        "reset_auths_warning": "⚠️ **Warning** ⚠️\nYou are about to terminate all other active sessions for this account except the current bot session. Are you sure you want to proceed?",
        "yes_delete_now": "‼️ Yes, Delete Now",
        "logging_out_account": "⏳ Logging out account `{phone}`...",
        "logout_account_log": "Logout Account",
        "logout_success_update_list": "✅ Account logged out successfully. List will be updated now.",
        "logout_confirmation_message": "⚠️ **Logout Confirmation** ⚠️\nAre you sure you want to log out from account `{phone}`? You will need to log in again later.",
        "yes_logout_now": "‼️ Yes, Logout Now",
        "end_session_full_delete": "Terminate Session on Full Delete",
        "warning_logout_failed_continue_local_delete": "⚠️ Warning: Could not log out ({error}). Continuing with local deletion.",
        "change_name_log": "Change Name",
        "to": "to",
        "change_bio_log": "Change Bio",
        "change_username_log": "Change Username",
        "change_photo_log": "Change Photo",
        "new_photo_uploaded": "New photo uploaded successfully.",
        "details": "Details",
        "single_cleaner_log": "Single Cleaner",
        "deleted": "deleted",
        "contacts": "contacts",
"tfa_menu_title": "🔐 **Manage Two-Factor Authentication (2FA)**",
"tfa_status_header": "📊 **Current Status for account `{phone}`:**",
"tfa_is_enabled": "✅ Enabled",
"tfa_is_disabled": "❌ Disabled",
"tfa_recovery_email": "Recovery Email:",
"tfa_no_recovery_email": "Not Set",
"tfa_view_status_button": "⚙️ View Status",
"tfa_change_password_button": "🔑 add|Change Password",
"tfa_change_email_button": "✉️ Add/Change Recovery Email",
"tfa_disable_button": "🔓 Remove Protection (Disable)",
"tfa_enter_new_recovery_email": "✉️ Please send the new recovery email.",
"tfa_email_change_success": "✅ Recovery email changed successfully.",
"tfa_email_change_failed": "❌ Failed to change recovery email: {error}",
"tfa_disable_prompt": "⚠️ **Confirmation** ⚠️\nTo disable protection, please enter the current password.",
"tfa_disable_success": "✅ Two-factor authentication disabled successfully.",
"tfa_disable_failed": "❌ Failed to disable protection: {error}",
        "change_2fa_log": "Change 2FA",
        "password_change_success_log": "Password changed successfully.",
        "enable_2fa_log": "Enable 2FA",
        "protection_enabled_success_log": "Protection enabled successfully.",
        "waiting_email_code_log": "Waiting for email confirmation code.",
        "email_confirmed_protection_enabled_log": "Email confirmed and protection enabled.",
        "failed_code_confirmation": "Code confirmation failed",
        "auto_reply": "Auto Reply",
        "replied_to": "replied to",
        "for_user": "for user",
        "add_autoreply_log": "Add Auto Reply",
        "keyword": "Keyword",
        "back_to_proxies_list": "🔙 Back to Proxies List",
        "back_to_subscribers_list": "🔙 Back to Subscribers List",
        "are_you_sure_to_proceed": "Are you sure you want to proceed?",
        "bulk_join_log": "Bulk Join",
        "success_in_joining": "successfully joined",
        "bulk_leave_log": "Bulk Leave",
        "success_in_leaving": "successfully left",
        "bulk_task": "Bulk Task",
        "for_link": "for link",
        "start_member_extraction_log": "Start Member Extraction",
        "success_member_extraction_log": "Successful Member Extraction",
        "extracted": "extracted",
        "failed_member_extraction_log": "Failed Member Extraction",
        "bulk_export_session_log": "Bulk Session Export",
        "bulk_cleaner_log": "Bulk Cleaner",
        "no_change": "no change",
        "accounts_count": "account(s)",
        "scheduled_task_report_header": "**Scheduled Task `{job_id}` Report**",
        "scheduled_task": "Scheduled Task",
        "target": "Target",
        "loading_scheduled_tasks": "Loading scheduled and smart tasks from database...",
        "failed_to_load_scheduled_task": "Failed to load scheduled task {job_id}: {error}",
        "loaded_scheduled_tasks_count": "Loaded {count} scheduled tasks.",
        "scheduled_daily_smart_notifications": "Daily smart notifications task scheduled.",
        "failed_to_schedule_smart_notifications": "Failed to schedule smart notifications task: {error}",
        "scheduled_client_pool_cleanup": "Client pool cleanup task scheduled.",
        "failed_to_schedule_client_pool_cleanup": "Failed to schedule client pool cleanup task: {error}",
        "auto_reply_listeners_info": "Auto-reply listeners will be started on demand (not at startup).",
        "failed_to_send_admin_notification": "Failed to send notification to admin {admin_id}: {error}",
        "unknown": "Unknown",
        "expires": "Expires",
        "expires_on": "expires on",
        "total_proxies": "Total Proxies",
        "used_proxies": "Used Proxies",
        "active_sessions_header": "🔒 **Active Sessions for account** `{phone} ({account_name})`:",
        "error_getting_sessions": "❌ Error getting sessions: {error}",
        "not_subscribed": "❌ You are not subscribed to the bot.",
        "subscription_active": "✅ Your subscription is active and expires on {end_date}.",
        "subscription_expired": "❌ Your subscription has expired.",
        "no_accounts_registered": "❌ No accounts registered for you.",
        "choose_language_prompt": "Please choose your language:",
        "subscriber_not_found": "❌ Subscriber not found.",
        "before": "{age} ago",
        "login_success_code": "Login success (code)",
        "login_success_password": "Login success (password)",
        "failed_needs_login": "Failed - needs login",
        "cleaner_delete_deleted_contacts_log": "Cleaner - Delete Deleted Contacts",
        "delete_proxy_button": "🗑️ Delete Proxy",
        "bulk_task_final_report": "✅ Task '{action_title}' completed.\n\n- **Success:** {success_count}\n- **Failed/Warning:** {failure_count}",
        "back_to_bulk_menu": "🔙 Back to Bulk Management",
    }
}

DEFAULT_LANG = 'ar'

def _(key: str, user_id: int, **kwargs) -> str:
    """
    Retrieves localized text for a given key and user ID.
    """
    lang = get_user_language(user_id)
    if lang is None:
        lang = DEFAULT_LANG

    text = LANGUAGE_DATA.get(lang, {}).get(key) or LANGUAGE_DATA.get(DEFAULT_LANG, {}).get(key)
    
    if not text:
        return f"Missing Text: {key} (Lang: {lang or 'N/A'})"

    # --- هذا هو الإصلاح الجذري ---
    # نقوم بتعبئة النص فقط في حال وجود بيانات لتعبئتها
    if kwargs:
        return text.format(**kwargs)
    # إذا لم تكن هناك بيانات، نرجع النص الخام كما هو
    return text
    # --- نهاية الإصلاح ---



# ==============================================================================
# ||                   [تعديل] تجمعات اتصالات Telethon (Connection Pooling)    ||
# ==============================================================================
# يفضل استخدام defaultdict لسهولة الوصول وإنشاء قيم افتراضية
CLIENT_POOL = defaultdict(lambda: {'client': None, 'last_used_monotonic': None})
# مدة صلاحية العميل في الذاكرة (بالثواني) - 5 دقائق هنا
CLIENT_TIMEOUT_SECONDS = 300


# ==============================================================================
# ||                   ثالثاً: إدارة قاعدة البيانات (SQLite)                    ||
# ==============================================================================
def db_connect():
    """إنشاء اتصال بقاعدة البيانات وإرجاع كائن الاتصال والمؤشر."""
    con = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=10)
    con.row_factory = sqlite3.Row
    return con, con.cursor()

def init_db():
    """
    [تعديل جذري V9] تهيئة قاعدة البيانات مع تحديثات للمهام المجدولة وإضافة عمود اللغة.
    """
    con, cur = db_connect()
    # جدول الحسابات
    cur.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            phone TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            user_id INTEGER, first_name TEXT, username TEXT,
            status TEXT DEFAULT 'UNKNOWN', last_check TEXT,
            proxy_id INTEGER, add_method TEXT, creation_date TEXT,
            auth_hashes TEXT,
            UNIQUE(phone, owner_id)
        )
    ''')
    # جدول البروكسيات
    cur.execute('''
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY,
            proxy_str TEXT UNIQUE NOT NULL, protocol TEXT, hostname TEXT, port INTEGER,
            username TEXT, password TEXT, usage_count INTEGER DEFAULT 0
        )
    ''')
    # سجل النشاط
    cur.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, action TEXT NOT NULL, details TEXT
        )
    ''')
    # جدول المشتركين (تم إضافة عمود language)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            language TEXT DEFAULT 'ar' NOT NULL
        )
    ''')
    # <== تم الإصلاح: التحقق مما إذا كان عمود 'language' موجوداً في جدول 'subscribers'
    cur.execute("PRAGMA table_info(subscribers)")
    columns = [col[1] for col in cur.fetchall()]
    if 'language' not in columns:
        cur.execute("ALTER TABLE subscribers ADD COLUMN language TEXT DEFAULT 'ar' NOT NULL")
        logger.info("تم إضافة عمود 'language' إلى جدول 'subscribers'.")


    # جدول الردود الآلية
    cur.execute('''
        CREATE TABLE IF NOT EXISTS auto_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            phone TEXT NOT NULL,
            keyword TEXT NOT NULL,
            response TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            UNIQUE(owner_id, phone, keyword)
        )
    ''')
    # جدول المهام المجدولة (مع حقل الحالة الجديد)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE NOT NULL,
            owner_id INTEGER NOT NULL,
            phones TEXT NOT NULL,
            task_type TEXT NOT NULL,
            target TEXT,
            content TEXT,
            cron_str TEXT NOT NULL,
            next_run_time TEXT,
            status TEXT DEFAULT 'active' NOT NULL -- 'active' or 'paused'
        )
    ''')

    # إضافة المؤشرات لتحسين الأداء
    # SQLite يقوم بإنشاء مؤشر تلقائي للمفاتيح الأساسية والفريدة.
    # يمكن إضافة مؤشرات لـ foreign keys أو الأعمدة التي يتم البحث فيها بكثرة بدون unique/primary.
    cur.execute("CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts (status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_accounts_owner_id ON accounts (owner_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_log_phone ON activity_log (phone)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_auto_replies_owner_phone ON auto_replies (owner_id, phone)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_owner_id ON scheduled_tasks (owner_id)")

    # <== تم الإصلاح: إضافة جدول القصص المجدولة والفهرس
    cur.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE NOT NULL,
            owner_id INTEGER NOT NULL,
            phone TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_type TEXT NOT NULL, -- 'photo' or 'video'
            caption TEXT,
            cron_str TEXT NOT NULL,
            next_run_time TEXT,
            status TEXT DEFAULT 'active' NOT NULL -- 'active' or 'paused'
        )
    ''')
    cur.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_stories_owner_id ON scheduled_stories (owner_id)")

# --- [إضافة جديدة] جدول إيميلات الاستيراد ---
    # ... (الكود الموجود لديك في دالة init_db) ...
    # --- [إضافة جديدة] جدول إيميلات الاستيراد ---
    cur.execute('''
        CREATE TABLE IF NOT EXISTS import_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            email_address TEXT NOT NULL,
            app_password_encrypted TEXT NOT NULL,
            added_date TEXT NOT NULL,
            UNIQUE(owner_id, email_address)
        )
    ''')

    # --- [إضافة جديدة] جدول لحفظ كلمات مرور 2FA للحسابات ---
# ... (بقية الكود الموجود لديك في دالة init_db) ...

    # --- [إضافة جديدة] جدول لحفظ كلمات مرور 2FA للحسابات ---
    cur.execute('''
        CREATE TABLE IF NOT EXISTS account_2fa_passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            password_encrypted TEXT NOT NULL,
            hint TEXT,
            recovery_email TEXT,
            last_updated TEXT NOT NULL
        )
    ''')

    con.commit()
    con.close()
    logger.info("تم التحقق من قاعدة البيانات والجداول جاهزة للإصدار 9.5.")

# --- دوال التعامل مع المشتركين (تم تحديثها لدعم اللغة) ---
def add_subscriber(user_id, days):
    con, cur = db_connect()
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    # الاحتفاظ باللغة الحالية إذا كان المستخدم موجوداً
    cur.execute("SELECT language FROM subscribers WHERE user_id = ?", (user_id,))
    current_lang_row = cur.fetchone()
    current_lang = current_lang_row['language'] if current_lang_row else DEFAULT_LANG

    cur.execute("INSERT OR REPLACE INTO subscribers (user_id, start_date, end_date, language) VALUES (?, ?, ?, ?)",
                (user_id, start_date.isoformat(), end_date.isoformat(), current_lang))
    con.commit()
    con.close()
    return start_date, end_date

def remove_subscriber(user_id):
    con, cur = db_connect()
    cur.execute("DELETE FROM subscribers WHERE user_id = ?", (user_id,))
    con.commit()
    con.close()
    return cur.rowcount > 0

def get_subscriber(user_id):
    con, cur = db_connect()
    cur.execute("SELECT * FROM subscribers WHERE user_id = ?", (user_id,))
    sub = cur.fetchone()
    con.close()
    return sub

def get_all_subscribers(only_active=False):
    con, cur = db_connect()
    query = "SELECT * FROM subscribers"
    if only_active:
        query += " WHERE end_date > ?"
    query += " ORDER BY end_date DESC"

    params = (datetime.now().isoformat(),) if only_active else ()
    cur.execute(query, params)

    subs = cur.fetchall()
    con.close()
    return subs

# [إضافة] دوال جديدة لجلب المشتركين حسب معايير معينة للبث المخصص
def get_subs_by_date_range(start_date, end_date):
    con, cur = db_connect()
    cur.execute("SELECT user_id FROM subscribers WHERE start_date BETWEEN ? AND ?", (start_date, end_date))
    return [row['user_id'] for row in cur.fetchall()]

def get_subs_by_account_count(min_count, max_count):
    con, cur = db_connect()
    cur.execute("""
        SELECT s.user_id
        FROM subscribers s
        LEFT JOIN accounts a ON s.user_id = a.owner_id
        GROUP BY s.user_id
        HAVING COUNT(a.id) BETWEEN ? AND ?
    """, (min_count, max_count))
    return [row['user_id'] for row in cur.fetchall()]

# [إضافة] دوال جديدة للتعامل مع لغة المستخدم
def get_user_language(user_id: int) -> str:
    """يحصل على لغة المستخدم المفضلة من قاعدة البيانات."""
    con, cur = db_connect()
    cur.execute("SELECT language FROM subscribers WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    con.close()
    
    # --- هذا هو التعديل ---
    # إذا لم نجد المستخدم في قاعدة البيانات، نرجع None
    # هذا سيجعل شرط if not get_user_language(user_id) يعمل بشكل صحيح للمستخدم الجديد
    if not result:
        return None
    # إذا كان موجوداً، نرجع لغته أو اللغة الافتراضية
    return result['language'] if result['language'] else DEFAULT_LANG
    # --- نهاية التعديل ---


def set_user_language(user_id: int, lang_code: str):
    """
    يحدد لغة المستخدم المفضلة في قاعدة البيانات.
    إذا كان المستخدم جديداً، يقوم بإضافته مع تاريخ اشتراك منتهي.
    """
    con, cur = db_connect()
    # تاريخ قديم جداً لضمان أن المستخدم الجديد غير مشترك
    past_date = "1970-01-01T00:00:00"
    
    # نستخدم هذا الأمر الذكي:
    # إذا لم يكن المستخدم موجوداً، قم بإضافته مع لغته وتاريخ قديم.
    # إذا كان موجوداً، قم فقط بتحديث لغته.
    cur.execute("""
        INSERT INTO subscribers (user_id, start_date, end_date, language) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) 
        DO UPDATE SET language = excluded.language;
    """, (user_id, past_date, past_date, lang_code))
    
    con.commit()
    con.close()


# --- دوال التعامل مع الحسابات (معدلة لعزل البيانات) ---
def add_account_to_db(phone, owner_id, user_id=None, first_name=None, username=None, status='UNKNOWN', add_method=None, creation_date=None):
    con, cur = db_connect()
    cur.execute("INSERT OR IGNORE INTO accounts (phone, owner_id) VALUES (?, ?)", (phone, owner_id))
    cur.execute("""
        UPDATE accounts
        SET user_id = ?, first_name = ?, username = ?, status = ?,
            add_method = COALESCE(?, add_method),
            creation_date = COALESCE(?, creation_date)
        WHERE phone = ? AND owner_id = ?
    """, (user_id, first_name, username, status, add_method, creation_date, phone, owner_id))
    con.commit()
    con.close()

def remove_account_from_db(phone, owner_id):
    con, cur = db_connect()
    cur.execute("SELECT proxy_id FROM accounts WHERE phone = ? AND owner_id = ?", (phone, owner_id))
    result = cur.fetchone()
    if result and result['proxy_id']:
        cur.execute("UPDATE proxies SET usage_count = usage_count - 1 WHERE id = ? AND usage_count > 0", (result['proxy_id'],))
    cur.execute("DELETE FROM accounts WHERE phone = ? AND owner_id = ?", (phone, owner_id))
    cur.execute("DELETE FROM activity_log WHERE phone = ?", (phone,))
    cur.execute("DELETE FROM auto_replies WHERE phone = ? AND owner_id = ?", (phone, owner_id))
    con.commit()
    con.close()

def get_accounts_by_owner(owner_id, only_active=False, only_inactive=False):
    con, cur = db_connect()
    query = "SELECT * FROM accounts WHERE owner_id = ?"
    params = [owner_id]
    if only_active:
        query += " AND status = 'ACTIVE'"
    if only_inactive:
        query += " AND status != 'ACTIVE'"
    query += " ORDER BY id ASC"
    cur.execute(query, tuple(params))
    accounts = cur.fetchall()
    con.close()
    return accounts

def get_account_by_phone(phone, owner_id):
    con, cur = db_connect()
    cur.execute("SELECT * FROM accounts WHERE phone = ? AND owner_id = ?", (phone, owner_id))
    account = cur.fetchone()
    con.close()
    return account

def get_last_added_account_date(owner_id):
    con, cur = db_connect()
    cur.execute("SELECT MAX(creation_date) as last_date FROM accounts WHERE owner_id = ? AND creation_date IS NOT NULL", (owner_id,))
    result = cur.fetchone()
    con.close()
    return result['last_date'] if result and result['last_date'] else None


def update_account_status(phone: str, owner_id: int, status: str, user_id: int = None, first_name: str = None, username: str = None, last_check_update: bool = True):
    con, cur = db_connect()
    current_account = get_account_by_phone(phone, owner_id)
    if not current_account: return

    if user_id is None: user_id = current_account['user_id']
    if first_name is None: first_name = current_account['first_name']
    if username is None: username = current_account['username']

    query = "UPDATE accounts SET status = COALESCE(?, status), user_id = ?, first_name = ?, username = ?"
    params = [status, user_id, first_name, username]

    if last_check_update:
        query += ", last_check = ?"
        # <== تم الإصلاح: تغيير صيغة الوقت إلى نظام 12 ساعة مع AM/PM
        params.append(datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"))

    query += " WHERE phone = ? AND owner_id = ?"
    params.extend([phone, owner_id])

    cur.execute(query, tuple(params))
    con.commit()
    con.close()


def update_account_auth_hashes(phone, owner_id, auth_hashes):
    con, cur = db_connect()
    hashes_json = json.dumps(auth_hashes)
    cur.execute("UPDATE accounts SET auth_hashes = ? WHERE phone = ? AND owner_id = ?", (hashes_json, phone, owner_id))
    con.commit()
    con.close()

def assign_proxy_to_account(phone, owner_id, proxy_id):
    con, cur = db_connect()
    cur.execute("SELECT proxy_id FROM accounts WHERE phone = ? AND owner_id = ?", (phone, owner_id))
    old_proxy_id = cur.fetchone()
    if old_proxy_id and old_proxy_id['proxy_id']:
        cur.execute("UPDATE proxies SET usage_count = usage_count - 1 WHERE id = ? AND usage_count > 0", (old_proxy_id['proxy_id'],))
    cur.execute("UPDATE accounts SET proxy_id = ? WHERE phone = ? AND owner_id = ?", (proxy_id, phone, owner_id))
    if proxy_id:
        cur.execute("UPDATE proxies SET usage_count = usage_count + 1 WHERE id = ?", (proxy_id,))
    con.commit()
    con.close()
    log_activity(phone, _("proxy_assign_success", owner_id), f"Assigned Proxy ID: {proxy_id or 'None'}")

# --- دوال التعامل مع البروكسيات والسجل ---
def add_proxy_to_db(proxy_str):
    match = re.match(r'(socks5|http|socks4)://(?:(.*?):(.*?)@)?(.*?):(\d+)', proxy_str)
    if not match: return False, _("proxy_invalid_format", 0)
    protocol, username, password, hostname, port = match.groups()
    con, cur = db_connect()
    try:
        cur.execute("INSERT INTO proxies (proxy_str, protocol, hostname, port, username, password) VALUES (?, ?, ?, ?, ?, ?)",
                    (proxy_str, protocol, hostname, int(port), username, password))
        con.commit()
        return True, _("proxy_add_success", 0)
    except sqlite3.IntegrityError:
        return False, _("proxy_already_exists", 0)
    finally:
        con.close()

def get_all_proxies_from_db():
    con, cur = db_connect()
    cur.execute("SELECT * FROM proxies ORDER BY id ASC")
    proxies = cur.fetchall()
    con.close()
    return proxies

def remove_proxy_from_db(proxy_id):
    con, cur = db_connect()
    cur.execute("UPDATE accounts SET proxy_id = NULL WHERE proxy_id = ?", (proxy_id,))
    cur.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
    con.commit()
    con.close()

def get_proxy_by_id(proxy_id):
    if not proxy_id: return None
    con, cur = db_connect()
    cur.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,))
    proxy = cur.fetchone()
    con.close()
    return proxy

def log_activity(phone, action, details=""):
    con, cur = db_connect()
    cur.execute("INSERT INTO activity_log (phone, action, details) VALUES (?, ?, ?)",
                (phone, action, details))
    con.commit()
    con.close()

def get_activity_log(phone):
    con, cur = db_connect()
    cur.execute("SELECT * FROM activity_log WHERE phone = ? ORDER BY timestamp DESC", (phone,))
    logs = cur.fetchall()
    con.close()
    return logs

# --- دوال التعامل مع الردود الآلية ---
def add_auto_reply(owner_id, phone, keyword, response):
    con, cur = db_connect()
    try:
        cur.execute("INSERT INTO auto_replies (owner_id, phone, keyword, response) VALUES (?, ?, ?, ?)",
                    (owner_id, phone, keyword.lower(), response))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()

def get_auto_replies(owner_id, phone):
    con, cur = db_connect()
    cur.execute("SELECT * FROM auto_replies WHERE owner_id = ? AND phone = ? ORDER BY keyword", (owner_id, phone))
    replies = cur.fetchall()
    con.close()
    return replies

def remove_auto_reply(reply_id):
    con, cur = db_connect()
    cur.execute("DELETE FROM auto_replies WHERE id = ?", (reply_id,))
    con.commit()
    con.close()

# --- دوال التعامل مع المهام المجدولة ---
def add_scheduled_task(job_id, owner_id, phones, task_type, cron_str, target=None, content=None, next_run_time=None):
    con, cur = db_connect()
    cur.execute("""
        INSERT INTO scheduled_tasks (job_id, owner_id, phones, task_type, target, content, cron_str, next_run_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
    """, (job_id, owner_id, json.dumps(phones), task_type, target, content, cron_str, next_run_time.isoformat() if next_run_time else None))
    con.commit()
    con.close()

def get_scheduled_tasks(owner_id):
    con, cur = db_connect()
    cur.execute("SELECT * FROM scheduled_tasks WHERE owner_id = ?", (owner_id,))
    tasks = cur.fetchall()
    con.close()
    return tasks

def get_all_scheduled_tasks():
    con, cur = db_connect()
    cur.execute("SELECT * FROM scheduled_tasks")
    tasks = cur.fetchall()
    con.close()
    return tasks

def remove_scheduled_task_from_db(job_id, owner_id):
    con, cur = db_connect()
    cur.execute("DELETE FROM scheduled_tasks WHERE job_id = ? AND owner_id = ?", (job_id, owner_id))
    con.commit()
    deleted = cur.rowcount > 0
    con.close()
    return deleted

def update_task_next_run(job_id, next_run_time):
    con, cur = db_connect()
    cur.execute("UPDATE scheduled_tasks SET next_run_time = ? WHERE job_id = ?", (next_run_time.isoformat() if next_run_time else None, job_id))
    con.commit()
    con.close()

def update_task_status(job_id, status: str):
    """[إضافة] تحديث حالة المهمة (active/paused)."""
    con, cur = db_connect()
    cur.execute("UPDATE scheduled_tasks SET status = ? WHERE job_id = ?", (status, job_id))
    con.commit()
    con.close()

# ==============================================================================
# ||         [جديد] دوال التشفير، IMAP، والتعامل مع الجداول الجديدة           ||
# ==============================================================================

# --- دوال التشفير ---
def encrypt_password(password: str) -> str:
    """Encrypts a password using the global key."""
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    """Decrypts a password using the global key."""
    try:
        return cipher_suite.decrypt(encrypted_password.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt password. The encryption key might have changed.")
        return "DECRYPTION_FAILED"

# ... (الكود الموجود لديك) ...
# --- دوال التعامل مع إيميلات الاستيراد ---
def add_import_email(owner_id, email_address, app_password):
    con, cur = db_connect()
    try:
        # استخدام دالة الترميز الجديدة هنا
        encrypted_pass = encrypt_email_password_base64(app_password) # <== تم التعديل
        added_date = datetime.now().isoformat()
        cur.execute(
            "INSERT INTO import_emails (owner_id, email_address, app_password_encrypted, added_date) VALUES (?, ?, ?, ?)",
            (owner_id, email_address, encrypted_pass, added_date)
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()

def get_import_emails_by_owner(owner_id):
    con, cur = db_connect()
    cur.execute("SELECT * FROM import_emails WHERE owner_id = ?", (owner_id,))
    emails = cur.fetchall()
    con.close()
    return emails

def get_import_email_by_id(email_id, owner_id): # <== أضف هذه الدالة (كانت مفقودة في الملف الأصلي)
    con, cur = db_connect()
    cur.execute("SELECT * FROM import_emails WHERE id = ? AND owner_id = ?", (email_id, owner_id))
    email_data = cur.fetchone()
    con.close()
    return email_data

def remove_import_email(email_id, owner_id):
    con, cur = db_connect()
    cur.execute("DELETE FROM import_emails WHERE id = ? AND owner_id = ?", (email_id, owner_id))
    deleted = cur.rowcount > 0
    con.commit()
    con.close()
    return deleted

# ... (بعد دالة get_import_email_by_id) ...

# --- دوال التعامل مع كلمات مرور 2FA المحفوظة (الموحدة) ---
def save_2fa_password(owner_id, phone, password, hint, recovery_email):
    con, cur = db_connect()
    # 🚨 تأكد من استخدام التشفير القوي هنا (Fernet)
    encrypted_pass = cipher_suite.encrypt(password.encode()).decode() # <== هذا هو الاستخدام الصحيح لـ Fernet
    last_updated = datetime.now().isoformat()
    cur.execute(
        """
        INSERT OR REPLACE INTO account_2fa_passwords
        (owner_id, phone, password_encrypted, hint, recovery_email, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (owner_id, phone, encrypted_pass, hint, recovery_email, last_updated)
    )
    con.commit()
    con.close()

def get_accounts_by_2fa_recovery_email(email_address: str, owner_id: int):
    """
    Finds all accounts that use a specific email as their 2FA recovery email.
    """
    con, cur = db_connect()
    # نحتاج إلى ربط جدول الحسابات بجدول كلمات مرور 2FA للحصول على النتيجة المطلوبة
    cur.execute("""
        SELECT a.phone, a.first_name, a.username 
        FROM accounts a
        JOIN account_2fa_passwords fa ON a.phone = fa.phone AND a.owner_id = fa.owner_id
        WHERE fa.recovery_email = ? AND fa.owner_id = ?
    """, (email_address, owner_id))
    accounts = cur.fetchall()
    con.close()
    return accounts


# ... (بعدها تأتي get_accounts_by_2fa_recovery_email) ...

# ==============================================================================
# ||         [جديد] دوال التشفير، IMAP، والتعامل مع الجداول الجديدة           ||
# ==============================================================================

# ... (الكود السابق مثل دوال التشفير وقاعدة البيانات) ...

# --- [حل محسن] دوال منطق IMAP لجلب الكود (لا تسبب تجميد للبوت) ---

async def check_email_credentials(email_address: str, app_password: str) -> bool:
    """
    [محسن] يتحقق من صحة بيانات تسجيل الدخول للإيميل دون تجميد البوت.
    """
    def do_check():
        try:
            # هذه العملية تعمل في خيط منفصل
            with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
                imap.login(email_address, app_password)
                return True
        except Exception as e:
            logger.warning(f"فشل التحقق من تسجيل الدخول لـ {email_address}: {e}")
            return False
            
    # تشغيل عملية التحقق في خيط منفصل لتجنب التجميد
    return await asyncio.to_thread(do_check)


async def find_telegram_code_in_gmail(email_address: str, app_password: str, timeout: int = 60) -> str | None:
    """
    [حل نهائي] يتصل بـ Gmail، يبحث عن كود تيليجرام الأحدث، ويعيده.
    هذه النسخة لا تجمد البوت وتعمل بشكل غير متزامن.
    """
    start_time = time.monotonic()
    logger.info(f"بدء البحث عن كود تيليجرام في {email_address}...")

    def do_imap_work():
        """
        هذه هي الدالة التي تحتوي على الكود الذي يسبب التجميد.
        سيتم تشغيلها في خيط منفصل بواسطة asyncio.to_thread.
        """
        try:
            with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
                imap.login(email_address, app_password)
                imap.select("inbox")

                # البحث عن رسائل غير مقروءة من تيليجرام فقط لزيادة الكفاءة
                status, messages = imap.search(None, '(UNSEEN FROM "noreply@telegram.org")')
                if status != "OK" or not messages[0]:
                    # إذا لم يتم العثور على رسائل غير مقروءة، ابحث في جميع الرسائل
                    status, messages = imap.search(None, '(FROM "noreply@telegram.org")') # <== تم التعديل: للبحث في كل الرسائل
                    if status != "OK" or not messages[0]:
                        return None # لا يوجد رسائل تطابق البحث

                message_ids = messages[0].split()
                latest_id = message_ids[-1] # الحصول على آخر رسالة

                # جلب محتوى الرسالة
                _, msg_data = imap.fetch(latest_id, "(RFC822)")
                
                # وضع علامة "مقروء" على الرسالة لمنع معالجتها مرة أخرى
                # نقوم بذلك بعد جلب المحتوى لضمان عدم وجود سباق شروط
                imap.store(latest_id, '+FLAGS', '\\Seen') # <== تم النقل إلى هنا

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        body = ""
                        # ... (كود استخراج نص الرسالة - لا تغيير) ...
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    try:
                                        body = part.get_payload(decode=True).decode()
                                        break
                                    except UnicodeDecodeError:
                                        body = part.get_payload(decode=True).decode('latin-1')
                        else:
                            try:
                                body = msg.get_payload(decode=True).decode()
                            except UnicodeDecodeError:
                                body = msg.get_payload(decode=True).decode('latin-1')

                        # 🚨🚨🚨 هنا هو التعديل الرئيسي: تعابير نمطية محسنة 🚨🚨🚨
                        code = None
                        
                        # 1. البحث عن "Your code is: XXXXXX" أو "Code: XXXXXX" (6 أرقام)
                        match = re.search(r'(?:Your code is|Code):\s*(\d{6})', body, re.IGNORECASE)
                        if match:
                            code = match.group(1)
                        
                        # 2. البحث عن "login code: XXXXX" (5 أرقام أو أكثر) - النمط القديم
                        if not code:
                            match = re.search(r'login code:\s*(\d{5,})', body, re.IGNORECASE)
                            if match:
                                code = match.group(1)

                        # 3. البحث عن 6 أرقام متتالية محاطة بحدود كلمة (أقل تحديداً ولكن قد يكون مفيداً)
                        if not code:
                            match = re.search(r'\b(\d{6})\b', body)
                            if match:
                                code = match.group(1)
                        
                        # إذا لم يتم العثور على الكود بعد محاولة كل الأنماط
                        if not code:
                            logger.debug(f"No code found with specific patterns in email body for {email_address}. Full body (first 500 chars): {body[:500]}")

                        if code:
                            logger.info(f"تم العثور على الكود {code} في {email_address}")
                            return code
        except Exception as e:
            # ... (كود معالجة الخطأ - لا تغيير) ...
            logger.error(f"خطأ أثناء العمل على IMAP في خيط منفصل لـ {email_address}: {e}")
        return None


    # حلقة المحاولة والتكرار
    while time.monotonic() - start_time < timeout:
        try:
            # هنا يتم تشغيل الدالة التي تسبب التجميد في خيط منفصل
            code = await asyncio.to_thread(do_imap_work)
            
            if code:
                return code # إذا تم العثور على الكود، قم بإرجاعه وإنهاء الدالة

            logger.info(f"لم يتم العثور على كود بعد لـ {email_address}, محاولة جديدة بعد 7 ثواني...")
            await asyncio.sleep(7)

        except Exception as e:
            logger.error(f"حدث خطأ في حلقة البحث عن الكود الرئيسية: {e}")
            await asyncio.sleep(5)
    
    logger.warning(f"انتهت مهلة البحث ({timeout} ثانية) عن الكود في {email_address} دون العثور عليه.")
    return None

# 🚨 إضافة الدالة الجديدة: جلب آخر رسالة بريد إلكتروني
async def fetch_latest_email(email_address: str, app_password: str) -> dict | None:
    """يجلب آخر رسالة بريد إلكتروني من صندوق الوارد."""
    def do_fetch():
        try:
            with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
                imap.login(email_address, app_password)
                imap.select("inbox")

                # البحث عن جميع الرسائل
                status, messages = imap.search(None, 'ALL')
                if status != "OK" or not messages[0]:
                    return None # لا توجد رسائل

                message_ids = messages[0].split()
                if not message_ids:
                    return None

                latest_id = message_ids[-1] # الحصول على آخر رسالة
                
                # جلب محتوى الرسالة بالكامل
                _, msg_data = imap.fetch(latest_id, "(RFC822)")
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # فك تشفير الموضوع والمرسل
                        subject_header = msg.get("Subject", "")
                        sender_header = msg.get("From", "")

                        decoded_subject = ''
                        if subject_header:
                            try:
                                decoded_parts = decode_header(subject_header)
                                for part, charset in decoded_parts:
                                    if isinstance(part, bytes):
                                        decoded_subject += part.decode(charset or 'utf-8', errors='ignore')
                                    else:
                                        decoded_subject += part
                            except Exception:
                                decoded_subject = subject_header # Fallback if decoding fails

                        decoded_sender = ''
                        if sender_header:
                            try:
                                decoded_parts = decode_header(sender_header)
                                for part, charset in decoded_parts:
                                    if isinstance(part, bytes):
                                        decoded_sender += part.decode(charset or 'utf-8', errors='ignore')
                                    else:
                                        decoded_sender += part
                            except Exception:
                                decoded_sender = sender_header # Fallback if decoding fails

                        # استخراج نص الرسالة
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                ctype = part.get_content_type()
                                cdisp = str(part.get('Content-Disposition'))

                                if ctype == "text/plain" and 'attachment' not in cdisp:
                                    try:
                                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                        break
                                    except UnicodeDecodeError:
                                        body = part.get_payload(decode=True).decode('latin-1', errors='ignore')
                        else:
                            try:
                                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except UnicodeDecodeError:
                                body = msg.get_payload(decode=True).decode('latin-1', errors='ignore')

                        return {
                            "from": decoded_sender,
                            "subject": decoded_subject,
                            "date": msg.get("Date"),
                            "body": body
                        }
        except Exception as e:
            logger.error(f"خطأ أثناء جلب الإيميل من {email_address}: {e}")
            raise # أعد رمي الخطأ ليتم معالجته في الدالة المتصلة
        return None

    return await asyncio.to_thread(do_fetch)
# ... (بقية الكود الموجود لديك) ...


# ==============================================================================
# ||                 رابعاً: المنطق المركزي للمهام المجدولة والردود                 ||
# ==============================================================================
async def execute_scheduled_task(bot, job_id, owner_id, phones_json, task_type, target, content):
    logger.info(f"Executing scheduled task {job_id} of type {task_type} for owner {owner_id}")
    phones = json.loads(phones_json)
    report = [f"**{_('scheduled_task_report_header', owner_id, job_id=job_id)}**\n"]
    for phone in phones:
        client = await get_telethon_client(phone, owner_id)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception(_("account_needs_login_alert", owner_id))

            if task_type == 'join':
                await client(functions.channels.JoinChannelRequest(target))
                report.append(f"✅ `{phone}`: {_('task_success', owner_id)}")
            elif task_type == 'message':
                await client.send_message(target, content)
                report.append(f"✅ `{phone}`: {_('task_success', owner_id)}")
            elif task_type == 'check':
                me = await client.get_me()
                update_account_status(phone, owner_id, 'ACTIVE', me.id, me.first_name, me.username)
                report.append(f"✅ `{phone}`: {_('task_success', owner_id)}")

            log_activity(phone, f"{_('scheduled_task', owner_id)}: {task_type}", f"{_('task_success', owner_id)} - {_('target', owner_id)}: {target}")

        except Exception as e:
            report.append(f"❌ `{phone}`: {_('task_failure', owner_id, error=e)}")
            log_activity(phone, f"{_('scheduled_task', owner_id)}: {task_type}", f"{_('failed', owner_id)}: {e}")
        finally:
            pass # The pool manager will handle disconnection
        await asyncio.sleep(2)

    job = scheduler.get_job(job_id)
    if job:
        update_task_next_run(job_id, job.next_run_time)
        try:
            final_report = "\n".join(report)
            await bot.send_message(chat_id=owner_id, text=final_report, parse_mode=constants.ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Failed to send scheduled task report to {owner_id}: {e}")

async def auto_reply_listener(client: TelegramClient, owner_id: int):
    if not hasattr(client, 'on'):
        logger.error(f"Telethon client for owner {owner_id} does not have 'on' attribute.")
        return

    me = await client.get_me()
    phone = f"+{me.phone}"
    replies = get_auto_replies(owner_id, phone)
    keyword_map = {r['keyword']: r['response'] for r in replies}
    if not keyword_map: return

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if not event.is_private or event.sender.bot:
            return
        
        message_text = event.raw_text.lower()
        for keyword, response in keyword_map.items():
            if keyword in message_text:
                await asyncio.sleep(2)
                await event.reply(response)
                log_activity(phone, _("auto_reply", owner_id), _("replied_to", owner_id, keyword=keyword, user_id=event.sender_id))
                break

async def start_client_for_autoreply(phone, owner_id):
    client = await get_telethon_client(phone, owner_id)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(f"Client for {phone} not authorized, skipping auto-reply.")
            return

        logger.info(f"Auto-reply listener started for {phone}.")
        await auto_reply_listener(client, owner_id)
        while client.is_connected() and await client.is_user_authorized():
            await asyncio.sleep(60)

    except Exception as e:
        logger.error(f"Error in auto-reply client for {phone}: {e}")
        pass

async def load_and_run_background_tasks(bot: "Application.bot"):
    logger.info(_("loading_scheduled_tasks", 0))
    tasks = get_all_scheduled_tasks()
    for task in tasks:
        job_id = task['job_id']
        try:
            scheduler.add_job(
                execute_scheduled_task,
                CronTrigger.from_crontab(task['cron_str'], timezone="Asia/Damascus"),
                id=job_id,
                name=f"Task {job_id} for {task['owner_id']}",
                args=[bot, task['job_id'], task['owner_id'], task['phones'], task['task_type'], task['target'], task['content']],
                replace_existing=True
            )
            if task['status'] == 'paused':
                scheduler.pause_job(job_id)
        except Exception as e:
            logger.error(_("failed_to_load_scheduled_task", 0, job_id=job_id, error=e))
    logger.info(_('loaded_scheduled_tasks_count', 0, count=len(scheduler.get_jobs())))

    try:
        scheduler.add_job(
            admin_smart_notifications,
            'cron', day_of_week='*', hour=9,
            id='admin_smart_notifications_job',
            args=[bot],
            replace_existing=True
        )
        logger.info(_("scheduled_daily_smart_notifications", 0))
    except Exception as e:
        logger.error(_('failed_to_schedule_smart_notifications', 0, error=e))

    try:
        scheduler.add_job(
            cleanup_telethon_client_pool,
            'interval', minutes=CLIENT_TIMEOUT_SECONDS // 60,
            id='telethon_client_pool_cleanup',
            replace_existing=True
        )
        logger.info(_("scheduled_client_pool_cleanup", 0))
    except Exception as e:
        logger.error(_('failed_to_schedule_client_pool_cleanup', 0, error=e))

    logger.info(_("auto_reply_listeners_info", 0))

async def cleanup_telethon_client_pool():
    logger.info("Starting Telethon client pool cleanup...")
    current_time = time.monotonic()
    keys_to_remove = []

    for key, data in list(CLIENT_POOL.items()):
        client = data['client']
        last_used = data['last_used_monotonic']
        
        if client and client.is_connected():
            if (current_time - last_used) > CLIENT_TIMEOUT_SECONDS:
                try:
                    await client.disconnect()
                    logger.info(f"Disconnected idle client: {key[0]} (owner: {key[1]})")
                except Exception as e:
                    logger.error(f"Error disconnecting client {key[0]}: {e}")
                keys_to_remove.append(key)
        else:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        if key in CLIENT_POOL:
            del CLIENT_POOL[key]
    
    logger.info(f"Telethon client pool cleanup finished. Remaining clients: {len(CLIENT_POOL)}")


# ==============================================================================
# ||                   خامساً: الدوال المساعدة والأدوات (Utilities)              ||
# ==============================================================================
async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def is_authorized_user(user_id: int) -> bool:
    if await is_admin(user_id):
        return True
    sub = get_subscriber(user_id)
    if sub:
        try:
            end_date = datetime.fromisoformat(sub['end_date'])
            if end_date > datetime.now():
                return True
        except (ValueError, TypeError):
             logger.error(f"Could not parse end_date for user {user_id}: {sub['end_date']}")
             return False
    return False

# ... (الكود الموجود لديك) ...
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Safely navigates back to the previous state in the conversation stack
    by mocking the expected update type.
    """
    query = update.callback_query
    # نجيب على الكويري أولاً إذا كان موجوداً
    if query:
        await query.answer()

    state_stack = context.user_data.get('state_stack', deque(maxlen=10))
    
    # نتأكد من وجود حالة سابقة للرجوع إليها
    if len(state_stack) > 1:
        state_stack.pop()  # نحذف الحالة الحالية
        handler_func, mock_data = state_stack[-1]  # نأخذ الحالة التي قبلها
        
        # هذا هو الجزء الأهم:
        # نستخدم دالة المحاكاة لضمان بناء كائن التحديث بشكل صحيح وآمن
        # وتجنب التعارض بين الرسائل النصية وضغطات الأزرار.
        return await mock_update_and_call(handler_func, update, context, mock_data, push=False)
    else:
        # إذا لم يكن هناك مكان للرجوع إليه، نعود للقائمة الرئيسية
        return await back_to_main_menu(update, context)
# ... (بقية الكود الموجود لديك) ...


async def send_admin_notification(context: ContextTypes.DEFAULT_TYPE, message: str):
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=message, parse_mode=constants.ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(_("failed_to_send_admin_notification", 0, admin_id=admin_id, error=e))

def create_paginated_keyboard(buttons, page, page_size, callback_prefix, total_items, user_id):
    start_index = page * page_size
    end_index = start_index + page_size
    keyboard = [buttons[i:i + 2] for i in range(start_index, min(end_index, len(buttons)), 2)]
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ " + _("previous", user_id), callback_data=f"{callback_prefix}:{page-1}"))
    total_pages = math.ceil(total_items / page_size)
    if total_pages > 1:
        nav_buttons.append(InlineKeyboardButton(_("log_page", user_id, current_page=page + 1, total_pages=total_pages), callback_data="noop"))
    if end_index < len(buttons):
        nav_buttons.append(InlineKeyboardButton(_("next", user_id) + " ➡️", callback_data=f"{callback_prefix}:{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    return keyboard

async def get_telethon_client(phone: str, owner_id: int, session_string: str = None) -> TelegramClient:
    key = (phone, owner_id)
    # Check if a valid, connected client is already in the pool
    if CLIENT_POOL[key]['client'] and CLIENT_POOL[key]['client'].is_connected():
        # Check if the client was used recently
        if (time.monotonic() - CLIENT_POOL[key]['last_used_monotonic']) < CLIENT_TIMEOUT_SECONDS:
            CLIENT_POOL[key]['last_used_monotonic'] = time.monotonic()
            logger.debug(f"Re-using client from pool for {phone}.")
            return CLIENT_POOL[key]['client']
        else: # Client timed out, disconnect and remove
            try:
                await CLIENT_POOL[key]['client'].disconnect()
                logger.info(f"Disconnected timed-out client: {phone}.")
            except Exception as e:
                logger.error(f"Error disconnecting timed-out client {phone}: {e}")
            del CLIENT_POOL[key]

    # If no valid client in pool, create a new one
    if session_string:
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    else:
        session_path = os.path.join(SESSIONS_DIR, f"{owner_id}_{phone}.session")
        account = get_account_by_phone(phone, owner_id)
        proxy_info = None
        if account and account['proxy_id']:
            proxy_db = get_proxy_by_id(account['proxy_id'])
            if proxy_db:
                proxy_info = (proxy_db['protocol'], proxy_db['hostname'], proxy_db['port'], True, proxy_db['username'], proxy_db['password'])
        
        client = TelegramClient(SQLiteSession(session_path), API_ID, API_HASH, proxy=proxy_info, connection_retries=2)
    
    # Add the new client to the pool
    CLIENT_POOL[key]['client'] = client
    CLIENT_POOL[key]['last_used_monotonic'] = time.monotonic()
    logger.debug(f"Created new client for {phone} and added to pool.")
    return client

async def cleanup_conversation(context: ContextTypes.DEFAULT_TYPE):
    # Keep essential keys, especially for pagination and navigation
    keys_to_keep = {'account_page', 'proxy_page', 'log_page', 'state_stack', 'selected_accounts', 'selected_phone'}
    user_data_keys = list(context.user_data.keys())
    for key in user_data_keys:
        if key not in keys_to_keep:
            del context.user_data[key]

async def push_state(context: ContextTypes.DEFAULT_TYPE, handler, mock_data):
    if 'state_stack' not in context.user_data:
        context.user_data['state_stack'] = deque(maxlen=10)
    context.user_data['state_stack'].append((handler, mock_data))

async def mock_update_and_call(handler_func, original_update, context: ContextTypes.DEFAULT_TYPE, new_callback_data, push=True):
    if push:
        await push_state(context, handler_func, new_callback_data)

    # <== تم الإصلاح: التعامل مع /start بشكل خاص لمنع التكرار اللانهائي أو الأخطاء
    if handler_func.__name__ == 'start_command':
        return await back_to_main_menu(original_update, context)

    # <== تم الإصلاح: توحيد طريقة الحصول على الرسالة لزيادة الموثوقية
    message = original_update.effective_message
    if not message:
        message = Mock()
        message.chat_id = original_update.effective_chat.id
        message.message_id = None # Important to avoid errors on edit

    mock_update = Mock(spec=Update)
    mock_update.effective_user = original_update.effective_user
    mock_update.effective_chat = original_update.effective_chat
    mock_update.effective_message = message # استخدام الرسالة الموحدة

    mock_callback_query = Mock(spec=CallbackQuery)
    mock_callback_query.data = new_callback_data
    mock_callback_query.message = message
    mock_callback_query.from_user = original_update.effective_user

    async def mock_answer(*args, **kwargs): pass
    mock_callback_query.answer = mock_answer
    
    # Attach bot methods for editing messages
    mock_callback_query.edit_message_text = context.bot.edit_message_text
    mock_callback_query.edit_message_reply_markup = context.bot.edit_message_reply_markup

    mock_update.callback_query = mock_callback_query
    return await handler_func(mock_update, context)

async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if not message: return ConversationHandler.END

    user_id = update.effective_user.id
    await message.reply_text(_("action_cancelled", user_id))
    
    await cleanup_conversation(context)
    context.user_data.clear() # Clear all user data on full cancel
    
    await message.chat.send_message(
        text=_("main_menu_return", user_id),
        reply_markup=await get_main_keyboard(user_id)
    )
    return ConversationHandler.END

# <== تم الإصلاح: دالة إلغاء جديدة للعودة إلى قائمة إدارة الحساب
async def cancel_to_account_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the sub-operation and returns to the specific account management menu."""
    user_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    
    await update.message.reply_text(_("action_cancelled", user_id))
    
    if not phone:
        return await back_to_main_menu(update, context)

    # Re-show the account management menu
    text, reply_markup = await _get_account_management_payload(phone, user_id, context)
    
    if reply_markup:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    return MANAGE_ACCOUNT

async def cancel_bulk_selection_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current sub-step and returns to the account selection screen for the same bulk action."""
    query = update.callback_query
    await query.answer() # لا نحتاج لعرض رسالة، فهو مجرد انتقال للخلف
    
    # --- هذا هو التعديل ---
    # بدلاً من تنظيف السياق والعودة لقائمة المهام،
    # نقوم فقط بإعادة استدعاء دالة اختيار الحسابات.
    # هذه الدالة ستستخدم البيانات المحفوظة في الـ context لتعيد عرض الشاشة كما كانت.
    return await select_accounts_for_bulk_action(update, context)
    # --- نهاية التعديل ---

    
async def back_to_delete_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """A specific back button that returns to the bulk delete options menu."""
    query = update.callback_query
    await query.answer()
    if context.user_data.get('state_stack') and len(context.user_data['state_stack']) > 0:
        context.user_data['state_stack'].pop()
    return await bulk_delete_options(update, context)
    
async def progress_updater(message, total_items, current_item, text_prefix, user_id):
    if total_items > 0 and (current_item % 5 == 0 or current_item == total_items):
        try:
            percentage = (current_item / total_items) * 100
            bar_length = 10
            filled_length = int(bar_length * current_item // total_items)
            bar = '█' * filled_length + '─' * (bar_length - filled_length)
            
            await message.edit_text(
                f"{text_prefix}\n\n`{bar}`\n`{current_item} / {total_items}` ({percentage:.1f}%)",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            await asyncio.sleep(0.5)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.warning(f"Progress update failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in progress_updater: {e}")
    elif total_items == 0:
        try:
            await message.edit_text(f"{text_prefix}\n\n`0 / 0` (0%)", parse_mode=constants.ParseMode.MARKDOWN)
            await asyncio.sleep(0.5)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.warning(f"Progress update failed: {e}")

def format_bytes(byte_count):
    """Converts bytes to a human-readable format (GB or MB)."""
    if byte_count is None:
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while byte_count >= power and n < len(power_labels) - 1:
        byte_count /= power
        n += 1
    return f"{byte_count:.1f} {power_labels[n]}"

async def handle_login_success_message(update: Update, context: ContextTypes.DEFAULT_TYPE, newly_logged_in_phone: str, first_name: str):
    """Handles sending the correct success message after a login/relogin."""
    owner_id = update.effective_user.id
    # استخراج الرقم الذي كان يحتاج تسجيل دخول، ثم حذفه من الذاكرة
    phone_needing_relogin = context.user_data.pop('phone_needing_relogin', None)
    
    reply_text = ""
    message_to_reply = update.message or update.callback_query.message

    # إذا كانت العملية هي "إعادة تسجيل دخول"
    if phone_needing_relogin:
        # إذا كان الرقم المدخل هو نفس الرقم المطلوب
        if newly_logged_in_phone == phone_needing_relogin:
            reply_text = _("relogin_success", owner_id, phone=newly_logged_in_phone)
        # إذا أدخل المستخدم رقماً مختلفاً
        else:
            reply_text = _("relogin_flow_new_account_added", owner_id, new_phone=newly_logged_in_phone, old_phone=phone_needing_relogin)
    # إذا كانت العملية هي "إضافة حساب" عادية
    else:
        reply_text = _("login_success", owner_id, first_name=first_name)
    
    await message_to_reply.reply_text(reply_text)



# ==============================================================================
# ||                         سادساً: لوحات المفاتيح الرئيسية                     ||
# ==============================================================================
async def get_main_keyboard(user_id: int):
    keyboard = [
        [
            InlineKeyboardButton(_("add_account_button_main", user_id), callback_data='add_account_start'),
            InlineKeyboardButton(_("remove_account_button_main", user_id), callback_data='unified_bulk:deleter_start')
        ],
        # <== تم التعديل: هذا الزر الآن يفتح قائمة الخيارات الجديدة
        [InlineKeyboardButton(_("manage_accounts_button_main", user_id), callback_data='show_management_options')],
        [InlineKeyboardButton(_("scheduled_tasks_button_main", user_id), callback_data='scheduler_menu_start')],
        [InlineKeyboardButton(_("manage_proxies_button_main", user_id), callback_data='manage_proxies_start:0')],
             [InlineKeyboardButton(_("manage_import_emails_button_main", user_id), callback_data='manage_emails_start')],
        [InlineKeyboardButton(_("check_accounts_button_main", user_id), callback_data='check_accounts_start'), InlineKeyboardButton(_("dashboard_button_main", user_id), callback_data='dashboard')],
        [InlineKeyboardButton(_("extraction_section_button_main", user_id), callback_data='scraper_menu'), InlineKeyboardButton(_("export_csv_button_main", user_id), callback_data='export_csv')],
        
        [InlineKeyboardButton(_("contact_dev_button_main", user_id), url=f"https://t.me/{DEV_USERNAME}")]
    ]
    if await is_admin(user_id):
        keyboard.insert(0, [InlineKeyboardButton(_("admin_panel_button_main", user_id), callback_data='bot_admin_menu')])
    return InlineKeyboardMarkup(keyboard)

def get_automation_keyboard(user_id: int):
    keyboard = [
        # الصف الأول: الانضمام والمغادرة
        [InlineKeyboardButton(_("join_bulk_button", user_id), callback_data='unified_bulk:joiner'),
         InlineKeyboardButton(_("leave_bulk_button", user_id), callback_data='unified_bulk:leaver')],

        # الصف الثاني: 2FA والمنظف
        [InlineKeyboardButton(_("bulk_2fa_button", user_id), callback_data='unified_bulk:bulk_2fa'),
         InlineKeyboardButton(_("cleaner_button", user_id), callback_data='unified_bulk:cleaner')],

        # الصف الثالث: تسجيل الخروج وإعادة تعيين الجلسات
        [InlineKeyboardButton(_("logout_bulk_button", user_id), callback_data='unified_bulk:logout'),
         InlineKeyboardButton(_("bulk_reset_sessions_button", user_id), callback_data='unified_bulk:reset_sessions')],
        
        # الصف الرابع: تغيير الاسم والنبذة
        [InlineKeyboardButton(_("bulk_name_button", user_id), callback_data='unified_bulk:bulk_name'),
         InlineKeyboardButton(_("bulk_bio_button", user_id), callback_data='unified_bulk:bulk_bio')],
        
        # الصف الخامس: تغيير الصورة ونشر القصص
        [InlineKeyboardButton(_("bulk_photo_button", user_id), callback_data='unified_bulk:bulk_photo'),
         InlineKeyboardButton(_("bulk_post_story_button", user_id), callback_data='unified_bulk:bulk_story')],

        # الصف السادس: إدارة جهات الاتصال (إضافة وحذف)
        [InlineKeyboardButton(_("bulk_add_contacts_button", user_id), callback_data='unified_bulk:add_contacts'),
         InlineKeyboardButton(_("bulk_delete_contacts_button", user_id), callback_data='unified_bulk:delete_contacts')],

        # الصف السابع: تصدير جهات الاتصال والجلسات
        [InlineKeyboardButton(_("export_contacts_button", user_id), callback_data='unified_bulk:export_contacts'),
         InlineKeyboardButton(_("bulk_export_button_main", user_id), callback_data='unified_bulk:bulk_export')],
        
        # الصف الثامن: تعيين البروكسي (يمكن أن يكون وحيداً أو مع زر آخر مستقبلاً)
        [InlineKeyboardButton(_("bulk_proxy_assign_button", user_id), callback_data='unified_bulk:bulk_proxy')],

        # زر الرجوع لقائمة الإدارة (فردي/جماعي)
        # 🚨 التعديل هنا 🚨
        [InlineKeyboardButton(_("back_to_main_menu", user_id), callback_data='show_management_options')] # <== تغيير هنا

    ]
    return InlineKeyboardMarkup(keyboard)

# ... (الكود الموجود لديك) ...
def get_scraper_keyboard(user_id: int):
    keyboard = [
        [InlineKeyboardButton(_("extract_members_button", user_id), callback_data='unified_bulk:members')],
        # 🚨 التعديل هنا 🚨
        [InlineKeyboardButton(_("back_to_main_menu", user_id), callback_data='show_management_options')] # <== تغيير هنا
    ]
    return InlineKeyboardMarkup(keyboard)
# ... (بقية الكود الموجود لديك) ...


# <== تم التعديل: دالة جديدة لعرض خيارات الإدارة (فردي/جماعي)
async def show_management_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the choice between single and bulk account management."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    keyboard = [[
        InlineKeyboardButton(_("bulk_management_button", user_id), callback_data="show_bulk_action_options"),
        InlineKeyboardButton(_("single_management_button", user_id), callback_data="manage_accounts_start:0")
    ]]
    keyboard.append([InlineKeyboardButton(_("back_to_main_menu", user_id), callback_data="back_to_main")])
    
    await query.message.edit_text(
        text=_("management_options_title", user_id),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# <== تم التعديل: دالة جديدة لعرض قائمة المهام الجماعية
async def show_bulk_action_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the menu of available bulk actions."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    await query.message.edit_text(
        _("bulk_actions_menu_title", user_id),
        reply_markup=get_automation_keyboard(user_id)
    )

# ==============================================================================
# ||                         سابعاً: معالجات الأوامر الرئيسية                    ||
# ==============================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the /start command.
    If the user is new, it starts the language selection conversation.
    Otherwise, it shows the appropriate menu.
    """
    user = update.effective_user
    user_id = user.id

    # إذا كان المستخدم جديداً تماماً (لا لغة مسجلة له)، نبدأ محادثة اختيار اللغة
    if get_user_language(user_id) is None:
        await choose_language(update, context)
        return LANG_SELECT # ننتقل إلى حالة انتظار اختيار اللغة

    # إذا كان المستخدم قديماً، نتحقق من اشتراكه
    if not await is_authorized_user(user_id):
        keyboard = [
            [InlineKeyboardButton(_("check_sub_status_button", user_id), callback_data='check_subscription_status')],
            [InlineKeyboardButton(_("contact_dev_button", user_id), url=f"https://t.me/{DEV_USERNAME}")]
        ]
        await update.message.reply_text(
            _("not_authorized", user_id),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END # ننهي المحادثة

    # إذا كان المستخدم قديماً ومشتركاً، نعرض القائمة الرئيسية
    context.user_data['state_stack'] = deque(maxlen=10)
    await push_state(context, start_command, 'main_menu_dummy_data')

    await update.message.reply_text(
        _("welcome_message", user_id, user_mention=user.mention_html()),
        reply_markup=await get_main_keyboard(user_id),
        parse_mode=constants.ParseMode.HTML
    )
    return ConversationHandler.END # ننهي المحادثة



async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts the user to choose a language."""
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("العربية 🇸🇾", callback_data='set_lang:ar')],
        [InlineKeyboardButton("English 🇬🇧", callback_data='set_lang:en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # تحديد إذا كانت رسالة جديدة أو تعديل لرسالة قديمة
    message = update.callback_query.message if update.callback_query else update.message

    if update.callback_query:
        await update.callback_query.answer()
        await message.edit_text(_("choose_language", user_id), reply_markup=reply_markup)
    else:
        await message.reply_text(_("choose_language", user_id), reply_markup=reply_markup)

    return LANG_SELECT # الانتقال إلى حالة انتظار اختيار اللغة



async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sets the user's language and then checks for authorization."""
    query = update.callback_query
    user_id = query.from_user.id
    selected_lang = query.data.split(':')[1]

    try:
        # نقوم بتحديث اللغة (فقط إذا كان المستخدم مشتركاً قديماً)
        set_user_language(user_id, selected_lang)
        
        # نستخدم اللغة التي اختارها للتو لإظهار رسالة التأكيد
        await query.answer(LANGUAGE_DATA[selected_lang]["language_set_success"], show_alert=True)
        await query.message.delete()

        # الآن، نفحص إذا كان المستخدم مشتركاً أم لا
        if await is_authorized_user(user_id):
            # إذا كان مشتركاً، نعرض له القائمة الرئيسية
            await context.bot.send_message(
                chat_id=user_id,
                text=_( "welcome_message", user_id, user_mention=query.from_user.mention_html()),
                reply_markup=await get_main_keyboard(user_id),
                parse_mode=constants.ParseMode.HTML
            )
        else:
            # إذا لم يكن مشتركاً، نعرض له رسالة الاشتراك باللغة التي اختارها
            keyboard = [
                [InlineKeyboardButton(LANGUAGE_DATA[selected_lang]["check_sub_status_button"], callback_data='check_subscription_status')],
                [InlineKeyboardButton(LANGUAGE_DATA[selected_lang]["contact_dev_button"], url=f"https://t.me/{DEV_USERNAME}")]
            ]
            await context.bot.send_message(
                chat_id=user_id,
                text=LANGUAGE_DATA[selected_lang]["not_authorized"],
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error setting language for user {user_id}: {e}")
        await query.answer("Error setting language.", show_alert=True)
        return ConversationHandler.END


async def check_subscription_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    sub = get_subscriber(user_id)
    if sub:
        end_date = datetime.fromisoformat(sub['end_date'])
        if end_date > datetime.now():
            await query.answer(_("subscription_active", user_id, end_date=end_date.strftime('%Y-%m-%d')), show_alert=True)
        else:
            await query.answer(_("subscription_expired", user_id), show_alert=True)
    else:
        await query.answer(_("not_subscribed", user_id), show_alert=True)


# ... (الكود الموجود لديك) ...
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    context.user_data.clear()
    context.user_data['state_stack'] = deque(maxlen=10)

    message_to_use = query.message if query else update.message
    try:
        await message_to_use.edit_text(
            text=_("returned_to_main_menu", user_id), # <--- تم التغيير هنا
            reply_markup=await get_main_keyboard(user_id)
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
             logger.info(f"Could not edit message on back_to_main, sending new one: {e}")
             await update.effective_chat.send_message(
                text=_("returned_to_main_menu", user_id), # <--- تم التغيير هنا
                reply_markup=await get_main_keyboard(user_id)
             )
    except Exception as e:
        logger.info(f"Could not edit message on back_to_main, sending new one: {e}")
        await update.effective_chat.send_message(
            text=_("returned_to_main_menu", user_id), # <--- تم التغيير هنا
            reply_markup=await get_main_keyboard(user_id)
        )

    return ConversationHandler.END
# ... (بقية الكود الموجود لديك) ...


async def show_scraper_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    await push_state(context, show_scraper_menu, 'scraper_menu')
    await query.message.edit_text(_("scraper_menu_title", user_id), reply_markup=get_scraper_keyboard(user_id))


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    msg = await query.message.edit_text(
        f"⏳ {_('loading_dashboard', user_id)}",
        parse_mode=constants.ParseMode.MARKDOWN
    )

    await push_state(context, dashboard, 'dashboard')

    con, cur = db_connect()

    cur.execute("SELECT status, COUNT(*) FROM accounts WHERE owner_id = ? GROUP BY status", (user_id,))
    status_counts = {row['status']: row['COUNT(*)'] for row in cur.fetchall()}

    cur.execute("SELECT COUNT(*) FROM proxies")
    total_proxies = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM proxies WHERE usage_count > 0")
    used_proxies = cur.fetchone()[0] or 0

    total_accounts = sum(status_counts.values())
    active = status_counts.get('ACTIVE', 0)
    banned = status_counts.get('BANNED', 0)
    needs_login = status_counts.get('NEEDS_LOGIN', 0)
    unknown = status_counts.get('UNKNOWN', 0)

    text = (_("dashboard_title", user_id) + "\n\n"
            + _("account_stats_header", user_id, total=total_accounts) + "\n"
            + f"   - 🟢 {_('status_active', user_id)}: `{active}`\n"
            + f"   - 🔴 {_('status_banned', user_id)}: `{banned}`\n"
            + f"   - 🟡 {_('status_needs_login', user_id)}: `{needs_login}`\n"
            + f"   - ❓ {_('status_unknown', user_id)}: `{unknown}`\n\n"
            + _("proxy_stats_header", user_id) + "\n"
            + f"   - {_('total_proxies', user_id)}: `{total_proxies}`\n"
            + f"   - {_('used_proxies', user_id)}: `{used_proxies}`\n"
            )

    if await is_admin(user_id):
        cur.execute("SELECT COUNT(*) FROM subscribers WHERE end_date > ?", (datetime.now().isoformat(),))
        active_subs = cur.fetchone()[0] or 0
        text += (_("admin_stats_header", user_id) + "\n"
                 + _("active_subs_count", user_id, active_subs=active_subs) + "\n")

    con.close()

    keyboard = [[InlineKeyboardButton(_("refresh_button", user_id), callback_data='dashboard'), InlineKeyboardButton(_("go_back_button", user_id), callback_data='back_to_main')]]

    await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)

async def start_relogin_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the phone that needs relogin and starts the add account flow."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    # استخراج الرقم من زر الكول باك وحفظه في ذاكرة المحادثة
    phone_to_relogin = query.data.split(':')[1]
    context.user_data['phone_needing_relogin'] = phone_to_relogin
    
    # عرض تعليمات تسجيل الدخول للمستخدم
    await push_state(context, add_account_start, 'add_account_start')
    keyboard = [[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]
    await query.message.edit_text(
        text=_("add_account_instructions", user_id),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    # الانتقال إلى حالة انتظار إدخال المستخدم (رقم، جلسة، ملف)
    return ADD_AWAIT_INPUT


# ==============================================================================
# ||                       ثامناً: قسم إضافة حساب جديد                          ||
# ==============================================================================
async def add_account_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    await push_state(context, add_account_start, 'add_account_start')
    keyboard = [[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]
    await query.message.edit_text(
        text=_("add_account_instructions", user_id),
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN
    )
    return ADD_AWAIT_INPUT


async def add_process_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = update.effective_user.id

    if re.match(r'^\+\d{10,}$', text):
        return await add_process_phone(update, context, text)
    elif len(text) > 150: # Session strings are long
        return await add_process_string_session(update, context, text)
    else:
        await update.message.reply_text(_("invalid_input_format", user_id))
        return ADD_AWAIT_INPUT

async def add_process_session_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    doc = update.message.document
    owner_id = update.effective_user.id
    user_id = owner_id

    if not doc or not doc.file_name.endswith('.session'):
        await update.message.reply_text(_("invalid_session_file", user_id))
        return ADD_AWAIT_INPUT

    msg = await update.message.reply_text(_("session_file_received", user_id))

    temp_path = os.path.join(SESSIONS_DIR, f"temp_{owner_id}_{doc.file_id}.session")
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(temp_path)

    client_temp = TelegramClient(SQLiteSession(temp_path), API_ID, API_HASH)

    try:
        await client_temp.connect()
        if not await client_temp.is_user_authorized():
            raise AuthKeyUnregisteredError

        me = await client_temp.get_me()
        phone = f"+{me.phone}"

        result = await client_temp(functions.account.GetAuthorizationsRequest())
        my_auth = next((auth for auth in result.authorizations if auth.hash == 0), None)

        creation_date_str = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        if my_auth and my_auth.date_created:
            local_timezone = pytz.timezone("Asia/Damascus")
            created_dt = my_auth.date_created.astimezone(local_timezone)
            creation_date_str = created_dt.strftime('%Y-%m-%d %I:%M:%S %p')

        await client_temp.disconnect()

        final_path = os.path.join(SESSIONS_DIR, f"{owner_id}_{phone}.session")
        journal_path = f"{final_path}-journal"

        if os.path.exists(final_path): os.remove(final_path)
        if os.path.exists(journal_path): os.remove(journal_path)
        shutil.move(temp_path, final_path)

        add_account_to_db(phone, owner_id, me.id, me.first_name, me.username, 'ACTIVE', add_method=_("session_file_add_method", user_id), creation_date=creation_date_str)
        log_activity(phone, _("add_account", owner_id), _("add_via_session_file_success", owner_id))
        
        await handle_login_success_message(update, context, phone, me.first_name)

        
        await get_telethon_client(phone, owner_id)
        await check_single_account_logic(phone, owner_id, context, is_new_account=True)

    # <== تم الإصلاح: معالجة خطأ استخدام الجلسة من مكانين
    except AuthKeyDuplicatedError:
        await msg.edit_text(_("session_key_duplicated_error", user_id))
    except (AuthKeyUnregisteredError, TypeError, ValueError):
        await msg.edit_text(_("session_processing_failed", user_id))
    except Exception as e:
        logger.error(f"Failed to process session file: {e}", exc_info=True)
        await msg.edit_text(_("unexpected_error", user_id, error=e), parse_mode=constants.ParseMode.MARKDOWN)
    finally:
        if client_temp and client_temp.is_connected():
            await client_temp.disconnect()
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as rem_e:
                logger.error(f"Failed to remove temp session file '{temp_path}': {rem_e}")

    await cleanup_conversation(context)
    return ConversationHandler.END


async def add_process_phone(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str) -> int:
    context.user_data['phone'] = phone
    owner_id = update.effective_user.id
    user_id = owner_id

    # --- بداية التعديل: منطق التحقق النهائي ---
    existing_account = get_account_by_phone(phone, owner_id)
    phone_to_relogin = context.user_data.get('phone_needing_relogin')

    # سيتم منع المتابعة إذا كان الحساب موجوداً بالفعل
    if existing_account:
        # الشرط الوحيد للمتابعة هو أن يكون المستخدم في "عملية إعادة تسجيل دخول" وأن يكون الرقم المُدخل هو نفسه الرقم المطلوب
        # إذا لم يتحقق هذا الشرط، سيتم إظهار رسالة الخطأ
        if phone_to_relogin is None or phone != phone_to_relogin:
            await update.message.reply_text(_("account_already_exists_for_user", owner_id))
            await cleanup_conversation(context)
            return ConversationHandler.END
    # --- نهاية التعديل ---

    client = await get_telethon_client(phone, owner_id)
    context.user_data['client'] = client
    try:
        await client.connect()
        # عند إعادة الدخول، سيتم تحديث بيانات الحساب الموجود أصلاً في قاعدة البيانات
        creation_date_str = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        add_account_to_db(phone, owner_id, add_method=_("phone_number_add_method", user_id), creation_date=creation_date_str)
        sent_code = await client.send_code_request(phone)
        context.user_data['phone_code_hash'] = sent_code.phone_code_hash
        await update.message.reply_text(_("phone_code_sent", user_id))
        return ADD_CODE
    except FloodWaitError as e:
        await update.message.reply_text(_("flood_wait_error", user_id, seconds=e.seconds))
        return ConversationHandler.END
    except (PhoneNumberBannedError, UserDeactivatedBanError):
        await update.message.reply_text(_("phone_banned_error", user_id))
        update_account_status(phone, owner_id, 'BANNED')
        await send_admin_notification(context, _("account_banned_admin_alert", 0, phone=phone))
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(_("unexpected_error", user_id, error=e))
        return ConversationHandler.END



async def add_process_string_session(update: Update, context: ContextTypes.DEFAULT_TYPE, session_string: str) -> int:
    user_id = update.effective_user.id
    msg = await update.message.reply_text(_("string_session_checking", user_id))
    owner_id = update.effective_user.id

    client_temp = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    
    try:
        await client_temp.connect()
        if not await client_temp.is_user_authorized():
            await msg.edit_text(_("string_session_invalid", user_id))
            return ConversationHandler.END
        
        me = await client_temp.get_me()
        phone = f"+{me.phone}"

        session_file_path = os.path.join(SESSIONS_DIR, f'{owner_id}_{phone}.session')
        
        # Disconnect before creating the new session to avoid file lock issues
        await client_temp.disconnect() 

        # Create a new SQLite session and save the auth key from the string session
        new_sqlite_session = SQLiteSession(session_file_path)
        temp_client_for_save = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await temp_client_for_save.connect()
        new_sqlite_session.set_dc(temp_client_for_save.session.dc_id, temp_client_for_save.session.server_address, temp_client_for_save.session.port)
        new_sqlite_session.auth_key = temp_client_for_save.session.auth_key
        new_sqlite_session.save()
        await temp_client_for_save.disconnect()
        
        creation_date_str = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        add_account_to_db(phone, owner_id, me.id, me.first_name, me.username, 'ACTIVE', add_method=_("string_session_add_method", user_id), creation_date=creation_date_str)
        log_activity(phone, _("add_account", owner_id), _("add_via_string_session_success", owner_id))
        await handle_login_success_message(update, context, phone, me.first_name)

        # Ensure the client pool is updated
        await get_telethon_client(phone, owner_id)
        await check_single_account_logic(phone, owner_id, context, is_new_account=True)
    except Exception as e:
        await msg.edit_text(_("unexpected_error", user_id, error=e))
    finally:
        pass

    await cleanup_conversation(context)
    return ConversationHandler.END


async def add_get_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw_input = update.message.text
    extracted_code = None

    # --- تعديل 1: جعل الاستخراج يفهم الفراغات ---
    # نزيل كل شيء ليس رقماً من الإدخال
    digits_only = re.sub(r'\D', '', raw_input)
    
    # نتحقق إذا كان لدينا 5 أرقام أو أكثر
    if len(digits_only) >= 5:
        extracted_code = digits_only
    # --- نهاية تعديل 1 ---

    if not extracted_code:
        await update.message.reply_text("لم أتمكن من استخراج الكود. يرجى إرسال الكود المكون من 5 أرقام فقط أو قم بإعادة توجيه الرسالة من تيليجرام.")
        return ADD_CODE

    # نقوم بتنسيق الكود النظيف مع الفراغات دائماً
    formatted_code = " ".join(extracted_code)
    
    phone = context.user_data['phone']
    owner_id = update.effective_user.id
    user_id = owner_id
    client: TelegramClient = context.user_data['client']
    
    # --- تعديل 2: تم إلغاء التأخير ورسالة الانتظار ---
    
    msg = await update.message.reply_text(f"⏳ جارٍ استخدام الكود `{formatted_code}`...")
    try:
        await client.sign_in(phone, formatted_code, phone_code_hash=context.user_data['phone_code_hash'])
        await msg.delete()

    except SessionPasswordNeededError:
        await msg.delete()
        await update.message.reply_text(_("account_needs_password", user_id))
        return ADD_PASSWORD
        
    # --- بداية تعديل 3: تحسين رسائل الخطأ ---
    except PhoneCodeInvalidError:
        await msg.delete()
        await update.message.reply_text(_("login_code_error_generic", user_id), parse_mode=constants.ParseMode.MARKDOWN)
        return ADD_CODE # نعود لحالة إدخال الكود ليتمكن المستخدم من المحاولة مجدداً
        
    except Exception as e:
        await msg.delete()
        error_str = str(e).lower()
        # إذا كان الخطأ هو انتهاء صلاحية الكود، نعرض رسالتنا المخصصة
        if "code has expired" in error_str:
            await update.message.reply_text(_("login_code_error_generic", user_id), parse_mode=constants.ParseMode.MARKDOWN)
            return ADD_CODE # نعود لحالة إدخال الكود
        else:
            # لأي خطأ آخر، نعرضه كما هو
            await update.message.reply_text(f"❌ حدث خطأ غير متوقع:\n`{e}`", parse_mode=constants.ParseMode.MARKDOWN)
            return ConversationHandler.END
    # --- نهاية تعديل 3 ---

    me = await client.get_me()
    update_account_status(phone, owner_id, 'ACTIVE', me.id, me.first_name, me.username)
    log_activity(phone, _("add_account", owner_id), _("login_success_code", owner_id))
    
    await handle_login_success_message(update, context, phone, me.first_name)
    
    await check_single_account_logic(phone, owner_id, context, is_new_account=True)
    await cleanup_conversation(context)
    return ConversationHandler.END


async def add_get_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    phone = context.user_data['phone']
    owner_id = update.effective_user.id
    user_id = owner_id
    client: TelegramClient = context.user_data['client']
    try:
        await client.sign_in(password=password)
    except PasswordHashInvalidError:
        await update.message.reply_text(_("invalid_password", user_id))
        return ADD_PASSWORD
    except Exception as e:
        await update.message.reply_text(_("unexpected_error", user_id, error=e))
        return ConversationHandler.END

    me = await client.get_me()
    update_account_status(phone, owner_id, 'ACTIVE', me.id, me.first_name, me.username)
    log_activity(phone, _("add_account", owner_id), _("login_success_password", owner_id))
    await handle_login_success_message(update, context, phone, me.first_name)
    await check_single_account_logic(phone, owner_id, context, is_new_account=True)
    await cleanup_conversation(context)
    return ConversationHandler.END


# ==============================================================================
# ||             تاسعاً: قسم فحص الحسابات (مع تقارير تفاعلية)                  ||
# ==============================================================================
async def check_accounts_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    await push_state(context, check_accounts_start, 'check_accounts_start')

    accounts = get_accounts_by_owner(user_id)
    if not accounts:
        keyboard = [[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]
        await query.message.edit_text(_("no_accounts_to_check", user_id), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    msg = await query.message.edit_text(
        _("checking_accounts", user_id, count=len(accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    
    tasks = [check_single_account_logic(acc['phone'], user_id, context, progress_msg=msg, total=len(accounts), current=i+1) for i, acc in enumerate(accounts)]
    results = await asyncio.gather(*tasks)

    report = _("check_accounts_report_header", user_id)
    status_counts = {'ACTIVE': 0, 'BANNED': 0, 'NEEDS_LOGIN': 0, 'UNKNOWN': 0}
    status_emoji = {'ACTIVE': '🟢', 'BANNED': '🔴', 'NEEDS_LOGIN': '🟡', 'UNKNOWN': '❓'}
    
    keyboard = []
    for phone, status, details in results:
        status_text = _(f"status_{status.lower()}", user_id)
        report += f"{status_emoji.get(status, '❔')} `{phone}`: **{status_text}**\n"
        if details:
            report += f"   └ {details}\n"
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if status in ['BANNED', 'NEEDS_LOGIN']:
            keyboard.append([
                InlineKeyboardButton(
                    _('check_account_quick_action', user_id, phone=phone),
                    callback_data=f"quick_action:{phone}:{status}"
                )
            ])

    summary = (_("check_accounts_summary_header", user_id) + "\n"
               + f"   - 🟢 {_('status_active', user_id)}: `{status_counts['ACTIVE']}`\n"
               + f"   - 🔴 {_('status_banned', user_id)}: `{status_counts['BANNED']}`\n"
               + f"   - 🟡 {_('status_needs_login', user_id)}: `{status_counts['NEEDS_LOGIN']}`\n"
               + f"   - ❓ {_('status_unknown', user_id)}: `{status_counts['UNKNOWN']}`")
    
    keyboard.append([InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')])
    await msg.edit_text(report + summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)


async def handle_quick_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    _, phone, status = query.data.split(':')
    
    context.user_data['selected_phone'] = phone
    
    keyboard = []
    if status == 'BANNED':
        keyboard = [
            [InlineKeyboardButton(_("delete_account_button", user_id), callback_data="mng:delete_confirm")],
            [InlineKeyboardButton(_("ignore_button", user_id), callback_data="close_message")]
        ]
    elif status == 'NEEDS_LOGIN':
        keyboard = [
            [InlineKeyboardButton(_("login_account_button", user_id), callback_data="add_account_start")],
            [InlineKeyboardButton(_("delete_account_button", user_id), callback_data="mng:delete_confirm")],
            [InlineKeyboardButton(_("ignore_button", user_id), callback_data="close_message")]
        ]
    
    await query.message.reply_text(_("quick_action_message", user_id, phone=phone), reply_markup=InlineKeyboardMarkup(keyboard))


async def close_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.message.delete()


async def check_single_account_logic(phone: str, owner_id: int, context: ContextTypes.DEFAULT_TYPE, is_new_account=False, progress_msg=None, total=1, current=1) -> tuple[str, str, str]:
    if progress_msg:
        await progress_updater(progress_msg, total, current, _("checking_accounts", owner_id, count=total), owner_id)

    client = await get_telethon_client(phone, owner_id)
    status, details, me = 'UNKNOWN', 'No details', None
    try:
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            status = 'ACTIVE'
            
            escaped_first_name = markdown_v2(me.first_name or "")
            escaped_username = markdown_v2(me.username or "")

            details = f"Logged in as {escaped_first_name}"
            if escaped_username:
                details += f" (@{escaped_username})"

            if not is_new_account:
                account_db = get_account_by_phone(phone, owner_id)
                if not account_db: raise Exception("Account not found in DB for owner.")
                
                stored_hashes_json = account_db['auth_hashes']
                stored_hashes = set(json.loads(stored_hashes_json)) if stored_hashes_json else set()

                result = await client(functions.account.GetAuthorizationsRequest())
                current_hashes = {auth.hash for auth in result.authorizations}

                if stored_hashes and current_hashes - stored_hashes:
                    new_sessions = [auth for auth in result.authorizations if auth.hash in (current_hashes - stored_hashes)]
                    for session in new_sessions:
                        await send_admin_notification(context, _("security_alert_new_login", owner_id, phone=phone, owner_id=owner_id, device_model=session.device_model, ip=session.ip, country=session.country, app_name=session.app_name))
                        log_activity(phone, _("security_alert", owner_id), _("new_login_from", owner_id, ip=session.ip, country=session.country))

                update_account_auth_hashes(phone, owner_id, list(current_hashes))
        else:
            status = 'NEEDS_LOGIN'
            details = _("session_key_unregistered", owner_id)
            
    except (PhoneNumberBannedError, UserDeactivatedBanError) as e:
        status = 'BANNED'
        details = _("phone_banned_error", owner_id)
        await send_admin_notification(context, _("admin_account_banned_alert", 0, phone=phone, owner_id=owner_id))
        log_activity(phone, _("account_banned_alert", owner_id), str(e))
    except AuthKeyUnregisteredError:
        status = 'NEEDS_LOGIN'
        details = _("session_key_unregistered", owner_id)
    except RpcCallFailError as e:
        status = 'UNKNOWN'
        details = f"RPC Error: {e}"
    except Exception as e:
        status = 'UNKNOWN'
        # <== تم الإصلاح: تهريب رسالة الخطأ قبل عرضها
        details = f"Connection error: {markdown_v2(str(e))}"
        logger.error(f"Error checking {phone} for {owner_id}: {e}", exc_info=True)
    finally:
        pass

    update_account_status(phone, owner_id, status,
                          me.id if me else None,
                          me.first_name if me else None,
                          me.username if me else None)
    return phone, status, details

# ==============================================================================
# ||                      عاشراً: قسم إدارة الحسابات (مطور جداً)                  ||
# ==============================================================================

async def manage_accounts_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    owner_id = query.from_user.id 
    page = int(query.data.split(':')[1]) if ':' in query.data else 0
    context.user_data['account_page'] = page
    await query.answer()

    await push_state(context, manage_accounts_start, f"manage_accounts_start:{page}")

    accounts = get_accounts_by_owner(owner_id)
    if not accounts:
        keyboard = [[InlineKeyboardButton(_("back_to_main_menu", owner_id), callback_data='back_to_main')]]
        await query.message.edit_text(_("no_accounts_registered", owner_id), reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    buttons = []
    status_emoji = {'ACTIVE': '🟢', 'BANNED': '🔴', 'NEEDS_LOGIN': '🟡', 'UNKNOWN': '❓'}
    for acc in accounts:
        emoji = status_emoji.get(acc['status'], '❔')
        btn_text = f"{emoji} {acc['phone']}" + (f" ({acc['first_name'] or acc['username'] or _('unknown_name', owner_id)})" if acc['first_name'] or acc['username'] else "")
        buttons.append(InlineKeyboardButton(btn_text, callback_data=f"select_acc:{acc['phone']}"))

    keyboard_list = create_paginated_keyboard(buttons, page, 8, 'manage_accounts_start', len(accounts), owner_id)
    # 🚨 التعديل هنا: تغيير 'back_to_main' إلى 'show_management_options' 🚨
    keyboard_list.append([InlineKeyboardButton(_("back_to_main_menu", owner_id), callback_data='show_management_options')]) # <== تغيير هنا

    await query.message.edit_text(
        _("account_management_title", owner_id),
        reply_markup=InlineKeyboardMarkup(keyboard_list),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    # <== تم الإصلاح: تصحيح الخطأ الطباعي في السطر التالي
    return SELECT_ACCOUNT

# <== تم الإصلاح: دالة مساعدة لمنع تكرار الكود
async def _get_account_management_payload(phone: str, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[str, InlineKeyboardMarkup]:
    """Builds the text and keyboard for the account management menu."""
    account = get_account_by_phone(phone, user_id)
    if not account:
        return _("error_account_not_found", user_id), None

    proxy_info = _("proxy_not_set", user_id)
    if account['proxy_id']:
        proxy = get_proxy_by_id(account['proxy_id'])
        if proxy:
            proxy_info = f"`{proxy['protocol']}://...`"

    last_check_str = account['last_check'] or _("last_check_not_available", user_id)
    add_method_str = account['add_method'] or _("add_method_unknown", user_id)
    status_translated = _(f"status_{account['status'].lower()}", user_id)
    
    first_name = account['first_name'] or _('not_specified', user_id)
    username = account['username'] or _('not_available', user_id)

    text = (_("account_details_header", user_id, phone=phone) + "\n"
            + f"   - **{_('account_name', user_id)}** `{first_name}`\n"
            + f"   - **{_('account_id', user_id)}** `@{username}`\n"
            + f"   - **{_('account_status', user_id)}** `{status_translated}` ({_('account_last_check', user_id)}: `{last_check_str}`)\n"
            + f"   - **{_('account_add_method', user_id)}** `{add_method_str}`\n")

    if account['creation_date']:
        text += f"   - **{_('account_session_date', user_id)}** `{account['creation_date']}`\n"
        try:
            creation_dt = None
            # Try parsing both 24-hour and 12-hour formats for backward compatibility
            for fmt in ('%Y-%m-%d %I:%M:%S %p', '%Y-%m-%d %H:%M:%S'):
                try:
                    creation_dt = datetime.strptime(account['creation_date'], fmt)
                    break
                except ValueError: pass
            
            if creation_dt:
                damascus_tz = pytz.timezone("Asia/Damascus")
                now_aware = datetime.now(damascus_tz)
                # Make creation_dt timezone-aware
                creation_dt_aware = creation_dt.astimezone(damascus_tz) if creation_dt.tzinfo else damascus_tz.localize(creation_dt)
                
                # Calculate 24h mark
                target_24h_dt = creation_dt_aware + timedelta(hours=24)
                target_24h_str = target_24h_dt.strftime('%I:%M:%S %p')
                time_remaining = target_24h_dt - now_aware
                if time_remaining.total_seconds() < 0:
                    time_remaining_str = "انتهت"
                else:
                    r_h, rem = divmod(int(time_remaining.total_seconds()), 3600)
                    r_m, r_s = divmod(rem, 60)
                    time_remaining_str = f"{r_h:02}:{r_m:02}:{r_s:02}"
                text += f"   - **{_('session_24h_mark', user_id)}** `{target_24h_str}` (`{_('time_left', user_id)} {time_remaining_str}`)\n"

                # Calculate session age
                time_passed = now_aware - creation_dt_aware
                days = time_passed.days
                hours, rem = divmod(time_passed.seconds, 3600)
                minutes, seconds = divmod(rem, 60)
                age_text = _('session_age_full_detail', user_id, d=int(days), h=int(hours), m=int(minutes), s=int(seconds))
                text += f"   - **{_('session_age', user_id)}** `{age_text}`\n"
        except Exception as e:
            logger.warning(f"Could not parse creation_date for timer: {account['creation_date']} - Error: {e}")

    text += f"   - **{_('account_proxy', user_id)}** {proxy_info}"
    
    current_page = context.user_data.get('account_page', 0)
    keyboard = [
        [InlineKeyboardButton(_("update_data_button", user_id), callback_data="mng:reload"), InlineKeyboardButton(_("extract_session_button", user_id), callback_data="mng:extract_session")],
        [InlineKeyboardButton(_("change_name_button", user_id), callback_data="mng:change_name"), InlineKeyboardButton(_("change_bio_button", user_id), callback_data="mng:change_bio")],
        [InlineKeyboardButton(_("change_photo_button", user_id), callback_data="mng:change_photo"), InlineKeyboardButton(_("change_username_button", user_id), callback_data="mng:change_username")],
        [InlineKeyboardButton(_("manage_2fa_button", user_id), callback_data="mng:manage_2fa"), InlineKeyboardButton(_("clean_account_button", user_id), callback_data="mng:cleaner_start")],
        [InlineKeyboardButton(_("auto_replies_button", user_id), callback_data=f"autoreply:menu:{phone}")],
        [InlineKeyboardButton(_("manage_stories_button", user_id), callback_data=f"story:menu:{phone}")],
        [InlineKeyboardButton(_("manage_contacts_button", user_id), callback_data="s_contacts:menu")],
        [InlineKeyboardButton(_("active_sessions_button", user_id), callback_data="mng:active_sessions")],
        [InlineKeyboardButton(_("get_last_message_button", user_id), callback_data="mng:get_last_msg"), InlineKeyboardButton(_("assign_proxy_button", user_id), callback_data="mng:assign_proxy")],
        [InlineKeyboardButton(_("activity_log_button", user_id), callback_data="mng:view_log:0")],
        [InlineKeyboardButton(_("delete_account_final_button", user_id), callback_data="mng:delete_confirm")],
    ]

    # --- هذا هو التعديل المطلوب ---
    # إضافة زر إعادة تسجيل الدخول بشكل شرطي
    if account['status'] == 'NEEDS_LOGIN':
        keyboard.append([InlineKeyboardButton(_("relogin_button_account_menu", user_id), callback_data=f"start_relogin_flow:{phone}")])
    # --- نهاية التعديل ---

    keyboard.append([InlineKeyboardButton(_("go_back_button", user_id), callback_data=f"manage_accounts_start:{current_page}")])
    
    return text, InlineKeyboardMarkup(keyboard)


# ==============================================================================
# ||             قسم إدارة جهات الاتصال لحساب فردي (جديد ومفعل)               ||
# ==============================================================================

async def add_contacts_from_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles an uploaded contact file and routes it to the correct execution function."""
    document = update.message.document
    if not document or not document.file_name.endswith('.txt'):
        await update.message.reply_text("❌ يرجى إرسال ملف بصيغة .txt فقط.")
        # We stay in the same state, waiting for a valid file or text
        if context.user_data.get('contact_add_mode') == 'single':
            return SINGLE_CONTACT_GET_LIST
        else:
            return BULK_CONTACTS_GET_LIST

    file = await context.bot.get_file(document.file_id)
    file_content_bytes = await file.download_as_bytearray()
    contacts_input = file_content_bytes.decode('utf-8')

    # Pass the file content to the appropriate execution function
    if context.user_data.get('contact_add_mode') == 'single':
        return await execute_single_add_contacts(update, context, contacts_input=contacts_input)
    else:
        return await execute_bulk_add_contacts(update, context, contacts_input=contacts_input)

async def execute_bulk_add_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Adds a list of contacts to the selected accounts from text or file, parsing for valid formats."""
    contacts_input = update.message.text
    owner_id = update.effective_user.id
    
    # --- بداية التعديل الذكي ---
    words = re.split(r'\s+|,|\n', contacts_input)
    contacts_to_process = [word for word in words if word.strip().startswith('+') or word.strip().startswith('@')]
    
    if not contacts_to_process:
        await update.message.reply_text("❌ لم يتم العثور على أي أرقام هواتف أو معرفات صالحة في الإدخال.")
        return await show_contact_management_menu(update, context)
    # --- نهاية التعديل الذكي ---

    selected_accounts = list(context.user_data.get('selected_accounts', []))
    action_title = _("bulk_add_contacts_button", owner_id)

    msg = await update.message.reply_text(
        _("starting_bulk_task", owner_id, action_type=action_title, count=len(selected_accounts)),
    )
    
    success_count, failure_count = 0, 0
    report_lines = [f"**{_('bulk_task_report_header_no_link', owner_id, action_type=action_title)}**\n"]
    
    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", owner_id, current=i+1, total=len(selected_accounts), phone=phone), owner_id)
        account_success, account_fail = 0, 0
        try:
            client = await get_telethon_client(phone, owner_id)
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception(_("account_needs_login_alert", owner_id))
            
            for contact_str in contacts_to_process:
                try:
                    if contact_str.startswith('+') and contact_str[1:].isdigit():
                        contact_obj = types.InputPhoneContact(client_id=0, phone=contact_str, first_name=contact_str, last_name='')
                        await client(functions.contacts.ImportContactsRequest(contacts=[contact_obj]))
                    else:
                        user_entity = await client.get_entity(contact_str)
                        await client(functions.contacts.AddContactRequest(
                            id=user_entity,
                            first_name=user_entity.first_name or contact_str.replace('@',''),
                            last_name=user_entity.last_name or '',
                            phone="",
                            add_phone_privacy_exception=False
                        ))
                    account_success += 1
                except Exception as inner_e:
                    logger.warning(f"Failed to add contact {contact_str} for {phone}: {inner_e}")
                    account_fail += 1
                await asyncio.sleep(0.5)
            
            report_lines.append(f"✅ `{phone}`: {_('task_success', owner_id)} (Added: {account_success}, Failed: {account_fail})")
            success_count += 1
        except Exception as e:
            escaped_error = markdown_v2(str(e))
            report_lines.append(f"❌ `{phone}`: {_('task_failure', owner_id, error=escaped_error)}")
            failure_count += 1
        await asyncio.sleep(1)

    final_report_text = _("bulk_task_final_report", owner_id, 
                          action_title=action_title, 
                          success_count=success_count, 
                          failure_count=failure_count)
    
    keyboard = [[InlineKeyboardButton(_("back_to_bulk_menu", owner_id), callback_data="show_contact_management_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(final_report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    await cleanup_conversation(context)
    return ConversationHandler.ENDv


async def show_single_contact_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the contact management menu for a single account."""
    query = update.callback_query
    user_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    await query.answer()

    await push_state(context, show_single_contact_menu, query.data)

    # <== تم دمج أزرار الإضافة في زر واحد
    keyboard = [
        [InlineKeyboardButton(_("add_contacts_single_button", user_id), callback_data="s_contacts:add_prompt")],
        [InlineKeyboardButton(_("delete_all_contacts_single_button", user_id), callback_data="s_contacts:delete_confirm")],
        [InlineKeyboardButton(_("export_contacts_single_button", user_id), callback_data="s_contacts:export")],
        [InlineKeyboardButton(_("back_to_account_management", user_id), callback_data=f"select_acc:{phone}")]
    ]
    
    await query.message.edit_text(
        text=_("single_contact_menu_title", user_id, phone=phone),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SINGLE_CONTACT_MENU


async def single_add_from_file_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks the user to send the contact file."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(_("send_contact_file_prompt", query.from_user.id))
    return SINGLE_CONTACT_GET_FILE



async def add_contacts_from_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes an uploaded contact file and passes its content to the execution function."""
    document = update.message.document
    if not document or not document.file_name.lower().endswith('.txt'):
        await update.message.reply_text("❌ يرجى إرسال ملف بصيغة .txt فقط.")
        return SINGLE_CONTACT_GET_LIST

    file = await context.bot.get_file(document.file_id)
    file_content_bytes = await file.download_as_bytearray()
    contacts_input = file_content_bytes.decode('utf-8')

    # استدعاء دالة التنفيذ الرئيسية وتمرير محتوى الملف لها
    return await execute_single_add_contacts(update, context, contacts_input=contacts_input)


async def single_add_contacts_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the list of contacts to add for a single account."""
    query = update.callback_query
    await query.message.edit_text(_("enter_contacts_to_add", query.from_user.id))
    return SINGLE_CONTACT_GET_LIST

async def execute_bulk_add_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Adds a list of contacts to the selected accounts from text or file."""
    if contacts_input is None:
        contacts_input = update.message.text

    owner_id = update.effective_user.id
    
    msg = await update.message.reply_text(
        _("starting_bulk_task", owner_id, action_type=action_title, count=1)
    )
    
    success_count, failure_count = 0, 0
    
    try:
        contacts_to_add = [c.strip() for c in re.split(r'\s+|,|\n', contacts_input) if c.strip()]
        if not contacts_to_add:
            raise ValueError("No contacts provided.")

        client = await get_telethon_client(phone, owner_id)
        await client.connect()
        if not await client.is_user_authorized(): raise Exception(_("account_needs_login_alert", owner_id))

        for contact_str in contacts_to_add:
            try:
                if contact_str.startswith('+') and contact_str[1:].isdigit():
                    # Handle phone numbers
                    contact_obj = types.InputPhoneContact(client_id=0, phone=contact_str, first_name=contact_str, last_name='')
                    await client(functions.contacts.ImportContactsRequest(contacts=[contact_obj]))
                else:
                    # Handle usernames
                    user_entity = await client.get_entity(contact_str)
                    await client(functions.contacts.AddContactRequest(
                        id=user_entity,
                        first_name=user_entity.first_name or contact_str.replace('@',''),
                        last_name=user_entity.last_name or '',
                        phone="",
                        add_phone_privacy_exception=False
                    ))
                success_count += 1
                log_activity(phone, action_title, f"Successfully added {contact_str}")
            except Exception as inner_e:
                logger.warning(f"Failed to add contact {contact_str} for {phone}: {inner_e}")
                failure_count += 1
            await asyncio.sleep(1) # Small delay between adds

        status = _("bulk_task_final_report", owner_id, action_title=action_title, success_count=success_count, failure_count=failure_count)

    except Exception as e:
        status = _("story_post_failed", owner_id, error=str(e))
        log_activity(phone, action_title, status)
    
    keyboard = [[InlineKeyboardButton(_("back_to_account_management", owner_id), callback_data=f"select_acc:{phone}")]]
    await msg.edit_text(status, reply_markup=InlineKeyboardMarkup(keyboard))

    return SINGLE_CONTACT_MENU

async def single_delete_contacts_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks for final confirmation before deleting all contacts."""
    query = update.callback_query
    user_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(_("yes_delete_now", user_id), callback_data="s_contacts:execute_delete")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data='go_back')]
    ]
    await query.message.edit_text(
        _("confirm_delete_all_contacts", user_id, phone=phone), 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SINGLE_CONTACT_CONFIRM_DELETE

async def execute_single_delete_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Deletes all contacts from the selected account."""
    query = update.callback_query
    owner_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    action_title = _("bulk_delete_contacts_button", owner_id)
    await query.answer()
    
    msg = await query.message.edit_text(_("starting_bulk_task", owner_id, action_type=action_title, count=1))
    
    try:
        client = await get_telethon_client(phone, owner_id)
        await client.connect()
        if not await client.is_user_authorized(): raise Exception(_("account_needs_login_alert", owner_id))
        
        contacts = await client(functions.contacts.GetContactsRequest(hash=0))
        if contacts.users:
            await client(functions.contacts.DeleteContactsRequest(id=contacts.users))
            status = _("task_success", owner_id)
        else:
            status = _("no_contacts_to_export", owner_id)
        log_activity(phone, action_title, status)
    except Exception as e:
        status = _("story_post_failed", owner_id, error=str(e))
        log_activity(phone, action_title, status)

    # <== تعديل: عرض النتيجة مع زر الرجوع
    keyboard = [[InlineKeyboardButton(_("back_to_account_management", owner_id), callback_data=f"select_acc:{phone}")]]
    final_text = _("story_final_status", owner_id, status=status)
    await msg.edit_text(final_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return SINGLE_CONTACT_MENU

async def execute_single_export_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exports contacts for a single account."""
    query = update.callback_query
    owner_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    action_title = _("export_contacts_button", owner_id)
    await query.answer()

    msg = await query.message.edit_text(_("starting_bulk_task", owner_id, action_type=action_title, count=1))
    
    try:
        client = await get_telethon_client(phone, owner_id)
        await client.connect()
        if not await client.is_user_authorized(): raise Exception(_("account_needs_login_alert", owner_id))
        
        contacts = await client(functions.contacts.GetContactsRequest(hash=0))
        
        export_text = f"--- Contacts for {phone} ---\n"
        if not contacts.users:
            export_text += _("no_contacts_to_export", owner_id)
        else:
            for user in contacts.users:
                username_str = f"@{user.username}" if user.username else "N/A"
                export_text += f"ID: {user.id}, Name: {user.first_name}, Username: {username_str}\n"
        
        output_file = io.BytesIO(export_text.encode('utf-8'))
        output_file.name = f"contacts_{phone.replace('+', '')}.txt"
        
        await context.bot.send_document(chat_id=owner_id, document=output_file)
        status = _("export_contacts_caption", owner_id, count=len(contacts.users))
        log_activity(phone, action_title, _("success", owner_id))
    except Exception as e:
        status = _("story_post_failed", owner_id, error=str(e))
        log_activity(phone, action_title, _("failed", owner_id, error=str(e)))
    
    # <== تعديل: عرض النتيجة مع زر الرجوع
    keyboard = [[InlineKeyboardButton(_("back_to_account_management", owner_id), callback_data=f"select_acc:{phone}")]]
    final_text = _("story_final_status", owner_id, status=status)
    await msg.edit_text(final_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return SINGLE_CONTACT_MENU

async def select_account_for_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    phone = None
    if ':' in query.data:
        potential_phone = query.data.split(':')[1]
        if potential_phone.startswith('+'):
            phone = potential_phone
            context.user_data['selected_phone'] = phone

    if not phone:
        phone = context.user_data.get('selected_phone')

    if not phone:
        await query.message.edit_text(_("error_account_not_found", user_id))
        return ConversationHandler.END

    await push_state(context, select_account_for_management, f"select_acc:{phone}")
    
    text, reply_markup = await _get_account_management_payload(phone, user_id, context)

    if reply_markup:
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)
    else:
        await query.message.edit_text(text)

    return MANAGE_ACCOUNT

async def handle_management_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action_full = query.data
    action_parts = action_full.split(':')
    action = action_parts[1]
    
    owner_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    if not phone:
        await query.answer(_("error_account_not_selected", owner_id), show_alert=True)
        return await back_to_main_menu(update, context)

    await query.answer()
    client = await get_telethon_client(phone, owner_id)

    if action == 'reload':
        msg = await query.message.edit_text(_("updating_account_data", owner_id, phone=phone))
        await check_single_account_logic(phone, owner_id, context)
        log_activity(phone, _("update_data_log", owner_id), _("manual_update_requested", owner_id))
        
        # <== تم الإصلاح: إعادة عرض القائمة المحدثة مباشرة
        text, reply_markup = await _get_account_management_payload(phone, owner_id, context)
        await msg.edit_text(text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)
        return MANAGE_ACCOUNT

    elif action == 'extract_session':
        msg = await query.message.edit_text(_("extracting_session", owner_id))
        try:
            await client.connect()
            if await client.is_user_authorized():
                session_string = StringSession.save(client.session)
                log_activity(phone, _("extract_session_log", owner_id), _("success", owner_id))
                await msg.delete()
                # <== تم الإصلاح: إضافة زر رجوع
                keyboard = [[
                    InlineKeyboardButton(
                        _("back_to_account_management", owner_id), 
                        callback_data=f"select_acc:{phone}"
                    )
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(
                    _("session_code_header", owner_id, phone=phone, session_string=session_string),
                    reply_markup=reply_markup,
                    parse_mode=constants.ParseMode.MARKDOWN
                )
            else:
                await msg.edit_text(_("extract_session_failed_login_needed", owner_id))
                await asyncio.sleep(2)
                return await go_back(update, context)

        except Exception as e:
            await msg.edit_text(_("extract_session_failed_error", owner_id, error=str(e)))
            await asyncio.sleep(2)
            return await go_back(update, context)
        finally:
            return MANAGE_ACCOUNT
    
    elif action == 'get_last_msg':
        msg = await query.message.edit_text(_("getting_last_message", owner_id))
        try:
            await client.connect()
            if not await client.is_user_authorized():
                await msg.edit_text(_("account_needs_login_alert", owner_id))
            else:
                last_dialog = await client.get_dialogs(limit=1)
                if not last_dialog:
                    await msg.edit_text(_("no_messages_in_account", owner_id))
                else:
                    message = last_dialog[0].message
                    sender = await message.get_sender()
                    sender_name = getattr(sender, 'first_name', None) or getattr(sender, 'title', _('unknown', owner_id))
                    
                    message_text = (_("last_message_header", owner_id, phone=phone) + "\n\n"
                                    + f"▪️ **{_('from', owner_id)}:** `{sender_name}`\n"
                                    + f"▪️ **{_('date', owner_id)}:** `{message.date.strftime('%Y-%m-%d %H:%M')}`\n"
                                    + f"▪️ **{_('content', owner_id)}:**\n`{message.text or _('message_no_text', owner_id)}`")
                    
                    keyboard = [[
                        InlineKeyboardButton(
                            _("back_to_account_management", owner_id), 
                            callback_data=f"select_acc:{phone}"
                        )
                    ]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await msg.edit_text(message_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)
                log_activity(phone, _("get_last_message_log", owner_id), _("success", owner_id))
        except Exception as e:
            log_activity(phone, _("get_last_message_log", owner_id), f"{_('failed', owner_id)}: {e}")
            await msg.edit_text(_("error", owner_id, error=e))
        return MANAGE_ACCOUNT

    elif action == 'change_name':
        await push_state(context, handle_management_action, query.data)
        await query.message.edit_text(_("enter_new_first_name", owner_id),
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("cancel_button", owner_id), callback_data="go_back")]]))
        return GET_NEW_VALUE
        
    elif action == 'change_bio':
        await push_state(context, handle_management_action, query.data)
        await query.message.edit_text(_("enter_new_bio", owner_id),
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("cancel_button", owner_id), callback_data="go_back")]]))
        return GET_BIO

    elif action == 'change_username':
        await push_state(context, handle_management_action, query.data)
        await query.message.edit_text(_("enter_new_username", owner_id),
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("cancel_button", owner_id), callback_data="go_back")]]))
        return SET_NEW_USERNAME

    elif action == 'change_photo':
        await push_state(context, handle_management_action, query.data)
        await query.message.edit_text(_("send_new_photo", owner_id),
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("cancel_button", owner_id), callback_data="go_back")]]))
        return GET_PHOTO

    elif action == 'manage_2fa':
        return await tfa_start_management(update, context, client)
        
    elif action == 'cleaner_start':
        return await single_cleaner_start(update, context)

    elif action == 'active_sessions':
        return await handle_active_sessions(update, context, client, phone, owner_id)
    
    elif action == 'reset_auths_confirm':
        keyboard = [
            [InlineKeyboardButton(_("yes_delete_now", owner_id), callback_data="mng:reset_auths_execute")],
            [InlineKeyboardButton(_("cancel_button", owner_id), callback_data='go_back')]
        ]
        await query.message.edit_text(_("reset_auths_warning", owner_id),
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        return MANAGE_ACCOUNT

    elif action == 'reset_auths_execute':
        msg = await query.message.edit_text(_("deleting_sessions", owner_id))
        try:
            await client.connect()
            await client(functions.auth.ResetAuthorizationsRequest())
            log_activity(phone, _("delete_sessions_log", owner_id), _("all_other_sessions_deleted", owner_id))
            await msg.edit_text(_("all_other_sessions_deleted_success", owner_id))
        except Exception as e:
            log_activity(phone, _("delete_sessions_log", owner_id), f"{_('failed', owner_id)}: {e}")
            await msg.edit_text(_("error", owner_id, error=e))
        finally:
            pass
        await asyncio.sleep(2)
        return await handle_active_sessions(update, context, client, phone, owner_id)

    elif action == 'assign_proxy':
        context.user_data['phone_to_assign_proxy'] = phone
        return await manage_proxies_start(update, context, from_account_management=True)

    elif action == 'logout_confirm':
        # This seems to be a duplicate, let's remove it and point to delete confirm
        # This makes the UI cleaner. The 'Wipe & Logout' is the main destructive action.
        keyboard = [
            [InlineKeyboardButton(_("yes_logout_now", owner_id), callback_data=f"mng:logout_execute")],
            [InlineKeyboardButton(_("cancel_button", owner_id), callback_data='go_back')]
        ]
        await query.message.edit_text(
            _("logout_confirmation_message", owner_id, phone=phone),
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN
        )
        return MANAGE_ACCOUNT

    elif action == 'logout_execute':
        msg = await query.message.edit_text(_("logging_out_account", owner_id, phone=phone))
        success = False
        try:
            await client.connect()
            if await client.is_user_authorized():
                await client.log_out()
                update_account_status(phone, owner_id, 'NEEDS_LOGIN')
                log_activity(phone, _("logout_account_log", owner_id), _("success", owner_id))
                success = True
            else:
                # Already logged out, just update status
                update_account_status(phone, owner_id, 'NEEDS_LOGIN')
                success = True
        except Exception as e:
            log_activity(phone, _("logout_account_log", owner_id), f"{_('failed', owner_id)}: {e}")
            await query.answer(_("error", owner_id, error=e), show_alert=True)
        finally:
            pass
        
        if success:
            await msg.edit_text(_("logout_success_update_list", owner_id))
            await asyncio.sleep(2)

        return await select_account_for_management(update, context)

    elif action == 'delete_confirm':
        keyboard = [
            [InlineKeyboardButton(_("confirm_delete_full_logout", owner_id), callback_data="mng:delete_execute:full")],
            [InlineKeyboardButton(_("confirm_delete_local_only", owner_id), callback_data="mng:delete_execute:local")],
            [InlineKeyboardButton(_("cancel_button", owner_id), callback_data='go_back')]
        ]
        await query.message.edit_text(
            _("choose_delete_method", owner_id),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MANAGE_ACCOUNT

    elif action == 'delete_execute':
        delete_type = action_parts[2]
        user_id_for_delete = query.from_user.id
        msg_text = _("deleting_account_progress", user_id_for_delete, phone=phone)
        msg = await query.message.edit_text(msg_text)
        
        if delete_type == 'full':
            await msg.edit_text(f"{msg_text}\n{_('delete_step_logout', user_id_for_delete)}")
            try:
                await client.connect()
                if await client.is_user_authorized():
                    await client.log_out()
                    log_activity(phone, _("end_session_full_delete", user_id_for_delete), _("success", user_id_for_delete))
            except Exception as e:
                log_activity(phone, _("end_session_full_delete", user_id_for_delete), f"{_('failed', user_id_for_delete)}: {e}")
                await query.answer(_("warning_logout_failed_continue_local_delete", user_id_for_delete, error=e), show_alert=True)
            finally:
                pass
        
        await msg.edit_text(f"{msg_text}\n{_('delete_step_local_data', user_id_for_delete)}")
        session_path = os.path.join(SESSIONS_DIR, f"{owner_id}_{phone}.session")
        if os.path.exists(session_path):
            os.remove(session_path)
        remove_account_from_db(phone, owner_id)
        
        await query.answer(_("delete_success", user_id_for_delete), show_alert=True)
        await msg.delete()
        
        state_stack = context.user_data.get('state_stack', deque(maxlen=10))
        if len(state_stack) > 1: state_stack.pop() # Pop the management menu state
        
        # Now go back to the account list
        return await go_back(update, context)


    elif action == 'view_log':
        page = int(action_full.split(':')[2])
        context.user_data['log_page'] = page
        return await view_activity_log(update, context, phone)

    return MANAGE_ACCOUNT

async def process_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    msg = await update.message.reply_text(_("updating_name", owner_id))
    
    parts = [p.strip() for p in new_value.split('|')]
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''
    
    client = await get_telethon_client(phone, owner_id)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await msg.edit_text(_("account_needs_login_alert", owner_id))
        else:
            await client(functions.account.UpdateProfileRequest(first_name=first_name, last_name=last_name))
            update_account_status(phone, owner_id, None, first_name=first_name, username=get_account_by_phone(phone, owner_id)['username'])
            log_activity(phone, _("change_name_log", owner_id), f"{_('to', owner_id)}: {first_name} {last_name}")
            await msg.edit_text(_("name_update_success", owner_id))
    except Exception as e:
        log_activity(phone, _("change_name_log", owner_id), f"{_('failed', owner_id)}: {e}")
        await msg.edit_text(_("error", owner_id, error=e))
    finally:
        await asyncio.sleep(2)
        await go_back(update, context)
    return ConversationHandler.END
    
async def process_new_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_bio = update.message.text
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    msg = await update.message.reply_text(_("updating_bio", owner_id))
    client = await get_telethon_client(phone, owner_id)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await msg.edit_text(_("account_needs_login_alert", owner_id))
        else:
            await client(functions.account.UpdateProfileRequest(about=new_bio))
            log_activity(phone, _("change_bio_log", owner_id), f"{_('to', owner_id)}: {new_bio[:30]}...")
            await msg.edit_text(_("bio_update_success", owner_id))
    except Exception as e:
        log_activity(phone, _("change_bio_log", owner_id), f"{_('failed', owner_id)}: {e}")
        await msg.edit_text(_("error", owner_id, error=e))
    finally:
        await asyncio.sleep(2)
        await go_back(update, context)
    return ConversationHandler.END

async def set_new_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_username = update.message.text.replace('@', '').strip()
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    msg = await update.message.reply_text(_("updating_username", owner_id, username=new_username))
    client = await get_telethon_client(phone, owner_id)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await msg.edit_text(_("account_needs_login_alert", owner_id))
        else:
            await client(functions.account.UpdateUsernameRequest(new_username))
            update_account_status(phone, owner_id, None, username=new_username, first_name=get_account_by_phone(phone, owner_id)['first_name'])
            log_activity(phone, _("change_username_log", owner_id), f"{_('to', owner_id)}: @{new_username}")
            await msg.edit_text(_("username_update_success", owner_id))
            await asyncio.sleep(2)
            await go_back(update, context)
    except UsernameOccupiedError:
        await msg.edit_text(_("username_occupied", owner_id))
        return SET_NEW_USERNAME
    except UsernameInvalidError:
        await msg.edit_text(_("username_invalid", owner_id))
        return SET_NEW_USERNAME
    except Exception as e:
        log_activity(phone, _("change_username_log", owner_id), f"{_('failed', owner_id)}: {e}")
        await msg.edit_text(_("error", owner_id, error=e))
        await asyncio.sleep(2)
        await go_back(update, context)
    return ConversationHandler.END
                
async def process_new_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    msg = await update.message.reply_text(_("uploading_photo", owner_id))
    client = await get_telethon_client(phone, owner_id)
    try:
        photo_file = await update.message.photo[-1].get_file()
        downloaded_file = await photo_file.download_as_bytearray()
        
        await client.connect()
        if not await client.is_user_authorized():
            await msg.edit_text(_("account_needs_login_alert", owner_id))
        else:
            await client(functions.photos.UploadProfilePhotoRequest(file=await client.upload_file(bytes(downloaded_file))))
            log_activity(phone, _("change_photo_log", owner_id), _("new_photo_uploaded", owner_id))
            await msg.edit_text(_("photo_update_success", owner_id))
        
    except Exception as e:
        log_activity(phone, _("change_photo_log", owner_id), f"{_('failed', owner_id)}: {e}")
        await msg.edit_text(_("error", owner_id, error=e))
    finally:
        await asyncio.sleep(2)
        await go_back(update, context)
    return ConversationHandler.END

async def view_activity_log(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    await push_state(context, view_activity_log, query.data)

    page = context.user_data.get('log_page', 0)
    logs = get_activity_log(phone)
    
    if not logs:
        text = _("activity_log_title", user_id, phone=phone) + "\n\n" + _("no_activity_log", user_id)
        keyboard_list = [[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard_list), parse_mode=constants.ParseMode.MARKDOWN)
        return MANAGE_ACCOUNT

    page_size = 5
    start_index = page * page_size
    end_index = start_index + page_size
    
    text = _("activity_log_title", user_id, phone=phone) + "\n\n"
    for log in logs[start_index:end_index]:
        timestamp = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%y-%m-%d %H:%M')
        text += f"▪️ **[{timestamp}]** - `{log['action']}`\n"
        if log['details']:
            text += f"   └ {_('details', user_id)}: `{log['details']}`\n"

    buttons = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ " + _("previous", user_id), callback_data=f"mng:view_log:{page-1}"))
    
    total_pages = math.ceil(len(logs) / page_size)
    if total_pages > 1:
        nav_buttons.append(InlineKeyboardButton(_("log_page", user_id, current_page=page + 1, total_pages=total_pages), callback_data="noop"))

    if end_index < len(logs):
        nav_buttons.append(InlineKeyboardButton(_("next", user_id) + " ➡️", callback_data=f"mng:view_log:{page+1}"))
    
    if nav_buttons: buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')])
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=constants.ParseMode.MARKDOWN)
    return MANAGE_ACCOUNT

# ==============================================================================
# ||                   [إصلاح نهائي] قسم إدارة القصص (طريقة مبسطة)                 ||
# ==============================================================================

async def story_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    
    message_to_edit = query.message if query else update.message
    
    await query.answer()

    if ':' in query.data and len(query.data.split(':')) > 2:
        phone = query.data.split(':')[2]
        context.user_data['selected_phone'] = phone
    
    await push_state(context, story_menu_start, query.data)

    keyboard = [
        [InlineKeyboardButton(_("story_post_now_button", user_id), callback_data="story:action:post_now")],
        [InlineKeyboardButton(_("back_to_account_management", user_id), callback_data='go_back')]
    ]
    
    await message_to_edit.edit_text(
        text=_("story_menu_title", user_id, phone=context.user_data['selected_phone']),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    return STORY_MENU

async def story_handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    action = query.data.split(':')[2]
    await query.answer()

    if action == 'post_now':
        await query.message.edit_text(text=_("story_send_file_prompt", user_id))
        return STORY_GET_FILE
    return STORY_MENU

async def story_get_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    photo, video = message.photo, message.video
    if not photo and not video:
        await message.reply_text(_("story_send_file_prompt", message.from_user.id))
        return STORY_GET_FILE

    context.user_data['story_file_id'] = photo[-1].file_id if photo else video.file_id
    context.user_data['story_file_type'] = 'photo' if photo else 'video'

    await message.reply_text(_("story_send_caption_prompt", message.from_user.id))
    return STORY_GET_CAPTION

async def story_get_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    caption = update.message.text
    context.user_data['story_caption'] = caption if caption != '/skip' else ""
    return await story_ask_privacy(update, context)

async def story_skip_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['story_caption'] = ""
    return await story_ask_privacy(update, context)

async def story_ask_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton(_("privacy_all", user_id), callback_data="story:set_privacy:all")],
        [InlineKeyboardButton(_("privacy_contacts", user_id), callback_data="story:set_privacy:contacts")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data='go_back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_to_edit = update.callback_query.message if update.callback_query else update.message
    await message_to_edit.reply_text(_("story_ask_privacy", user_id), reply_markup=reply_markup)
    return STORY_ASK_PRIVACY

async def story_set_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    privacy_type = query.data.split(':')[2]
    context.user_data['story_privacy_type'] = privacy_type
    
    return await story_ask_period(update, context)

async def story_ask_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton(_("period_6h", user_id), callback_data="story:set_period:6")],
        [InlineKeyboardButton(_("period_12h", user_id), callback_data="story:set_period:12")],
        [InlineKeyboardButton(_("period_24h", user_id), callback_data="story:set_period:24")],
        [InlineKeyboardButton(_("period_48h", user_id), callback_data="story:set_period:48")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data='go_back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_to_edit = update.callback_query.message if update.callback_query else update.message
    await message_to_edit.edit_text(_("story_ask_period", user_id), reply_markup=reply_markup)
    return STORY_ASK_PERIOD

async def story_set_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    hours_str = query.data.split(':')[2]
    period_seconds = int(hours_str) * 3600
    context.user_data['story_period_seconds'] = period_seconds
    
    return await _execute_and_show_final_menu(update, context)

async def _execute_and_show_final_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    
    message_source = update.message if update.message else update.callback_query.message
    
    await message_source.delete() # Delete the last question
    msg = await context.bot.send_message(chat_id=owner_id, text=_("story_posting_now", owner_id))
    status = _("failed", owner_id)
    
    try:
        file_id = context.user_data.get('story_file_id')
        file_type = context.user_data.get('story_file_type')
        caption = context.user_data.get('story_caption', '')
        privacy_type = context.user_data.get('story_privacy_type')
        period_seconds = context.user_data.get('story_period_seconds')

        bot_file = await context.bot.get_file(file_id)
        file_bytes = await bot_file.download_as_bytearray()
        
        final_media_bytes = file_bytes
        if file_type == 'photo':
            image = Image.open(io.BytesIO(file_bytes))
            output_buffer = io.BytesIO()
            image.convert("RGB").save(output_buffer, format="JPEG")
            final_media_bytes = output_buffer.getvalue()

        client = await get_telethon_client(phone, owner_id)
        await client.connect()
        if not await client.is_user_authorized():
            raise Exception(_("account_needs_login_alert", owner_id))
            
        uploaded_file = await client.upload_file(bytes(final_media_bytes), file_name='story.jpg' if file_type == 'photo' else 'story.mp4')

        privacy_rules = []
        if privacy_type == 'all':
            privacy_rules.append(types.InputPrivacyValueAllowAll())
        elif privacy_type == 'contacts':
            privacy_rules.append(types.InputPrivacyValueAllowContacts())

        await client(functions.stories.SendStoryRequest(
            peer='me',
            media=types.InputMediaUploadedPhoto(file=uploaded_file) if file_type == 'photo' else types.InputMediaUploadedDocument(file=uploaded_file, mime_type='video/mp4', attributes=[]),
            caption=caption,
            privacy_rules=privacy_rules,
            period=period_seconds
        ))
        status = _("story_post_success", owner_id)
        log_activity(phone, "نشر قصة", status)

    except Exception as e:
        status = _("story_post_failed", owner_id, error=str(e))
        logger.error(f"Story posting failed for {phone}: {e}", exc_info=True)
        log_activity(phone, "فشل نشر قصة", str(e))
    
    await msg.delete()
    
    keyboard = [
        [InlineKeyboardButton(_("story_post_another_button", owner_id), callback_data="story:action:post_now")],
        [InlineKeyboardButton(_("back_to_stories_menu_button", owner_id), callback_data=f"story:menu:{phone}")]
    ]
    
    await context.bot.send_message(
        chat_id=owner_id,
        text=_("story_final_status", owner_id, status=status),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    for key in ['story_file_id', 'story_file_type', 'story_caption', 'story_privacy_type', 'story_period_seconds']:
        context.user_data.pop(key, None)

    return STORY_MENU

# ... (rest of the file from the original text)
#==============================================================================
# ||                   قسم منظف الحساب الفردي المتقدم                        ||
# ==============================================================================
async def single_cleaner_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    phone = context.user_data.get('selected_phone')
    await push_state(context, single_cleaner_start, "mng:cleaner_start")

    keyboard = [
        [InlineKeyboardButton(_("leave_all_channels", user_id), callback_data="single_clean:confirm:leave_channels")],
        [InlineKeyboardButton(_("leave_all_groups", user_id), callback_data="single_clean:confirm:leave_groups")],
        [InlineKeyboardButton(_("delete_bot_chats", user_id), callback_data="single_clean:confirm:delete_bots")],
        [InlineKeyboardButton(_("delete_private_no_contact_chats", user_id), callback_data="single_clean:confirm:delete_private_no_contact")],
        [InlineKeyboardButton(_("delete_deleted_contacts", user_id), callback_data="single_clean:confirm:delete_deleted_contacts")],
        [InlineKeyboardButton(_("full_clean", user_id), callback_data="single_clean:confirm:full_clean")],
        [InlineKeyboardButton(_("back_to_account_management", user_id), callback_data="go_back")]
    ]
    await query.message.edit_text(
        _("single_cleaner_start_title", user_id, phone=phone),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CLEANER_MENU_SINGLE

async def single_cleaner_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    clean_type = query.data.split(':')[-1]
    context.user_data['single_clean_type'] = clean_type
    
    type_map = {
        'leave_channels': _('leave_all_channels', user_id),
        'leave_groups': _('leave_all_groups', user_id),
        'delete_bots': _('delete_bot_chats', user_id),
        'delete_private_no_contact': _('delete_private_no_contact_chats', user_id),
        'delete_deleted_contacts': _('delete_deleted_contacts', user_id),
        'full_clean': _('full_clean', user_id)
    }
    phone = context.user_data.get('selected_phone')
    
    keyboard = [[
        InlineKeyboardButton(_("yes_clean_now", user_id), callback_data="single_clean:execute"),
        InlineKeyboardButton(_("cancel_button", user_id), callback_data="go_back")
    ]]
    
    action_text = type_map.get(clean_type, _("unknown", user_id))
    
    await query.message.edit_text(
        _("confirm_single_cleaner", user_id, phone=phone, action_text=action_text),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    return CLEANER_CONFIRM_SINGLE

async def single_cleaner_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    clean_type = context.user_data.get('single_clean_type')
    phone = context.user_data.get('selected_phone')
    owner_id = query.from_user.id
    
    if not clean_type or not phone:
        await query.message.edit_text(_("cleaner_error_missing_info", user_id))
        return await go_back(update, context)

    msg = await query.message.edit_text(
        _("starting_single_cleaner", user_id, phone=phone),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    
    client = await get_telethon_client(phone, owner_id)
    report = { "channels": 0, "groups": 0, "bots": 0, "private": 0, "deleted_contacts": 0, "errors": 0 }

    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise Exception(_("account_needs_login_alert", owner_id))

        items_processed = 0
        
        if clean_type == 'delete_deleted_contacts' or clean_type == 'full_clean':
            await msg.edit_text(_("checking_contacts", user_id))
            contacts_result = await client(functions.contacts.GetContactsRequest(hash=0))
            deleted_users_to_delete = [user for user in contacts_result.users if user.deleted]
            if not deleted_users_to_delete:
                 if clean_type == 'delete_deleted_contacts': await msg.edit_text(_("no_deleted_contacts", user_id))
            else:
                await client(functions.contacts.DeleteContactsRequest(id=deleted_users_to_delete))
                report['deleted_contacts'] = len(deleted_users_to_delete)
                if clean_type == 'delete_deleted_contacts': await msg.edit_text(
                    _("deleted_contacts_success", user_id, count=len(deleted_users_to_delete))
                )
            log_activity(phone, _("cleaner_delete_deleted_contacts_log", owner_id), f"{_('deleted', owner_id)} {report['deleted_contacts']} {_('contacts', owner_id)}.")
        
        if clean_type != 'delete_deleted_contacts':
            dialogs = await client.get_dialogs()
            total_items = len(dialogs)
            
            await msg.edit_text(
                _("starting_cleaner_found_dialogs", user_id, total_items=total_items),
                parse_mode=constants.ParseMode.MARKDOWN
            )
            await asyncio.sleep(1)

            for dialog in dialogs:
                items_processed += 1
                await progress_updater(msg, total_items, items_processed, 
                                       _("cleaning_in_progress", user_id, phone=phone), user_id)
                
                try:
                    entity = dialog.entity
                    action_taken = False
                    
                    is_channel = isinstance(entity, Channel) and not entity.megagroup
                    is_group = (isinstance(entity, Channel) and entity.megagroup) or isinstance(entity, Chat)
                    is_bot = isinstance(entity, User) and entity.bot
                    is_private_user = isinstance(entity, User) and not entity.bot and not entity.is_self

                    if clean_type in ['leave_channels', 'full_clean'] and is_channel:
                        await dialog.delete(); report['channels'] += 1; action_taken = True
                    elif clean_type in ['leave_groups', 'full_clean'] and is_group:
                        await dialog.delete(); report['groups'] += 1; action_taken = True
                    elif clean_type in ['delete_bots', 'full_clean'] and is_bot:
                        await client(functions.messages.DeleteHistoryRequest(peer=entity, max_id=0, just_clear=True, revoke=True)); report['bots'] += 1; action_taken = True
                    elif clean_type in ['delete_private_no_contact', 'full_clean'] and is_private_user and not getattr(entity, 'contact', False):
                        await client(functions.messages.DeleteHistoryRequest(peer=entity, max_id=0, just_clear=True, revoke=True)); report['private'] += 1; action_taken = True

                    if action_taken: await asyncio.sleep(0.5)

                except Exception as e_inner:
                    logger.warning(f"Single cleaner error for dialog {dialog.id} on {phone}: {e_inner}")
                    report['errors'] += 1

        final_report_text = _("cleaner_completed", user_id, phone=phone)
        if report['channels'] > 0: final_report_text += f"- {_('channels_left', user_id)}: `{report['channels']}`\n"
        if report['groups'] > 0: final_report_text += f"- {_('groups_left', user_id)}: `{report['groups']}`\n"
        if report['bots'] > 0: final_report_text += f"- {_('bot_chats_deleted', user_id)}: `{report['bots']}`\n"
        if report['private'] > 0: final_report_text += f"- {_('private_chats_deleted', user_id)}: `{report['private']}`\n"
        if report['deleted_contacts'] > 0: final_report_text += f"- {_('deleted', user_id)} {_('contacts', user_id)}: `{report['deleted_contacts']}`\n"
        if report['errors'] > 0: final_report_text += f"- {_('errors_occurred', user_id)}: `{report['errors']}`"
        
        log_activity(phone, f"{_('single_cleaner_log', owner_id)}: {clean_type}", json.dumps(report))
        await msg.edit_text(final_report_text, parse_mode=constants.ParseMode.MARKDOWN)

    except Exception as e:
        await msg.edit_text(_("cleaner_failed_error", user_id, error=e), parse_mode=constants.ParseMode.MARKDOWN)
    finally:
        pass

    await asyncio.sleep(4)
    return await go_back(update, context)

# ==============================================================================
# ||                   دوال عرض الجلسات النشطة وإدارة 2FA                     ||
# ==============================================================================

async def handle_active_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE, client, phone, owner_id):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    await push_state(context, handle_active_sessions, query.data)
    msg = await query.message.edit_text(_("getting_active_sessions", user_id))
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await msg.edit_text(_("account_needs_login_alert", user_id))
            return MANAGE_ACCOUNT

        account = get_account_by_phone(phone, owner_id)
        account_name = account['first_name'] or account['username'] or ""

        result = await client(functions.account.GetAuthorizationsRequest())
        
        local_timezone = pytz.timezone("Asia/Damascus")
        
        sessions_text_parts = []
        has_other_sessions = False

        header = _("active_sessions_header", user_id, phone=phone, account_name=account_name)
        
        for auth in sorted(result.authorizations, key=lambda a: a.hash == 0, reverse=True):
            is_current = auth.hash == 0
            if not is_current:
                has_other_sessions = True
            
            created_local = auth.date_created.astimezone(local_timezone)
            active_local = auth.date_active.astimezone(local_timezone)

            time_since_creation = datetime.now(local_timezone) - created_local
            days = time_since_creation.days
            total_seconds = time_since_creation.seconds
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            creation_age_str = _('session_age_full_detail', user_id, d=days, h=hours, m=minutes, s=seconds)
            
            creation_date_str = created_local.strftime('%Y-%m-%d %I:%M %p')
            active_date_str = active_local.strftime('%Y-%m-%d %I:%M %p')

            session_info = (
                f"{_('device', user_id)}: `{auth.device_model}`" + (f" **({_('current_bot_session', user_id)})**" if is_current else "") + "\n"
                f"{_('platform', user_id)}: `{auth.platform} | {auth.system_version}`\n"
                f"{_('application', user_id)}: `{auth.app_name} v{auth.app_version}`\n"
                f"{_('ip_address', user_id)}: `{auth.ip}` ({_('country', user_id)}: `{auth.country}`)\n"
                f"{_('creation_date', user_id)}: `{creation_date_str}` ({_('before', user_id, age=creation_age_str)})\n"
                f"{_('last_activity', user_id)}: `{active_date_str}`"
            )
            sessions_text_parts.append(session_info)

        full_text = header + "\n\n———————————\n\n".join(sessions_text_parts)
        
        keyboard = []
        if has_other_sessions:
            keyboard.append([InlineKeyboardButton(_("delete_other_sessions_button", user_id), callback_data="mng:reset_auths_confirm")])
            
        keyboard.append([InlineKeyboardButton(_("go_back_button", user_id), callback_data="go_back")])
        
        await msg.edit_text(full_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error in handle_active_sessions for {phone}: {e}")
        await msg.edit_text(_("error_getting_sessions", user_id, error=e))
    finally:
        pass
    
    return MANAGE_ACCOUNT

# ==============================================================================
# ||                   [جديد] قسم إدارة 2FA المطور                         ||
# ==============================================================================


# ... (الكود الموجود لديك) ...
async def tfa_handle_submenu_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    owner_id = query.from_user.id
    phone = context.user_data['selected_phone'] # نحتاج رقم الهاتف لجلب كلمة المرور
    action_parts = query.data.split(':')
    action = action_parts[1]

    if action == "view_status":
        await query.answer()
        return TFA_MENU

    elif action == "change_pass":
        password_info = context.user_data.get('tfa_password_info')
        if password_info.has_password:
            # هنا نطلب كلمة المرور الحالية للتحقق قبل التغيير
            await query.message.edit_text(_("tfa_account_protected", owner_id),
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("cancel_button", owner_id), callback_data="go_back")]]))
            return SET_NEW_PASSWORD # حالة تنتظر كلمة المرور الحالية
        else:
            await query.message.edit_text(_("tfa_account_not_protected", owner_id),
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("cancel_button", owner_id), callback_data="go_back")]]))
            return TFA_GET_NEW_PASS # حالة تنتظر كلمة المرور الجديدة للتفعيل

    # ... (الكود الموجود لديك) ...
    elif action == "change_email":
        password_info = context.user_data.get('tfa_password_info')
        if not password_info.has_password:
            await query.answer("🔐 يجب تفعيل الحماية بكلمة مرور أولاً!", show_alert=True)
            return TFA_MENU
        
        saved_2fa_info = get_2fa_password_info(owner_id, phone)
        
        current_password_known = False
        if saved_2fa_info and saved_2fa_info['password_encrypted']:
            decrypted_password = decrypt_password(saved_2fa_info['password_encrypted'])
            if decrypted_password != "DECRYPTION_FAILED":
                context.user_data['tfa_current_password_str'] = decrypted_password
                current_password_known = True
            else:
                await query.answer("❌ فشل فك تشفير كلمة المرور المحفوظة. يرجى إدخالها يدوياً.", show_alert=True)
        
        if current_password_known:
            await query.answer("✅ تم جلب كلمة المرور المحفوظة تلقائياً.")
            # 🚨 تغيير: ننتقل مباشرة إلى دالة عرض قائمة الإيميلات (tfa_select_recovery_email_from_list)
            # هذه الدالة يجب أن تُرسل رسالة جديدة، وليس تعديل الرسالة السابقة.
            return await tfa_select_recovery_email_from_list(update, context)
        else:
            await query.message.edit_text("🔑 لم يتم العثور على كلمة المرور في البوت. يرجى إدخال كلمة مرور التحقق بخطوتين الحالية لحساب تيليجرام.")
            return TFA_CHANGE_EMAIL_GET
# ... (بقية الكود) ...

    
    elif action == "disable":
        password_info = context.user_data.get('tfa_password_info')
        if not password_info.has_password:
            await query.answer("🔐 الحماية معطلة بالفعل!", show_alert=True)
            return TFA_MENU
        await query.message.edit_text(_("tfa_disable_prompt", owner_id))
        return TFA_DISABLE_GET_PASS

    return TFA_MENU
# ... (بقية الكود الموجود لديك) ...


async def tfa_change_recovery_email_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_email = update.message.text
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    # Use the stored string password, not the PasswordKdfAlgo object
    current_2fa_password = context.user_data.get('current_password_2fa') # <== IMPORTANT CHANGE HERE
    client: TelegramClient = context.user_data['client']

    msg = await update.message.reply_text(_("tfa_changing_password", owner_id))
    try:
        # We need the current password (string) to change the email
        # Use a lambda for the callback so it can access variables from this scope
        await client.edit_2fa(
            current_password=current_2fa_password,
            new_email=new_email,
            email_code_callback=lambda: find_telegram_code_in_gmail(new_email, decrypt_password(get_import_email_by_address(owner_id, new_email)['app_password_encrypted']))
        )
        await msg.edit_text(_("tfa_email_change_success", owner_id))
        log_activity(phone, "تغيير بريد 2FA", "نجاح")

    except EmailUnconfirmedError:
        # This block might not be fully reached if email_code_callback is used,
        # but kept for robustness or if the callback itself raises this.
        await msg.edit_text(_("2fa_email_verify_auto_attempt", owner_id))
        # The callback itself handles the auto-fetch logic now.
        # If it fails, an exception will be raised and caught by the outer 'except Exception'.
        await msg.edit_text(_("2fa_email_verify_auto_fail", owner_id))
        log_activity(phone, "تغيير بريد 2FA", "فشل الجلب التلقائي")

    except Exception as e:
        await msg.edit_text(_("tfa_email_change_failed", owner_id, error=e))
        log_activity(phone, "فشل تغيير بريد 2FA", str(e))
    # Removed the asyncio.sleep and go_back to prevent automatic return.
    # The conversation will stay in the current state or naturally end based on Telegram's behavior.
    return TFA_CHANGE_EMAIL_GET # Stay in the same state or return to the menu manually


async def tfa_disable_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    client: TelegramClient = context.user_data['client']

    msg = await update.message.reply_text(_("tfa_changing_password", owner_id))
    try:
        # To disable, we set new_password to an empty string
        await client.edit_2fa(current_password=password, new_password="")
        await msg.edit_text(_("tfa_disable_success", owner_id))
        log_activity(phone, "تعطيل 2FA", "نجاح")
    except Exception as e:
        await msg.edit_text(_("tfa_disable_failed", owner_id, error=e))
        log_activity(phone, "فشل تعطيل 2FA", str(e))

    await asyncio.sleep(2)
    return await go_back(update, context)


async def tfa_start_management(update: Update, context: ContextTypes.DEFAULT_TYPE, client: TelegramClient):
    user_id = update.effective_user.id
    await push_state(context, tfa_start_management, 'mng:manage_2fa')
    message_to_edit = update.callback_query.message if update.callback_query else update.message
    msg = await message_to_edit.edit_text(_("tfa_checking_status", user_id))

    try:
        await client.connect()
        password_info = await client(functions.account.GetPasswordRequest())
        context.user_data['client'] = client

        if password_info.has_password:
            await msg.edit_text(_("tfa_account_protected", user_id),
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("cancel_button", user_id), callback_data="go_back")]]))
            return SET_NEW_PASSWORD
        else:
            await msg.edit_text(_("tfa_account_not_protected", user_id),
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("cancel_button", user_id), callback_data="go_back")]]))
            return TFA_GET_NEW_PASS

    except Exception as e:
        await msg.edit_text(_("unexpected_error", user_id, error=e))
        return ConversationHandler.END

# ... (الكود الموجود لديك) ...
async def tfa_change_password_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # 🚨 التعديل هنا: استخدام نفس اسم المفتاح
    context.user_data['current_password_2fa'] = update.message.text # <== تأكد أن هذا السطر موجود بهذا الشكل
    await update.message.reply_text(_("tfa_enter_current_password", user_id))
    return CONFIRM_NEW_PASSWORD
# ... (بقية الكود الموجود لديك) ...


# ... (الكود الموجود لديك) ...
async def tfa_change_password_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_password = update.message.text
    current_password = context.user_data['current_password_2fa']
    phone = context.user_data['selected_phone']
    client: TelegramClient = context.user_data['client'] # العميل موجود في السياق من تفا_ماناجمنت_مينو_ستارت
    owner_id = update.effective_user.id

    msg = await update.message.reply_text(_("tfa_changing_password", owner_id))
    try:
        # لا نحتاج client.connect() هنا لأنه يتم توصيله في tfa_management_menu_start
        # ولكن من الجيد التأكد من أنه مصرح به إذا لم يكن هذا مؤكداً
        if not await client.is_user_authorized():
            raise Exception(_("account_needs_login_alert", owner_id))

        await client.edit_2fa(current_password=current_password, new_password=new_password)
        save_2fa_password(owner_id, phone, new_password, DEFAULT_2FA_HINT, None)
        
        log_activity(phone, _("change_2fa_log", owner_id), _("password_change_success_log", owner_id))
        await msg.edit_text(_("tfa_password_change_success", owner_id))
    except PasswordHashInvalidError:
        await msg.edit_text(_("tfa_invalid_current_password", owner_id))
    except Exception as e:
        log_activity(phone, _("change_2fa_log", owner_id), f"{_('failed', owner_id)}: {e}")
        await msg.edit_text(_("tfa_fatal_error", owner_id, error=e))
    finally:
        await asyncio.sleep(2)
        # 🚨 التعديل هنا: إرسال رسالة جديدة مع القائمة بدلاً من محاولة التعديل
        await update.effective_chat.send_message(
            _("returned_to_main_menu", owner_id), # يمكن استخدام رسالة عامة للعودة
            reply_markup=await get_main_keyboard(owner_id) # إرسال لوحة المفاتيح الرئيسية
        )
        return ConversationHandler.END # إنهاء المحادثة
# ... (بقية الكود الموجود لديك) ...


# ... (الكود الموجود لديك) ...
async def tfa_set_new_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone = context.user_data['selected_phone']
    new_password = update.message.text
    context.user_data['new_password'] = new_password

    # 🚨🚨🚨 التعديل هنا: استخدام client من context.user_data 🚨🚨🚨
    client: TelegramClient = context.user_data['client'] 
    
    msg = await update.message.reply_text(_("tfa_enabling_2fa", user_id))
    try:
        # client.connect() لا حاجة لها هنا إذا تم الاتصال في tfa_management_menu_start
        if not await client.is_user_authorized():
            raise Exception(_("account_needs_login_alert", user_id))

        await client.edit_2fa(new_password=new_password, hint=DEFAULT_2FA_HINT)
        save_2fa_password(user_id, phone, new_password, DEFAULT_2FA_HINT, None)
        
        log_activity(phone, _("enable_2fa_log", user_id), _("protection_enabled_success_log", user_id))
        await msg.edit_text(_("tfa_email_confirmed_success", user_id))
    except Exception as e:
        log_activity(phone, _("enable_2fa_log", user_id), f"Failed: {e}")
        await msg.edit_text(_("unexpected_error", user_id, error=e))
    finally:
        await asyncio.sleep(2)
        await update.effective_chat.send_message(
            _("returned_to_main_menu", user_id),
            reply_markup=await get_main_keyboard(user_id)
        )
        return ConversationHandler.END
# ... (بقية الكود الموجود لديك) ...


async def tfa_skip_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data['password_hint'] = ""
    await update.message.reply_text(_("tfa_hint_skipped", user_id))
    return TFA_GET_RECOVERY_EMAIL

async def tfa_set_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data['password_hint'] = update.message.text
    await update.message.reply_text(_("tfa_enter_recovery_email", user_id))
    return TFA_GET_RECOVERY_EMAIL

# ... (الكود الموجود لديك) ...
async def tfa_set_recovery_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email_address = update.message.text
    user_id = update.effective_user.id
    context.user_data['recovery_email'] = email_address
    phone = context.user_data['selected_phone']
    client: TelegramClient = context.user_data['client']
    new_password = context.user_data['new_password']
    context.user_data['current_password_2fa'] = new_password # <== Add this line, as this becomes the current password
    hint = context.user_data['password_hint']
    owner_id = update.effective_user.id

    msg = await update.message.reply_text(_("tfa_enabling_2fa", user_id))
    try:
        # 🚨🚨🚨 التعديل الرئيسي هنا: إضافة email_code_callback 🚨🚨🚨
        # تعريف دالة Callback لجلب الكود بشكل غير متزامن
        async def get_email_code_for_2fa_setup(is_resend=False): # <== أضف is_resend=False
            await msg.edit_text(_("2fa_email_verify_auto_attempt", user_id))
            # ... (بقية كود الدالة) ...
            import_emails = get_import_emails_by_owner(owner_id)
            fetched_code = None

            # جلب كلمة مرور التطبيق للإيميل الذي تم إدخاله للتو
            # لا نستخدم get_import_email_by_owner هنا لأن الإيميل قد لا يكون محفوظاً بعد
            # بدلاً من ذلك، سنحاول البحث عنه ضمن الإيميلات المحفوظة أو نستخدم الإيميل المدخل مباشرة.
            
            # إذا كان الإيميل المدخل موجوداً ضمن الإيميلات المحفوظة لدى المستخدم، نستخدم كلمة مرور التطبيقات الخاصة به.
            # وإلا، فالبوت لا يعرف كلمة مرور التطبيقات لهذا الإيميل، ولن يتمكن من جلب الكود تلقائياً.
            
            target_email_row = next((e for e in import_emails if e['email_address'] == email_address), None)

            if target_email_row:
                app_pass = decrypt_email_password_base64(target_email_row['app_password_encrypted']) # <== استخدام دالة فك الترميز الجديدة
                if app_pass != "DECRYPTION_FAILED":
                    code = await find_telegram_code_in_gmail(email_address, app_pass)
                    if code:
                        fetched_code = code
            
            if fetched_code:
                await msg.edit_text(_("2fa_email_verify_auto_success", user_id))
                return fetched_code
            else:
                # إذا فشل الجلب التلقائي، نثير استثناءً لتليثون يطلب الكود يدوياً
                await msg.edit_text(_("2fa_email_verify_auto_fail", user_id))
                raise EmailUnconfirmedError("Auto-fetch failed, manual code required.")

        # استدعاء edit_2fa مع email_code_callback
        await client.edit_2fa(
            new_password=new_password,
            hint=hint,
            email=email_address, # <== تم التغيير هنا من email إلى new_email في هذا السياق
            email_code_callback=get_email_code_for_2fa_setup
        )
        
        log_activity(phone, _("enable_2fa_log", user_id), _("protection_enabled_success_log", user_id))
        await msg.edit_text(_("tfa_email_confirmed_success", user_id))
        await asyncio.sleep(2)
        await go_back(update, context)
        return ConversationHandler.END

    except EmailUnconfirmedError:
        # هذا الجزء سيتم الوصول إليه إذا فشلت get_email_code_for_2fa_setup في جلب الكود
        log_activity(phone, _("enable_2fa_log", user_id), "Auto-fetch failed. Waiting for manual code.")
        await msg.edit_text(_("tfa_email_unconfirmed", user_id, email=email_address))
        return TFA_GET_EMAIL_CODE

    except Exception as e:
        log_activity(phone, _("enable_2fa_log", user_id), f"Failed: {e}")
        await msg.edit_text(_("unexpected_error", user_id, error=e))
        await asyncio.sleep(2)
        await go_back(update, context)
        return ConversationHandler.END
# ... (بقية الكود الموجود لديك) ...



async def tfa_confirm_email_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    user_id = update.effective_user.id
    phone = context.user_data['selected_phone']
    client: TelegramClient = context.user_data['client']
    new_password = context.user_data['new_password']

    msg = await update.message.reply_text(_("tfa_confirming_code", user_id))
    try:
        await client.edit_2fa(new_password=new_password, code=code)
        log_activity(phone, _("enable_2fa_log", user_id), _("email_confirmed_protection_enabled_log", user_id))
        await msg.edit_text(_("tfa_email_confirmed_success", user_id))
    except Exception as e:
        log_activity(phone, _("enable_2fa_log", user_id), _("failed_code_confirmation", user_id, error=e))
        await msg.edit_text(_("tfa_code_confirmation_failed", user_id, error=e))
    finally:
        await asyncio.sleep(2)
        await go_back(update, context)
    return ConversationHandler.END

# ==============================================================================
# ||                        قسم الردود الآلية                          ||
# ==============================================================================

async def autoreply_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    phone = query.data.split(':')[2]
    owner_id = query.from_user.id
    context.user_data['selected_phone'] = phone
    await push_state(context, autoreply_menu_start, query.data)

    replies = get_auto_replies(owner_id, phone)
    text = _("autoreply_menu_title", user_id, phone=phone)
    keyboard = [[InlineKeyboardButton(_("add_new_reply_button", user_id), callback_data="autoreply:add")]]

    if not replies:
        text += _("no_auto_replies", user_id)
    else:
        text += _("replies_list", user_id)
        for reply in replies:
            keyboard.append([
                InlineKeyboardButton(f"🔑 `{reply['keyword']}`", callback_data=f"noop"),
                InlineKeyboardButton(_("delete_button", user_id), callback_data=f"autoreply:delete:{reply['id']}")
            ])

    keyboard.append([InlineKeyboardButton(_("back_to_account_management", user_id), callback_data="go_back")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)
    return AUTOREPLY_MENU

async def autoreply_handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    action = query.data.split(':')[1]
    phone = context.user_data['selected_phone']

    if action == 'add':
        await query.message.edit_text(_("enter_keyword", user_id))
        return AUTOREPLY_GET_KEYWORD
    
    elif action == 'delete':
        reply_id = int(query.data.split(':')[2])
        remove_auto_reply(reply_id)
        await query.answer(_("autoreply_deleted", user_id), show_alert=True)
        # --- هذا هو السطر الذي تم إصلاحه ---
        # تم تمرير update الكامل بدلاً من query فقط
        return await mock_update_and_call(autoreply_menu_start, update, context, f"autoreply:menu:{phone}", push=False)
        # --- نهاية الإصلاح ---
    
    return AUTOREPLY_MENU


async def autoreply_get_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    context.user_data['autoreply_keyword'] = update.message.text
    await update.message.reply_text(_("enter_response_message", user_id))
    return AUTOREPLY_GET_RESPONSE

async def autoreply_get_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyword = context.user_data.pop('autoreply_keyword', None)
    if not keyword: return ConversationHandler.END 

    response_msg = update.message.text
    phone = context.user_data['selected_phone']
    owner_id = update.effective_user.id

    if add_auto_reply(owner_id, phone, keyword, response_msg):
        await update.message.reply_text(_("autoreply_add_success", owner_id))
        log_activity(phone, _("add_autoreply_log", owner_id), _("keyword", owner_id, keyword=keyword))
    else:
        await update.message.reply_text(_("autoreply_already_exists", owner_id))

    await go_back(update, context)
    return ConversationHandler.END

# ==============================================================================
# ||                        قسم إدارة البروكسيات                        ||
# ==============================================================================
async def manage_proxies_start(update: Update, context: ContextTypes.DEFAULT_TYPE, from_account_management=False):
    query = update.callback_query
    user_id = query.from_user.id
    page = 0
    if query.data and ':' in query.data:
        try:
            page = int(query.data.split(':')[1])
        except (ValueError, IndexError):
            page = 0
    context.user_data['proxy_page'] = page
    await query.answer()

    if not from_account_management:
        await push_state(context, manage_proxies_start, query.data)

    proxies = get_all_proxies_from_db()
    text = _("manage_proxies_title", user_id)
    keyboard_buttons = []
    phone_to_assign = context.user_data.get('phone_to_assign_proxy')

    if phone_to_assign:
        text = _("assign_proxy_to_account", user_id, phone=phone_to_assign)
        keyboard_buttons.append(InlineKeyboardButton(_("unassign_proxy_button", user_id), callback_data=f"proxy_assign:none"))
    else:
        if not proxies:
            text += _("no_proxies_added", user_id)
        else:
            text += _("available_proxies_list", user_id)

    for p in proxies:
        btn_text = f"🆔{p['id']}: ...{p['hostname'][-15:]}:{p['port']} ({p['usage_count']}👤)"
        callback = f"proxy_details:{p['id']}" if not phone_to_assign else f"proxy_assign:{p['id']}"
        keyboard_buttons.append(InlineKeyboardButton(btn_text, callback_data=callback))

    keyboard_list = create_paginated_keyboard(keyboard_buttons, page, 5, 'manage_proxies_start', len(proxies), user_id)

    back_button = InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')
    if not phone_to_assign:
        keyboard_list.insert(0, [InlineKeyboardButton(_("add_new_proxy_button", user_id), callback_data="proxy_add_start")])
        keyboard_list.append([InlineKeyboardButton(_("back_to_main_menu", user_id), callback_data='back_to_main')])
    else:
        keyboard_list.append([back_button])

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard_list), parse_mode=constants.ParseMode.MARKDOWN)

    if from_account_management:
        return ASSIGN_PROXY_SELECT_ACCOUNT
    else:
        return MANAGE_PROXIES

async def add_proxy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    keyboard = [[InlineKeyboardButton(_("cancel_button", user_id), callback_data=f"manage_proxies_start:{context.user_data.get('proxy_page', 0)}")]]
    await query.message.edit_text(
        _("proxy_input_instructions", user_id),
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)
    return ADD_PROXY

async def process_proxy_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    proxy_str = update.message.text
    success, message = add_proxy_to_db(proxy_str)
    await update.message.reply_text(message)
    await mock_update_and_call(manage_proxies_start, update, context, f"manage_proxies_start:0", push=False)
    return MANAGE_PROXIES

async def proxy_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    proxy_id = int(query.data.split(':')[1])
    proxy = get_proxy_by_id(proxy_id)
    if not proxy:
        await query.message.edit_text(_("proxy_not_found", user_id))
        return MANAGE_PROXIES

    text = (_("proxy_details_title", user_id, id=proxy['id'])
            + f"```\n{proxy['proxy_str']}\n```\n"
            + _("proxy_usage", user_id, count=proxy['usage_count']))
    keyboard = [
        [InlineKeyboardButton(_("delete_proxy_button", user_id), callback_data=f"proxy_delete:{proxy_id}")],
        [InlineKeyboardButton(_("back_to_proxies_list", user_id), callback_data='go_back')]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)
    return MANAGE_PROXIES

async def delete_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    proxy_id = int(query.data.split(':')[1])
    remove_proxy_from_db(proxy_id)
    await query.answer(_("proxy_deleted", user_id), show_alert=True)
    
    # --- هذا هو السطر الذي تم إصلاحه ---
    # تم تمرير update الكامل بدلاً من query فقط
    return await mock_update_and_call(manage_proxies_start, update, context, f"manage_proxies_start:{context.user_data.get('proxy_page',0)}", push=False)
    # --- نهاية الإصلاح ---


async def assign_proxy_to_selected_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    proxy_id = query.data.split(':')[1]
    proxy_id = int(proxy_id) if proxy_id != 'none' else None
    
    owner_id = query.from_user.id
    phone = context.user_data.get('phone_to_assign_proxy')
    if not phone:
        await query.message.edit_text(_("error_account_not_selected", user_id))
        return ConversationHandler.END
        
    assign_proxy_to_account(phone, owner_id, proxy_id)
    await query.message.edit_text(_("proxy_assign_success", user_id))
    await asyncio.sleep(1)
    
    context.user_data.pop('phone_to_assign_proxy', None)
    return await go_back(update, context)

# ==============================================================================
# ||             قسم إدارة جهات الاتصال لحساب فردي (جديد)                    ||
# ==============================================================================

async def show_single_contact_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the contact management menu for a single account."""
    query = update.callback_query
    user_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    await query.answer()

    await push_state(context, show_single_contact_menu, query.data)

    keyboard = [
        [
            InlineKeyboardButton(_("add_contacts_single_button", user_id), callback_data="s_contacts:add_prompt"),
        ],
        [InlineKeyboardButton(_("delete_all_contacts_single_button", user_id), callback_data="s_contacts:delete_confirm")],
        [InlineKeyboardButton(_("export_contacts_single_button", user_id), callback_data="s_contacts:export")],
        [InlineKeyboardButton(_("back_to_account_management", user_id), callback_data=f"select_acc:{phone}")]
    ]
    
    await query.message.edit_text(
        text=_("single_contact_menu_title", user_id, phone=phone),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SINGLE_CONTACT_MENU

async def single_add_contacts_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the list of contacts to add for a single account."""
    query = update.callback_query
    await query.answer()
    context.user_data['contact_add_mode'] = 'single'
    await query.message.edit_text(_("enter_contacts_to_add", query.from_user.id))
    return SINGLE_CONTACT_GET_LIST

async def single_add_from_file_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks the user to send the contact file."""
    query = update.callback_query
    await query.answer()
    context.user_data['contact_add_mode'] = 'single'
    await query.message.edit_text(_("send_contact_file_prompt", query.from_user.id))
    return SINGLE_CONTACT_GET_FILE

async def add_contacts_from_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes an uploaded contact file."""
    document = update.message.document
    if not document or not document.file_name.lower().endswith('.txt'):
        await update.message.reply_text("❌ يرجى إرسال ملف بصيغة .txt فقط.")
        return SINGLE_CONTACT_GET_FILE

    file = await context.bot.get_file(document.file_id)
    file_content_bytes = await file.download_as_bytearray()
    contacts_input = file_content_bytes.decode('utf-8')

    return await execute_single_add_contacts(update, context, contacts_input=contacts_input)

async def execute_single_add_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE, contacts_input: str = None) -> int:
    """Adds contacts to the selected single account from text or file."""
    if contacts_input is None:
        contacts_input = update.message.text
    
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    action_title = _("add_contacts_single_button", owner_id)
    
    msg = await update.message.reply_text(
        _("starting_bulk_task", owner_id, action_type=action_title, count=1)
    )
    
    try:
        words = re.split(r'\s+|,|\n', contacts_input)
        contacts_to_process = [word for word in words if word.strip().startswith('+') or word.strip().startswith('@')]
        
        if not contacts_to_process:
            raise ValueError("No valid phone numbers or usernames found in the input.")

        client = await get_telethon_client(phone, owner_id)
        await client.connect()
        if not await client.is_user_authorized(): raise Exception(_("account_needs_login_alert", owner_id))
        
        success_count, failure_count = 0, 0
        for contact_str in contacts_to_process:
            try:
                if contact_str.startswith('+') and contact_str[1:].isdigit():
                    contact_obj = types.InputPhoneContact(client_id=0, phone=contact_str, first_name=contact_str, last_name='')
                    await client(functions.contacts.ImportContactsRequest(contacts=[contact_obj]))
                else:
                    user_entity = await client.get_entity(contact_str)
                    await client(functions.contacts.AddContactRequest(
                        id=user_entity,
                        first_name=user_entity.first_name or contact_str.replace('@',''),
                        last_name=user_entity.last_name or '',
                        phone="",
                        add_phone_privacy_exception=False
                    ))
                success_count += 1
                log_activity(phone, action_title, f"Successfully added {contact_str}")
            except Exception as inner_e:
                logger.warning(f"Failed to add contact {contact_str} for {phone}: {inner_e}")
                failure_count += 1
            await asyncio.sleep(0.5)

        status = _("bulk_task_final_report", owner_id, action_title=action_title, success_count=success_count, failure_count=failure_count)
        log_activity(phone, action_title, status)

    except Exception as e:
        status = _("story_post_failed", owner_id, error=str(e))
        log_activity(phone, action_title, status)
    
    keyboard = [[InlineKeyboardButton(_("back_to_account_management", owner_id), callback_data=f"select_acc:{phone}")]]
    await msg.edit_text(status, reply_markup=InlineKeyboardMarkup(keyboard))

    return SINGLE_CONTACT_MENU

async def single_delete_contacts_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for final confirmation before deleting all contacts."""
    query = update.callback_query
    user_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(_("yes_delete_now", user_id), callback_data="s_contacts:execute_delete")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data='s_contacts:menu')]
    ]
    await query.message.edit_text(
        _("confirm_delete_all_contacts", user_id, phone=phone), 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SINGLE_CONTACT_CONFIRM_DELETE

async def execute_single_delete_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Deletes all contacts from the selected account."""
    query = update.callback_query
    owner_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    action_title = _("delete_all_contacts_single_button", owner_id)
    await query.answer()
    
    msg = await query.message.edit_text(_("starting_bulk_task", owner_id, action_type=action_title, count=1))
    
    try:
        client = await get_telethon_client(phone, owner_id)
        await client.connect()
        if not await client.is_user_authorized(): raise Exception(_("account_needs_login_alert", owner_id))
        
        contacts = await client(functions.contacts.GetContactsRequest(hash=0))
        if contacts.users:
            await client(functions.contacts.DeleteContactsRequest(id=contacts.users))
            status = _("task_success", owner_id)
        else:
            status = _("no_contacts_to_export", owner_id)
        log_activity(phone, action_title, status)
    except Exception as e:
        status = _("story_post_failed", owner_id, error=str(e))
        log_activity(phone, action_title, status)

    keyboard = [[InlineKeyboardButton(_("back_to_account_management", owner_id), callback_data=f"select_acc:{phone}")]]
    final_text = _("story_final_status", owner_id, status=status)
    await msg.edit_text(final_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return SINGLE_CONTACT_MENU

async def execute_single_export_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Exports contacts for a single account."""
    query = update.callback_query
    owner_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    action_title = _("export_contacts_single_button", owner_id)
    await query.answer()
    
    msg = await query.message.edit_text(_("starting_bulk_task", owner_id, action_type=action_title, count=1))
    
    try:
        client = await get_telethon_client(phone, owner_id)
        await client.connect()
        if not await client.is_user_authorized(): raise Exception(_("account_needs_login_alert", owner_id))
        
        contacts = await client(functions.contacts.GetContactsRequest(hash=0))
        
        export_text = f"--- Contacts for {phone} ---\n"
        if not contacts.users:
            export_text += "لا يوجد جهات اتصال لتصديرها."
        else:
            for user in contacts.users:
                username_str = f"@{user.username}" if user.username else "N/A"
                export_text += f"ID: {user.id}, Name: {user.first_name}, Username: {username_str}\n"
        
        output_file = io.BytesIO(export_text.encode('utf-8'))
        output_file.name = f"contacts_{phone.replace('+', '')}.txt"
        
        await context.bot.send_document(chat_id=owner_id, document=output_file)
        status = _("export_contacts_caption", owner_id, count=len(contacts.users))
        log_activity(phone, action_title, _("success", owner_id))
        
    except Exception as e:
        status = _("story_post_failed", owner_id, error=str(e))
        log_activity(phone, action_title, _("failed", owner_id, error=str(e)))
    
    keyboard = [[InlineKeyboardButton(_("back_to_account_management", owner_id), callback_data=f"select_acc:{phone}")]]
    final_text = _("story_final_status", owner_id, status=status)
    await msg.edit_text(final_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return SINGLE_CONTACT_MENU

# ==============================================================================
# ||                        قسم المهام الآلية والاستخراج (موحد ومصلح)          ||
# ==============================================================================
async def start_bulk_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action_type = query.data.split(':')[1]
    
    context.user_data['bulk_action_type'] = action_type
    context.user_data['selected_accounts'] = set()
    
    return await select_accounts_for_bulk_action(update, context)

# <== تم الإصلاح: دالة التوجيه الرئيسية للمهام الجماعية
async def route_bulk_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action_key = query.data.split(':')[1]

    routing_map = {
        'get_link': bulk_action_get_link,
        'no_link': bulk_action_confirm_no_link,
        'scraper_options': scraper_select_type,
        'cleaner_options': cleaner_options,
        'bulk_export_confirm': bulk_export_confirm,
        'bulk_story_options': bulk_story_get_file,
        'get_bio': bulk_get_bio_prompt,
        'get_name': bulk_get_name_prompt,
        'get_photo': bulk_get_photo_prompt,
        'select_proxy': bulk_select_proxy_prompt,
        'add_contacts': bulk_add_contacts_get_list,
        'delete_contacts': bulk_action_confirm_no_link, # Delete contacts needs confirmation like logout
        'export_contacts': execute_export_contacts
    }
    next_handler = routing_map.get(action_key)

    if next_handler:
        return await next_handler(update, context)
    else:
        await query.message.edit_text("Unknown bulk action.")
        return ConversationHandler.END

# ... (الكود الموجود لديك) ...
def create_multi_select_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, accounts, page, page_size, callback_prefix, total_items):
    selected_set = context.user_data.get('selected_accounts', set())
    user_id = update.effective_user.id
    buttons = []
    for acc in accounts:
        is_selected = acc['phone'] in selected_set
        emoji = "✅" if is_selected else "🔲"
        btn_text = f"{emoji} {acc['phone']}" + (f" ({acc['first_name'] or acc['username'] or _('unknown_name', user_id)})" if acc['first_name'] or acc['username'] else "")
        buttons.append(InlineKeyboardButton(btn_text, callback_data=f"multi_select:{acc['phone']}"))

    keyboard = create_paginated_keyboard(buttons, page, 8, callback_prefix, total_items, user_id)

    control_buttons = [
        InlineKeyboardButton(_("select_all_button", user_id), callback_data="multi_select:all"),
        InlineKeyboardButton(_("invert_selection_button", user_id), callback_data="multi_select:invert"),
        InlineKeyboardButton(_("clear_selection_button", user_id), callback_data="multi_select:none")
    ]
    keyboard.insert(0, control_buttons)

    action_type = context.user_data.get('bulk_action_type')
    continue_text = _("continue_button", user_id, count=len(selected_set))
    
    # 🚨🚨🚨 التعديل هنا: إضافة bulk_2fa إلى callback_map 🚨🚨🚨
    callback_map = {
        'joiner': "bulk_confirm_selection:get_link",
        'leaver': "bulk_confirm_selection:get_link",
        'deleter': "bulk_confirm_selection:no_link",
        'logout': "bulk_confirm_selection:no_link",
        'reset_sessions': "bulk_confirm_selection:no_link",
        'members': "bulk_confirm_selection:scraper_options",
        'cleaner': "bulk_confirm_selection:cleaner_options",
        'bulk_export': 'bulk_confirm_selection:bulk_export_confirm',
        'bulk_story': 'bulk_confirm_selection:bulk_story_options',
        'bulk_bio': 'bulk_confirm_selection:get_bio',
        'bulk_name': 'bulk_confirm_selection:get_name',
        'bulk_photo': 'bulk_confirm_selection:get_photo',
        'bulk_proxy': 'bulk_confirm_selection:select_proxy',
        'add_contacts': 'bulk_confirm_selection:add_contacts',
        'delete_contacts': 'bulk_confirm_selection:delete_contacts',
        'export_contacts': 'bulk_confirm_selection:export_contacts',
        'bulk_2fa': 'bulk_confirm_selection:bulk_2fa_options', # <== أضف هذا السطر
    }
    continue_callback_data = callback_map.get(action_type)

    if continue_callback_data and selected_set:
        keyboard.append([InlineKeyboardButton(continue_text, callback_data=continue_callback_data)])
    
    if context.user_data.get('bulk_action_type') == 'deleter':
        keyboard.append([InlineKeyboardButton(_("cancel_and_return_button", user_id), callback_data="back_to_delete_options")])
    else:
        # 🚨🚨🚨 التعديل هنا: تغيير 'cancel_bulk_selection' إلى 'show_bulk_action_options' 🚨🚨🚨
        keyboard.append([InlineKeyboardButton(_("cancel_and_return_button", user_id), callback_data="show_bulk_action_options")]) # <== تغيير هنا
        
    return InlineKeyboardMarkup(keyboard)

# ... (بقية الكود الموجود لديك) ...


async def select_accounts_for_bulk_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    owner_id = query.from_user.id
    await query.answer()
    
    action_type = context.user_data.get('bulk_action_type')
    await push_state(context, select_accounts_for_bulk_action, f"unified_bulk:{action_type}:start")

    page = context.user_data.get('account_page', 0)
    selected_set = context.user_data.get('selected_accounts', set())
    
    show_all = action_type in ['deleter', 'cleaner']
    accounts = get_accounts_by_owner(owner_id, only_active=not show_all)

    if not accounts:
        # --- هذا هو السطر الذي تم إصلاحه ---
        # تم تغيير user_id إلى owner_id
        await query.message.edit_text(_("no_accounts_selected_cancel", owner_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", owner_id), callback_data='go_back')]]))
        # --- نهاية الإصلاح ---
        return ConversationHandler.END

    if ':' in query.data:
        cb_action, value = query.data.split(':', 1)
        if cb_action == 'multi_select':
            if value == 'all':
                selected_set.update(acc['phone'] for acc in accounts)
            elif value == 'none':
                selected_set.clear()
            elif value == 'invert':
                all_phones = {acc['phone'] for acc in accounts}
                selected_set.symmetric_difference_update(all_phones)
            else:
                selected_set.symmetric_difference_update({value})
            context.user_data['selected_accounts'] = selected_set
        elif 'page' in cb_action:
            try:
                page = int(value)
                context.user_data['account_page'] = page
            except ValueError:
                page = 0

    keyboard = create_multi_select_keyboard(update, context, accounts, page, 8, "select_accounts_for_bulk_action:page", len(accounts))

    action_titles = {
        'joiner': _("join_bulk_button", owner_id),
        'leaver': _("leave_bulk_button", owner_id),
        'deleter': _("remove_account_button_main", owner_id),
        'logout': _("logout_bulk_button", owner_id),
        'reset_sessions': _("bulk_reset_sessions_button", owner_id),
        'members': _("extract_members_button", owner_id),
        'cleaner': _("cleaner_button", owner_id),
        'scheduler': _("scheduled_tasks_button_main", owner_id),
        'bulk_export': _("bulk_export_button_main", owner_id),
        'bulk_story': _("bulk_post_story_button", owner_id),
        'bulk_bio': _("bulk_bio_button", owner_id),
        'bulk_name': _("bulk_name_button", owner_id),
        'bulk_photo': _("bulk_photo_button", owner_id),
        'bulk_proxy': _("bulk_proxy_assign_button", owner_id),
        'add_contacts': _("bulk_add_contacts_button", owner_id),
        'delete_contacts': _("bulk_delete_contacts_button", owner_id),
        'export_contacts': _("export_contacts_button", owner_id),
             'bulk_2fa': _("bulk_2fa_button", owner_id),
    }
    
    await query.message.edit_text(_("select_accounts_for_task", owner_id, action_title=action_titles.get(action_type, _('unknown', owner_id))),
                                  reply_markup=keyboard, parse_mode=constants.ParseMode.MARKDOWN)
    return SELECT_ACCOUNTS_FOR_ACTION



async def bulk_action_get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if not context.user_data.get('selected_accounts'):
        await query.message.edit_text(_("no_accounts_selected_cancel", user_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]))
        return ConversationHandler.END
    
    await query.message.edit_text(_("enter_group_link", user_id))
    return GET_LINK_FOR_BULK_ACTION

async def bulk_action_confirm_no_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    selected_accounts = context.user_data.get('selected_accounts', set())
    action_type = context.user_data['bulk_action_type']

    if not selected_accounts:
        await query.message.edit_text(_("no_accounts_selected_cancel", user_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]))
        return ConversationHandler.END

    warning_text = ""
    if action_type == 'deleter':
        delete_type_text = _("deleting_account_type_full", user_id) if context.user_data.get('bulk_delete_type') == 'full' else _("deleting_account_type_local", user_id)
        warning_text = _("warning_bulk_delete", user_id, delete_type_text=delete_type_text, count=len(selected_accounts))
    elif action_type == 'logout':
        warning_text = _("warning_bulk_logout", user_id, count=len(selected_accounts))
    elif action_type == 'reset_sessions':
        warning_text = _("confirm_bulk_reset_sessions", user_id, count=len(selected_accounts))
    elif action_type == 'delete_contacts':
        warning_text = _("confirm_bulk_delete_contacts", user_id, count=len(selected_accounts))

    keyboard = [
        [InlineKeyboardButton(_("yes_im_sure", user_id), callback_data=f"execute_bulk_no_link")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data="go_back")]
    ]
    await query.message.edit_text(f"{warning_text}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)
    return CONFIRM_BULK_NO_LINK_ACTION

async def execute_bulk_join_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    owner_id = update.effective_user.id
    context.user_data['target_link'] = link
    action_type = context.user_data['bulk_action_type']
    selected_accounts = list(context.user_data['selected_accounts'])

    action_titles = {
        'joiner': _("join_bulk_button", owner_id),
        'leaver': _("leave_bulk_button", owner_id)
    }
    translated_action = action_titles.get(action_type, action_type)
    
    msg = await update.message.reply_text(
        _("starting_bulk_task", owner_id, action_type=translated_action, count=len(selected_accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    
    report_lines = [f"**{_('bulk_task_report_header', owner_id, action_type=translated_action, link=link)}**\n"]
    success_count, failure_count = 0, 0
    
    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("starting_bulk_task", owner_id, action_type=translated_action, count=len(selected_accounts)), owner_id)
        client = await get_telethon_client(phone, owner_id)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception(_("account_needs_login_alert", owner_id))
            
            entity = await client.get_entity(link)
            if action_type == 'joiner':
                await client(functions.channels.JoinChannelRequest(entity))
                log_activity(phone, _("bulk_join_log", owner_id), _("success_in_joining", owner_id, link=link))
                report_lines.append(f"✅ `{phone}`: {_('task_success', owner_id)}")
                success_count += 1
            elif action_type == 'leaver':
                await client(functions.channels.LeaveChannelRequest(entity))
                log_activity(phone, _("bulk_leave_log", owner_id), _("success_in_leaving", owner_id, link=link))
                report_lines.append(f"✅ `{phone}`: {_('task_success', owner_id)}")
                success_count += 1

        except UserAlreadyParticipantError:
            report_lines.append(f"🟡 `{phone}`: {_('account_already_member', owner_id)}")
            failure_count += 1
        except UserNotParticipantError:
            report_lines.append(f"🟡 `{phone}`: {_('account_not_member', owner_id)}")
            failure_count += 1
        except Exception as e:
            escaped_error = markdown_v2(str(e))
            report_lines.append(f"❌ `{phone}`: {_('task_failure', owner_id, error=escaped_error)}")
            log_activity(phone, f"{_('bulk_task', owner_id)} ({action_type})", _("failed", owner_id, error=e, link=link))
            failure_count += 1
        finally:
            pass # Client managed by pool
            
    final_report_text = _("bulk_task_final_report", owner_id, 
                          action_title=translated_action, 
                          success_count=success_count, 
                          failure_count=failure_count)
    
    keyboard = [[
        InlineKeyboardButton(
            _("back_to_bulk_menu", owner_id), 
            callback_data="show_bulk_action_options"
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(final_report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    await cleanup_conversation(context)
    return ConversationHandler.END

async def execute_bulk_no_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    owner_id = query.from_user.id
    action_type = context.user_data['bulk_action_type']
    selected_accounts = list(context.user_data.get('selected_accounts', []))
    
    action_titles = {
        'deleter': _("remove_account_button_main", owner_id),
        'logout': _("logout_bulk_button", owner_id),
        'reset_sessions': _("bulk_reset_sessions_button", owner_id),
        'delete_contacts': _("bulk_delete_contacts_button", owner_id)
    }
    translated_action = action_titles.get(action_type, action_type)

    msg = await query.message.edit_text(
        _("starting_bulk_task", user_id, action_type=translated_action, count=len(selected_accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    
    report_lines = [f"**{_('bulk_task_report_header_no_link', user_id, action_type=translated_action)}**\n"]
    success_count, failure_count = 0, 0
    
    delete_type = context.user_data.get('bulk_delete_type', 'full')

    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", user_id, current=i+1, total=len(selected_accounts), phone=phone), user_id)
        try:
            client = await get_telethon_client(phone, owner_id)
            await client.connect()
            if not await client.is_user_authorized():
                # For deletion, we can continue even if not authorized
                if action_type != 'deleter':
                    raise Exception(_("account_needs_login_alert", user_id))

            if action_type == 'deleter':
                if delete_type == 'full' and await client.is_user_authorized():
                    try:
                        await client.log_out()
                    except Exception as e:
                        logger.warning(f"Could not log out {phone} before deleting: {e}")
                
                session_path = os.path.join(SESSIONS_DIR, f"{owner_id}_{phone}.session")
                if os.path.exists(session_path): os.remove(session_path)
                remove_account_from_db(phone, owner_id)
                report_lines.append(f"✅ `{phone}`: {_('delete_success', user_id)} ({delete_type})")
                success_count += 1
            
            elif action_type == 'logout':
                await client.log_out()
                update_account_status(phone, owner_id, 'NEEDS_LOGIN')
                log_activity(phone, "bulk_logout", _("success", owner_id))
                report_lines.append(f"✅ `{phone}`: {_('logout_success', user_id)}")
                success_count += 1

            elif action_type == 'reset_sessions':
                await client(functions.auth.ResetAuthorizationsRequest())
                log_activity(phone, "bulk_reset_sessions", _("success", owner_id))
                report_lines.append(f"✅ `{phone}`: {_('all_other_sessions_deleted_success', user_id)}")
                success_count += 1
                
            elif action_type == 'delete_contacts':
                contacts = await client(functions.contacts.GetContactsRequest(hash=0))
                if contacts.users:
                    await client(functions.contacts.DeleteContactsRequest(id=contacts.users))
                log_activity(phone, "bulk_delete_contacts", f"Deleted {len(contacts.users)} contacts.")
                report_lines.append(f"✅ `{phone}`: {_('task_success', user_id)}")
                success_count += 1

        except Exception as e:
            escaped_error = markdown_v2(str(e))
            report_lines.append(f"❌ `{phone}`: {_('task_failure', user_id, error=escaped_error)}")
            failure_count += 1
        finally:
            pass

    final_report_text = _("bulk_task_final_report", user_id, 
                          action_title=translated_action, 
                          success_count=success_count, 
                          failure_count=failure_count)
    
    keyboard = [[InlineKeyboardButton(_("back_to_bulk_menu", owner_id), callback_data="show_bulk_action_options")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(final_report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    await cleanup_conversation(context)
    return ConversationHandler.END

async def scraper_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if not context.user_data.get('selected_accounts'):
        await query.message.edit_text(_("no_accounts_selected_cancel", user_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]))
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton(_("all_members", user_id), callback_data="scraper_set_type:all")],
        [InlineKeyboardButton(_("recent_active_members", user_id), callback_data="scraper_set_type:recent")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data="go_back")],
    ]
    await query.message.edit_text(_("scraper_options_title", user_id), reply_markup=InlineKeyboardMarkup(keyboard))
    return SCRAPER_SELECT_TYPE

async def scraper_get_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    scraper_type = query.data.split(':')[1]
    context.user_data['scraper_type'] = scraper_type
    
    await query.message.edit_text(_("enter_scraper_limit", user_id))
    return SCRAPER_GET_LIMIT

async def scraper_get_group_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        limit = int(update.message.text)
        if limit < 0: raise ValueError
        context.user_data['scraper_limit'] = limit
    except ValueError:
        await update.message.reply_text(_("invalid_number_input", user_id))
        return SCRAPER_GET_LIMIT
    
    await update.message.reply_text(_("enter_group_link_scraper", user_id))
    return CONFIRM_BULK_ACTION

async def execute_member_scraper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    owner_id = update.effective_user.id
    phone = list(context.user_data['selected_accounts'])[0]
    limit = context.user_data.get('scraper_limit', 0)
    scraper_type = context.user_data.get('scraper_type', 'all')
    
    msg = await update.message.reply_text(
        _("extracting_members_from", owner_id, link=link, phone=phone)
    )
    
    client = await get_telethon_client(phone, owner_id)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise Exception(_("scraper_account_needs_login", owner_id))
        
        filter_entity = None
        if scraper_type == 'recent':
            filter_entity = ChannelParticipantsRecent()
        
        all_participants = []
        entity_name = link.split('/')[-1]
        log_activity(phone, _("start_member_extraction_log", owner_id), f"From: {entity_name}")
        
        i = 0
        async for user in client.iter_participants(link, limit=limit or None, filter=filter_entity):
            i += 1
            if not user.bot:
                all_participants.append({
                    'user_id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username
                })
            if i % 100 == 0:
                await msg.edit_text(_("extracting_progress", owner_id, count=len(all_participants)))
        
        if not all_participants:
            await msg.edit_text(_("no_members_found", owner_id))
            return ConversationHandler.END

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['user_id', 'first_name', 'last_name', 'username'])
        writer.writeheader()
        writer.writerows(all_participants)
        output.seek(0)
        
        file_bio = io.BytesIO(output.getvalue().encode('utf-8'))
        file_bio.name = f"members_{entity_name}_{scraper_type}.csv"
        
        await update.message.reply_document(
            document=file_bio,
            caption=_("extraction_success_caption", owner_id, count=len(all_participants))
        )
        log_activity(phone, _("success_member_extraction_log", owner_id), f"Extracted {len(all_participants)} from {entity_name}")
        await msg.delete()

    except Exception as e:
        log_activity(phone, _("failed_member_extraction_log", owner_id), f"Error: {e}")
        await msg.edit_text(_("extraction_failed", owner_id, error=e))
    finally:
        pass
        
    await cleanup_conversation(context)
    return ConversationHandler.END

async def bulk_get_bio_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    await query.message.edit_text(text=_("enter_bulk_bio", user_id))
    return BULK_GET_BIO

async def execute_bulk_bio_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_bio = update.message.text
    owner_id = update.effective_user.id
    
    selected_accounts = list(context.user_data.get('selected_accounts', []))
    action_title = _("bulk_bio_button", owner_id)

    msg = await update.message.reply_text(
        _("starting_bulk_task", owner_id, action_type=action_title, count=len(selected_accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )

    success_count, failure_count = 0, 0

    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", owner_id, current=i+1, total=len(selected_accounts), phone=phone), owner_id)
        try:
            client = await get_telethon_client(phone, owner_id)
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception(_("account_needs_login_alert", owner_id))
            
            await client(functions.account.UpdateProfileRequest(about=new_bio))
            log_activity(phone, "bulk_bio_change", _("success", owner_id))
            success_count += 1
        except Exception as e:
            failure_count += 1
            log_activity(phone, "bulk_bio_change", f"{_('failed', owner_id)}: {e}")
        finally:
            pass

    final_report_text = _("bulk_task_final_report", owner_id, 
                          action_title=action_title, 
                          success_count=success_count, 
                          failure_count=failure_count)
    
    keyboard = [[InlineKeyboardButton(_("back_to_bulk_menu", owner_id), callback_data="show_bulk_action_options")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(final_report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    await cleanup_conversation(context)
    return ConversationHandler.END

async def bulk_get_name_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    await query.message.edit_text(text=_("enter_bulk_name", user_id))
    return BULK_GET_NAME

async def execute_bulk_name_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_name_input = update.message.text
    owner_id = update.effective_user.id

    parts = [p.strip() for p in new_name_input.split('|')]
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''
    
    selected_accounts = list(context.user_data.get('selected_accounts', []))
    action_title = _("bulk_name_button", owner_id)

    msg = await update.message.reply_text(
        _("starting_bulk_task", owner_id, action_type=action_title, count=len(selected_accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )

    success_count, failure_count = 0, 0
    
    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", owner_id, current=i+1, total=len(selected_accounts), phone=phone), owner_id)
        try:
            client = await get_telethon_client(phone, owner_id)
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception(_("account_needs_login_alert", owner_id))
            
            await client(functions.account.UpdateProfileRequest(first_name=first_name, last_name=last_name))
            update_account_status(phone, owner_id, None, first_name=first_name, last_check_update=False)
            log_activity(phone, "bulk_name_change", _("success", owner_id))
            success_count += 1
        except Exception as e:
            failure_count += 1
            log_activity(phone, "bulk_name_change", f"{_('failed', owner_id)}: {e}")
        finally:
            pass

    final_report_text = _("bulk_task_final_report", owner_id, 
                          action_title=action_title, 
                          success_count=success_count, 
                          failure_count=failure_count)
    
    keyboard = [[InlineKeyboardButton(_("back_to_bulk_menu", owner_id), callback_data="show_bulk_action_options")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(final_report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    await cleanup_conversation(context)
    return ConversationHandler.END

async def bulk_get_photo_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    await query.message.edit_text(text=_("enter_bulk_photo", user_id))
    return BULK_GET_PHOTO

async def execute_bulk_photo_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    owner_id = update.effective_user.id
    photo = update.message.photo[-1]
    
    selected_accounts = list(context.user_data.get('selected_accounts', []))
    action_title = _("bulk_photo_button", owner_id)

    msg = await update.message.reply_text(
        _("starting_bulk_task", owner_id, action_type=action_title, count=len(selected_accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )

    bot_file = await context.bot.get_file(photo.file_id)
    file_bytes = await bot_file.download_as_bytearray()

    success_count, failure_count = 0, 0

    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", owner_id, current=i+1, total=len(selected_accounts), phone=phone), owner_id)
        try:
            client = await get_telethon_client(phone, owner_id)
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception(_("account_needs_login_alert", owner_id))
            
            await client(functions.photos.UploadProfilePhotoRequest(file=await client.upload_file(bytes(file_bytes))))
            log_activity(phone, "bulk_photo_change", _("success", owner_id))
            success_count += 1
        except Exception as e:
            failure_count += 1
            log_activity(phone, "bulk_photo_change", f"{_('failed', owner_id)}: {e}")
        finally:
            pass

    final_report_text = _("bulk_task_final_report", owner_id, 
                          action_title=action_title, 
                          success_count=success_count, 
                          failure_count=failure_count)
    
    keyboard = [[InlineKeyboardButton(_("back_to_bulk_menu", owner_id), callback_data="show_bulk_action_options")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(final_report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    await cleanup_conversation(context)
    return ConversationHandler.END

async def bulk_select_proxy_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    proxies = get_all_proxies_from_db()
    if not proxies:
        await query.message.edit_text(
            _("no_proxies_added", user_id),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("back_to_bulk_menu", user_id), callback_data="show_bulk_action_options")]])
        )
        return ConversationHandler.END

    keyboard_buttons = []
    keyboard_buttons.append(InlineKeyboardButton(_("unassign_proxy_button", user_id), callback_data="bulk_assign_proxy:none"))
    
    for p in proxies:
        btn_text = f"🆔{p['id']}: ...{p['hostname'][-15:]}:{p['port']} ({p['usage_count']}👤)"
        keyboard_buttons.append(InlineKeyboardButton(btn_text, callback_data=f"bulk_assign_proxy:{p['id']}"))

    keyboard = [keyboard_buttons[i:i + 2] for i in range(0, len(keyboard_buttons), 2)]
    keyboard.append([InlineKeyboardButton(_("cancel_button", user_id), callback_data="cancel_bulk_selection")])

    await query.message.edit_text(
        text=_("select_proxy_for_bulk_assign", user_id),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BULK_SELECT_PROXY

async def execute_bulk_proxy_assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    owner_id = query.from_user.id
    await query.answer()

    proxy_id_str = query.data.split(':')[1]
    proxy_id = int(proxy_id_str) if proxy_id_str != 'none' else None
    
    selected_accounts = list(context.user_data.get('selected_accounts', []))
    action_title = _("bulk_proxy_assign_button", owner_id)

    msg = await query.message.edit_text(
        _("starting_bulk_task", owner_id, action_type=action_title, count=len(selected_accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )

    success_count, failure_count = 0, 0
    
    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", owner_id, current=i+1, total=len(selected_accounts), phone=phone), owner_id)
        try:
            assign_proxy_to_account(phone, owner_id, proxy_id)
            success_count += 1
        except Exception as e:
            failure_count += 1
        await asyncio.sleep(0.1)

    final_report_text = _("bulk_task_final_report", owner_id, 
                          action_title=action_title, 
                          success_count=success_count, 
                          failure_count=failure_count)
    
    keyboard = [[InlineKeyboardButton(_("back_to_bulk_menu", owner_id), callback_data="show_bulk_action_options")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(final_report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    await cleanup_conversation(context)
    return ConversationHandler.END

# ==============================================================================
# ||                   قسم إدارة جهات الاتصال الجماعي (مفعل)                   ||
# ==============================================================================

async def bulk_add_contacts_get_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    await query.message.edit_text(text=_("enter_contacts_to_add", user_id))
    return BULK_CONTACTS_GET_LIST

async def execute_bulk_add_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Adds a list of contacts to the selected accounts, resolving usernames."""
    contacts_input = update.message.text
    owner_id = update.effective_user.id
    
    contacts_to_add = [c.strip() for c in re.split(r'\s+|,|\n', contacts_input) if c.strip()]
    if not contacts_to_add:
        await update.message.reply_text("❌ لم يتم تقديم أي جهات اتصال صالحة.")
        # We need to return to the contact menu
        return await show_contact_management_menu(update, context)

    selected_accounts = list(context.user_data.get('selected_accounts', []))
    action_title = _("bulk_add_contacts_button", owner_id)

    msg = await update.message.reply_text(
        _("starting_bulk_task", owner_id, action_type=action_title, count=len(selected_accounts)),
    )
    
    success_count, failure_count = 0, 0
    report_lines = [f"**{_('bulk_task_report_header_no_link', owner_id, action_type=action_title)}**\n"]
    
    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", owner_id, current=i+1, total=len(selected_accounts), phone=phone), owner_id)
        account_success = 0
        account_fail = 0
        try:
            client = await get_telethon_client(phone, owner_id)
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception(_("account_needs_login_alert", owner_id))
            
            for contact_str in contacts_to_add:
                try:
                    if contact_str.startswith('+') and contact_str[1:].isdigit():
                        contact_obj = types.InputPhoneContact(client_id=0, phone=contact_str, first_name=contact_str, last_name='')
                        await client(functions.contacts.ImportContactsRequest(contacts=[contact_obj]))
                    else:
                        user_entity = await client.get_entity(contact_str)
                        await client(functions.contacts.AddContactRequest(
                            id=user_entity,
                            first_name=user_entity.first_name or contact_str.replace('@',''),
                            last_name=user_entity.last_name or '',
                            phone="",
                            add_phone_privacy_exception=False
                        ))
                    account_success += 1
                except Exception as inner_e:
                    logger.warning(f"Failed to add contact {contact_str} for {phone}: {inner_e}")
                    account_fail += 1
                await asyncio.sleep(0.5) # Delay between contacts
            
            report_lines.append(f"✅ `{phone}`: {_('task_success', owner_id)} (Added: {account_success}, Failed: {account_fail})")
            success_count += 1
        except Exception as e:
            escaped_error = markdown_v2(str(e))
            report_lines.append(f"❌ `{phone}`: {_('task_failure', owner_id, error=escaped_error)}")
            failure_count += 1
        await asyncio.sleep(1) # Delay between accounts

    final_report_text = _("bulk_task_final_report", owner_id, 
                          action_title=action_title, 
                          success_count=success_count, 
                          failure_count=failure_count)
    
    keyboard = [[InlineKeyboardButton(_("back_to_bulk_menu", owner_id), callback_data="show_contact_management_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(final_report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    await cleanup_conversation(context)
    return ConversationHandler.END


async def execute_export_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    owner_id = query.from_user.id
    await query.answer()

    action_title = _("export_contacts_button", owner_id)
    selected_accounts = list(context.user_data.get('selected_accounts', []))

    msg = await query.message.edit_text(_("starting_bulk_task", owner_id, action_type=action_title, count=len(selected_accounts)))

    full_export_text = ""
    success_count, failure_count = 0, 0

    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", owner_id, current=i+1, total=len(selected_accounts), phone=phone), owner_id)
        try:
            client = await get_telethon_client(phone, owner_id)
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception(_("account_needs_login_alert", owner_id))
            
            contacts = await client(functions.contacts.GetContactsRequest(hash=0))
            full_export_text += f"--- Contacts for {phone} ---\n"
            for user in contacts.users:
                username = f"@{user.username}" if user.username else "N/A"
                full_export_text += f"ID: {user.id}, Name: {user.first_name}, Username: {username}, Phone: {user.phone}\n"
            full_export_text += "\n"
            log_activity(phone, action_title, f"Exported {len(contacts.users)} contacts.")
            success_count += 1
        except Exception as e:
            full_export_text += f"--- Failed for {phone}: {e} ---\n\n"
            log_activity(phone, action_title, f"{_('failed', owner_id)}: {e}")
            failure_count += 1
        await asyncio.sleep(1)

    caption = _("bulk_task_final_report", owner_id, action_title=action_title, success_count=success_count, failure_count=failure_count)
    
    if full_export_text:
        output_file = io.BytesIO(full_export_text.encode('utf-8'))
        output_file.name = f"contacts_export_{owner_id}.txt"
        await context.bot.send_document(chat_id=owner_id, document=output_file, caption=caption)
        await msg.delete()
    else:
        await msg.edit_text(_("no_contacts_to_export", owner_id))

    await cleanup_conversation(context)
    return ConversationHandler.END

# ==============================================================================
# ||                   قسم نشر القصص الجماعي (مفعل)                       ||
# ==============================================================================

async def bulk_story_get_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    selected_accounts = context.user_data.get('selected_accounts')
    if not selected_accounts:
        await query.message.edit_text(_("no_accounts_selected_cancel", user_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]))
        return ConversationHandler.END
    
    await query.message.edit_text(text=_("story_send_file_prompt", user_id))
    return BULK_STORY_GET_FILE

async def bulk_story_get_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    photo, video = message.photo, message.video
    if not photo and not video:
        await message.reply_text(_("story_send_file_prompt", message.from_user.id))
        return BULK_STORY_GET_FILE

    context.user_data['bulk_story_file_id'] = photo[-1].file_id if photo else video.file_id
    context.user_data['bulk_story_file_type'] = 'photo' if photo else 'video'

    await message.reply_text(_("story_send_caption_prompt", message.from_user.id))
    return BULK_STORY_GET_CAPTION

async def bulk_story_ask_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    caption = update.message.text
    context.user_data['bulk_story_caption'] = "" if caption == '/skip' else caption

    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton(_("privacy_all", user_id), callback_data="bulk_story:set_privacy:all")],
        [InlineKeyboardButton(_("privacy_contacts", user_id), callback_data="bulk_story:set_privacy:contacts")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data='go_back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(_("story_ask_privacy", user_id), reply_markup=reply_markup)
    return BULK_STORY_ASK_PRIVACY

async def bulk_story_skip_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['bulk_story_caption'] = ""
    return await bulk_story_ask_privacy(update, context)

async def bulk_story_set_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    privacy_type = query.data.split(':')[2]
    context.user_data['bulk_story_privacy_type'] = privacy_type
    
    return await bulk_story_ask_period(update, context)

async def bulk_story_ask_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton(_("period_6h", user_id), callback_data="bulk_story:set_period:6")],
        [InlineKeyboardButton(_("period_12h", user_id), callback_data="bulk_story:set_period:12")],
        [InlineKeyboardButton(_("period_24h", user_id), callback_data="bulk_story:set_period:24")],
        [InlineKeyboardButton(_("period_48h", user_id), callback_data="bulk_story:set_period:48")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data='go_back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(_("story_ask_period", user_id), reply_markup=reply_markup)
    return BULK_STORY_ASK_PERIOD

async def bulk_story_set_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    hours_str = query.data.split(':')[2]
    period_seconds = int(hours_str) * 3600
    context.user_data['bulk_story_period_seconds'] = period_seconds

    selected_accounts_count = len(context.user_data.get('selected_accounts', []))

    keyboard = [
        [InlineKeyboardButton(_("yes_im_sure", user_id), callback_data="bulk_story_execute")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data='go_back')]
    ]
    
    await query.message.edit_text(
        _("confirm_bulk_cleaner", user_id, action_text=f"{_('bulk_post_story_button', user_id)} ({selected_accounts_count} {_('accounts_count', user_id)})"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    return BULK_STORY_CONFIRM


async def execute_bulk_story_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    selected_accounts = list(context.user_data.get('selected_accounts', []))
    action_title = _("bulk_post_story_button", user_id)

    msg = await query.message.edit_text(
        _("starting_bulk_task", user_id, action_type=action_title, count=len(selected_accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )

    file_id = context.user_data.get('bulk_story_file_id')
    file_type = context.user_data.get('bulk_story_file_type')
    caption = context.user_data.get('bulk_story_caption', '')
    privacy_type = context.user_data.get('bulk_story_privacy_type')
    period_seconds = context.user_data.get('bulk_story_period_seconds')

    success_count, failure_count = 0, 0
    
    bot_file = await context.bot.get_file(file_id)
    file_bytes = await bot_file.download_as_bytearray()
    
    final_media_bytes = file_bytes
    if file_type == 'photo':
        image = Image.open(io.BytesIO(file_bytes))
        output_buffer = io.BytesIO()
        image.convert("RGB").save(output_buffer, format="JPEG")
        final_media_bytes = output_buffer.getvalue()

    privacy_rules = []
    if privacy_type == 'all':
        privacy_rules.append(types.InputPrivacyValueAllowAll())
    elif privacy_type == 'contacts':
        privacy_rules.append(types.InputPrivacyValueAllowContacts())

    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", user_id, current=i+1, total=len(selected_accounts), phone=phone), user_id)
        
        try:
            client = await get_telethon_client(phone, user_id)
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception(_("account_needs_login_alert", user_id))
            
            uploaded_file = await client.upload_file(bytes(final_media_bytes), file_name='story.jpg' if file_type == 'photo' else 'story.mp4')

            await client(functions.stories.SendStoryRequest(
                peer='me',
                media=types.InputMediaUploadedPhoto(file=uploaded_file) if file_type == 'photo' else types.InputMediaUploadedDocument(file=uploaded_file, mime_type='video/mp4', attributes=[]),
                caption=caption,
                privacy_rules=privacy_rules,
                period=period_seconds
            ))
            log_activity(phone, action_title, _("success", user_id))
            success_count += 1
        except Exception as e:
            log_activity(phone, action_title, f"{_('failed', user_id)}: {e}")
            failure_count += 1
        finally:
            pass 

    final_report_text = _("bulk_task_final_report", user_id, 
                          action_title=action_title, 
                          success_count=success_count, 
                          failure_count=failure_count)
    
    keyboard = [[InlineKeyboardButton(_("back_to_bulk_menu", user_id), callback_data="show_bulk_action_options")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(final_report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

    # Clean up bulk story specific user_data
    for key in ['bulk_story_file_id', 'bulk_story_file_type', 'bulk_story_caption', 'bulk_story_privacy_type', 'bulk_story_period_seconds']:
        context.user_data.pop(key, None)

    await cleanup_conversation(context)
    return ConversationHandler.END


# ==============================================================================
# ||                   قسم تصدير الجلسات الجماعي                       ||
# ==============================================================================
async def bulk_export_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['bulk_action_type'] = 'bulk_export'
    context.user_data['selected_accounts'] = set()
    return await select_accounts_for_bulk_action(update, context)

async def bulk_export_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    selected_accounts = context.user_data.get('selected_accounts', set())
    if not selected_accounts:
        await query.message.edit_text(_("no_accounts_selected_cancel", user_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]))
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(_("yes_send_now_button", user_id, count=len(selected_accounts)), callback_data="bulk_export_execute")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data="go_back")]
    ]
    await query.message.edit_text(
        _("security_warning_export_sessions", user_id, count=len(selected_accounts)),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    return BULK_EXPORT_CONFIRM

async def bulk_export_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    owner_id = query.from_user.id
    selected_accounts = list(context.user_data['selected_accounts'])
    msg = await query.message.edit_text(
        _("exporting_sessions_start", owner_id, count=len(selected_accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )

    sessions_data = []
    success_count, failure_count = 0, 0

    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("exporting_sessions_in_progress", owner_id), owner_id)
        client = await get_telethon_client(phone, owner_id)
        try:
            await client.connect()
            if await client.is_user_authorized():
                session_string = StringSession.save(client.session)
                sessions_data.append(f"Phone: {phone}\nSession: {session_string}\n\n")
                log_activity(phone, _("bulk_export_session_log", owner_id), _("success", owner_id))
                success_count += 1
            else:
                sessions_data.append(f"Phone: {phone}\nSession: {_('failed_needs_login', owner_id)}\n\n")
                failure_count += 1
        except Exception as e:
            sessions_data.append(f"Phone: {phone}\nSession: {_('failed', owner_id, error=e)}\n\n")
            failure_count += 1
            log_activity(phone, _("bulk_export_session_log", owner_id), _("failed", owner_id, error=e))
        finally:
            pass
            await asyncio.sleep(1)

    summary = _("export_success_summary", owner_id, success_count=success_count, failure_count=failure_count)
    
    if sessions_data:
        full_text = "".join(sessions_data)
        output_file = io.BytesIO(full_text.encode('utf-8'))
        output_file.name = f"sessions_export_{owner_id}_{datetime.now().strftime('%Y%m%d')}.txt"
        await query.message.reply_document(document=output_file, caption=summary)
        await msg.delete()
    else:
        await msg.edit_text(_("no_sessions_exported", owner_id))

    await cleanup_conversation(context)
    return ConversationHandler.END

# ==============================================================================
# ||                        أقسام الحذف والتنظيف الجماعي                       ||
# ==============================================================================
async def bulk_delete_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    await push_state(context, bulk_delete_options, query.data)

    keyboard = [
        [InlineKeyboardButton(_("confirm_delete_full_logout", user_id), callback_data="select_bulk_delete_type:full")],
        [InlineKeyboardButton(_("confirm_delete_local_only", user_id), callback_data="select_bulk_delete_type:local")],
        [InlineKeyboardButton(_("back_to_main_menu", user_id), callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(
        _("choose_delete_method", user_id),
        reply_markup=reply_markup
    )
    return BULK_DELETE_OPTIONS

async def start_bulk_delete_with_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await push_state(context, start_bulk_delete_with_type, query.data)

    delete_type = query.data.split(':')[1]
    
    context.user_data['bulk_action_type'] = 'deleter'
    context.user_data['bulk_delete_type'] = delete_type
    context.user_data['selected_accounts'] = set()

    return await select_accounts_for_bulk_action(update, context)

async def cleaner_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['bulk_action_type'] = 'cleaner'
    context.user_data['selected_accounts'] = set()
    return await select_accounts_for_bulk_action(update, context)

async def cleaner_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    selected_count = len(context.user_data.get('selected_accounts', []))
    if selected_count == 0:
        await query.message.edit_text(_("no_accounts_selected_cancel", user_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("back_to_main_menu", user_id), callback_data='back_to_main')]]))
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(_("leave_all_channels", user_id), callback_data="cleaner_confirm:leave_channels")],
        [InlineKeyboardButton(_("leave_all_groups", user_id), callback_data="cleaner_confirm:leave_groups")],
        [InlineKeyboardButton(_("delete_bot_chats", user_id), callback_data="cleaner_confirm:delete_bots")],
        [InlineKeyboardButton(_("delete_private_no_contact_chats", user_id), callback_data="cleaner_confirm:delete_private_no_contact")],
        [InlineKeyboardButton(_("delete_deleted_contacts", user_id), callback_data="cleaner_confirm:delete_deleted_contacts")],
        [InlineKeyboardButton(_("full_clean", user_id), callback_data="cleaner_confirm:full_clean")],
        [InlineKeyboardButton(_("go_back_button", user_id), callback_data="show_bulk_action_options")]
    ]
    await query.message.edit_text(
        _("cleaning_accounts_bulk", user_id, count=selected_count),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CLEANER_OPTIONS

async def cleaner_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    clean_type = query.data.split(':')[1]
    context.user_data['cleaner_type'] = clean_type
    
    type_map = {
        'leave_channels': _('leave_all_channels', user_id),
        'leave_groups': _('leave_all_groups', user_id),
        'delete_bots': _('delete_bot_chats', user_id),
        'delete_private_no_contact': _('delete_private_no_contact_chats', user_id),
        'delete_deleted_contacts': _('delete_deleted_contacts', user_id),
        'full_clean': _('full_clean', user_id)
    }
    
    keyboard = [[
        InlineKeyboardButton(_("yes_clean_now", user_id), callback_data="cleaner_execute"),
        [InlineKeyboardButton(_("back_to_bulk_menu", user_id), callback_data="show_bulk_action_options")]
    ]]
    await query.message.edit_text(
        _("confirm_bulk_cleaner", user_id, action_text=type_map[clean_type]),
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN
    )
    return CLEANER_CONFIRM

async def cleaner_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    clean_type = context.user_data.get('cleaner_type')
    selected_accounts = list(context.user_data.get('selected_accounts', []))
    owner_id = query.from_user.id
    
    msg = await query.message.edit_text(
        _("starting_bulk_cleaner", user_id, clean_type=clean_type, count=len(selected_accounts)),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    
    report_lines = [f"{_('bulk_cleaner_report_header', user_id, clean_type=clean_type)}\n"]
    
    for i, phone in enumerate(selected_accounts):
        await msg.edit_text(
            _("working_on_account", user_id, current=i+1, total=len(selected_accounts), phone=phone),
            parse_mode=constants.ParseMode.MARKDOWN
        )
        
        client = await get_telethon_client(phone, owner_id)
        report = { "channels": 0, "groups": 0, "bots": 0, "private": 0, "deleted": 0, "errors": 0 }
        
        try:
            await client.connect()
            if not await client.is_user_authorized(): 
                raise Exception(_("account_needs_login_alert", user_id))

            if clean_type in ['delete_deleted_contacts', 'full_clean']:
                contacts_result = await client(functions.contacts.GetContactsRequest(hash=0))
                deleted_users_to_delete = [user for user in contacts_result.users if user.deleted]
                if deleted_users_to_delete:
                    await client(functions.contacts.DeleteContactsRequest(id=deleted_users_to_delete))
                    report['deleted'] = len(deleted_users_to_delete)
            
            if clean_type != 'delete_deleted_contacts':
                async for dialog in client.iter_dialogs():
                    try:
                        entity = dialog.entity
                        is_channel = isinstance(entity, Channel) and not entity.megagroup
                        is_group = (isinstance(entity, Channel) and entity.megagroup) or isinstance(entity, Chat)
                        is_bot = isinstance(entity, User) and entity.bot
                        is_private_user = isinstance(entity, User) and not entity.bot and not entity.is_self

                        action_taken = False
                        if clean_type in ['leave_channels', 'full_clean'] and is_channel:
                            await dialog.delete(); report['channels'] += 1; action_taken = True
                        elif clean_type in ['leave_groups', 'full_clean'] and is_group:
                            await dialog.delete(); report['groups'] += 1; action_taken = True
                        elif clean_type in ['delete_bots', 'full_clean'] and is_bot:
                            await client(functions.messages.DeleteHistoryRequest(peer=entity, max_id=0, just_clear=True, revoke=True)); report['bots'] += 1; action_taken = True
                        elif clean_type in ['delete_private_no_contact', 'full_clean'] and is_private_user and not getattr(entity, 'contact', False):
                            await client(functions.messages.DeleteHistoryRequest(peer=entity, max_id=0, just_clear=True, revoke=True)); report['private'] += 1; action_taken = True
                        
                        if action_taken:
                            await asyncio.sleep(0.5)

                    except Exception as e_inner:
                        logger.warning(f"Cleaner inner error for dialog {dialog.id} on {phone}: {e_inner}")
                        report['errors'] += 1
            
            details = ", ".join([f"{k}: {v}" for k, v in report.items() if v > 0])
            report_lines.append(f"✅ `{phone}`: {_('bulk_cleaner_success', user_id, details=details or _('no_change', user_id))}")
            log_activity(phone, f"{_('bulk_cleaner_log', owner_id)}: {clean_type}", json.dumps(report))

        except Exception as e:
            report_lines.append(f"❌ `{phone}`: {_('task_failure', user_id, error=e)}")
            log_activity(phone, f"{_('bulk_cleaner_log', owner_id)}: {clean_type}", f"{_('failed', owner_id)}: {e}")
        finally:
            pass

    final_report = '\n'.join(report_lines)
    await msg.edit_text(final_report, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("back_to_bulk_menu", user_id), callback_data="show_bulk_action_options")]]), parse_mode=constants.ParseMode.MARKDOWN)
    
    await cleanup_conversation(context)
    return ConversationHandler.END

# ==============================================================================
# ||                        قسم تصدير البيانات (CSV)                          ||
# ==============================================================================
async def export_accounts_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    owner_id = query.from_user.id
    await query.answer(_("export_csv_preparing", owner_id))
    
    accounts = get_accounts_by_owner(owner_id)
    if not accounts:
        await query.message.reply_text(_("no_accounts_to_export", owner_id))
        return

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['phone', 'user_id', 'first_name', 'username', 'status', 'last_check', 'proxy_id', 'add_method', 'creation_date'])
    
    for acc in accounts:
        writer.writerow([
            acc['phone'], acc['user_id'], acc['first_name'], acc['username'],
            acc['status'], acc['last_check'], acc['proxy_id'], acc['add_method'], acc['creation_date']
        ])
    
    output.seek(0)
    file_to_send = io.BytesIO(output.getvalue().encode('utf-8'))
    file_to_send.name = f"accounts_export_{owner_id}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    await query.message.reply_document(
        document=file_to_send,
        caption=_("export_csv_success", owner_id, count=len(accounts))
    )

# ==============================================================================
# ||                   قسم المهام المجدولة (Cron Jobs)                  ||
# ==============================================================================
async def scheduler_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    owner_id = query.from_user.id
    await query.answer()
    await push_state(context, scheduler_menu_start, 'scheduler_menu_start')
    
    tasks = get_scheduled_tasks(owner_id)
    text = _("scheduled_tasks_menu_title", owner_id)
    keyboard = [[InlineKeyboardButton(_("add_new_task_button", owner_id), callback_data="scheduler:add_start")]]

    if not tasks:
        text += _("no_scheduled_tasks", owner_id)
    else:
        task_types_map = {'join': _('task_join', owner_id), 'message': _('task_message', owner_id), 'check': _('task_check', owner_id)}
        for task in tasks:
            phones = json.loads(task['phones'])
            task_type_str = task_types_map.get(task['task_type'], task['task_type'])
            next_run_str = "N/A"
            if task['next_run_time']:
                next_run_str = datetime.fromisoformat(task['next_run_time']).strftime('%Y-%m-%d %H:%M')
            
            status_icon = _("task_resume_button", owner_id) if task['status'] == 'paused' else _("task_pause_button", owner_id)
            status_cb = "resume" if task['status'] == 'paused' else "pause"

            btn_text = f"⚙️ {task_type_str} | {len(phones)} {_('accounts_count', owner_id)} | {_('task_next_run', owner_id)} {next_run_str}"
            keyboard.append([
                InlineKeyboardButton(btn_text, callback_data=f"noop"),
                InlineKeyboardButton(status_icon, callback_data=f"scheduler:{status_cb}:{task['job_id']}"),
                InlineKeyboardButton(_("task_delete_button", owner_id), callback_data=f"scheduler:delete:{task['job_id']}")
            ])

    keyboard.append([InlineKeyboardButton(_("go_back_button", owner_id), callback_data="back_to_main")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SCHEDULER_MENU

async def scheduler_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(_("task_type_join", user_id), callback_data="scheduler:set_type:join")],
        [InlineKeyboardButton(_("task_type_message", user_id), callback_data="scheduler:set_type:message")],
        [InlineKeyboardButton(_("task_type_check", user_id), callback_data="scheduler:set_type:check")],
        [InlineKeyboardButton(_("go_back_button", user_id), callback_data="go_back")]
    ]
    await query.message.edit_text(_("choose_task_type", user_id), reply_markup=InlineKeyboardMarkup(keyboard))
    return SCHEDULER_SELECT_TYPE

async def scheduler_set_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    task_type = query.data.split(':')[1]
    context.user_data['scheduled_task_type'] = task_type
    
    if task_type == 'check':
        context.user_data['selected_accounts'] = {acc['phone'] for acc in get_accounts_by_owner(user_id)}
        cron_examples = _("cron_examples", user_id)
        await query.message.edit_text(_("enter_cron_schedule", user_id, cron_examples=cron_examples), parse_mode=constants.ParseMode.MARKDOWN)
        return SCHEDULER_GET_CRON
    else:
        context.user_data['selected_accounts'] = set() 
        context.user_data['bulk_action_type'] = 'scheduler' 
        await push_state(context, scheduler_set_type, query.data)
        return await select_accounts_for_bulk_action(update, context)

async def scheduler_get_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if not context.user_data.get('selected_accounts'):
        await query.message.edit_text(_("no_accounts_selected_cancel", user_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", user_id), callback_data='go_back')]]))
        return ConversationHandler.END

    task_type = context.user_data['scheduled_task_type']
    prompt_text = "3️⃣ "
    if task_type == 'join':
        prompt_text += _("enter_task_target", user_id)
    elif task_type == 'message':
        prompt_text += _("enter_message_target", user_id)
    
    await query.message.edit_text(prompt_text)
    return SCHEDULER_GET_TARGET

async def scheduler_get_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data['scheduled_target'] = update.message.text
    task_type = context.user_data['scheduled_task_type']
    
    if task_type == 'message':
        await update.message.reply_text(_("enter_message_content", user_id))
        return SCHEDULER_GET_CONTENT
    else: 
        cron_examples = _("cron_examples", user_id)
        await update.message.reply_text(_("enter_cron_schedule", user_id, cron_examples=cron_examples), parse_mode=constants.ParseMode.MARKDOWN)
        return SCHEDULER_GET_CRON

async def scheduler_get_cron(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.user_data.get('scheduled_task_type') == 'message':
        context.user_data['scheduled_content'] = update.message.text
    
    cron_examples = _("cron_examples", user_id)
    await update.message.reply_text(_("enter_cron_schedule", user_id, cron_examples=cron_examples), parse_mode=constants.ParseMode.MARKDOWN)
    return SCHEDULER_GET_CRON

async def scheduler_save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cron_str = update.message.text
    user_id = update.effective_user.id
    try:
        CronTrigger.from_crontab(cron_str)
    except Exception:
        await update.message.reply_text(_("invalid_cron_format", user_id))
        return SCHEDULER_GET_CRON

    owner_id = update.effective_user.id
    task_type = context.user_data['scheduled_task_type']
    phones = list(context.user_data['selected_accounts'])
    target = context.user_data.get('scheduled_target')
    content = context.user_data.get('scheduled_content')
    job_id = str(uuid.uuid4())

    try:
        job = scheduler.add_job(
            execute_scheduled_task,
            CronTrigger.from_crontab(cron_str, timezone="Asia/Damascus"),
            id=job_id,
            name=f"Task {job_id} for {owner_id}",
            args=[context.bot, job_id, owner_id, json.dumps(phones), task_type, target, content],
        )
        add_scheduled_task(job_id, owner_id, phones, task_type, cron_str, target, content, job.next_run_time)
        await update.message.reply_text(
            _("task_scheduled_success", user_id, next_run_time=job.next_run_time.strftime('%Y-%m-%d %H:%M'))
        )
    except Exception as e:
        await update.message.reply_text(_("task_scheduling_failed", user_id, error=e))

    await cleanup_conversation(context)
    await mock_update_and_call(scheduler_menu_start, update, context, "scheduler_menu_start", push=False)
    return ConversationHandler.END

async def scheduler_handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    _, action, job_id = query.data.split(':')
    owner_id = query.from_user.id

    job = scheduler.get_job(job_id)
    if not job:
        await query.answer(_("task_not_found", user_id), show_alert=True)
        remove_scheduled_task_from_db(job_id, owner_id)
    else:
        if action == 'delete':
            scheduler.remove_job(job_id)
            remove_scheduled_task_from_db(job_id, owner_id)
            await query.answer(_("task_deleted", user_id), show_alert=True)
        elif action == 'pause':
            scheduler.pause_job(job_id)
            update_task_status(job_id, 'paused')
            await query.answer(_("task_paused", user_id), show_alert=True)
        elif action == 'resume':
            scheduler.resume_job(job_id)
            update_task_status(job_id, 'active')
            update_task_next_run(job_id, job.next_run_time)
            await query.answer(_("task_resumed", user_id), show_alert=True)

    return await mock_update_and_call(scheduler_menu_start, query, context, "scheduler_menu_start", push=False)

# ==============================================================================
# ||                   قسم إدارة البوت (للأدمن فقط)                      ||
# ==============================================================================
async def bot_admin_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    await push_state(context, bot_admin_menu_start, 'bot_admin_menu')
    keyboard = [
        [InlineKeyboardButton(_("add_subscription_button", user_id), callback_data="admin:sub_add"),
         InlineKeyboardButton(_("remove_subscription_button", user_id), callback_data="admin:sub_rem")],
        [InlineKeyboardButton(_("view_subscribers_button", user_id), callback_data="admin:sub_list")],
        [InlineKeyboardButton(_("custom_broadcast_button", user_id), callback_data="admin:broadcast_start")],
        [InlineKeyboardButton(_("monitor_resources_button", user_id), callback_data="admin:monitor")],
        [InlineKeyboardButton(_("backup_db_button", user_id), callback_data="admin:backup"),
         InlineKeyboardButton(_("restore_db_button", user_id), callback_data="admin:restore_start")],
        [InlineKeyboardButton(_("back_to_main_menu", user_id), callback_data="back_to_main")]
    ]
    await query.message.edit_text(_("admin_panel_title", user_id), reply_markup=InlineKeyboardMarkup(keyboard))
    return BOT_ADMIN_MENU

async def sub_list_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    subs = get_all_subscribers()
    if not subs:
        await query.message.edit_text(_("no_subscribers", user_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", user_id), callback_data="go_back")]]))
        return BOT_ADMIN_MENU

    keyboard = []
    text = _("subscribers_list_title", user_id)
    for sub in subs:
        sub_user_id = sub['user_id']
        end_date = datetime.fromisoformat(sub['end_date'])
        status = "✅" if end_date > datetime.now() else "❌"
        
        user_info_text = f"{status} ID: {sub_user_id}"
        try:
            chat = await context.bot.get_chat(sub_user_id)
            user_info_text = f"{status} {chat.full_name or chat.first_name}"
        except Exception:
            pass

        keyboard.append([InlineKeyboardButton(user_info_text, callback_data=f"admin:sub_info:{sub_user_id}")])

    keyboard.append([InlineKeyboardButton(_("go_back_button", user_id), callback_data="bot_admin_menu")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return BOT_ADMIN_MENU

async def sub_info_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    sub_user_id = int(query.data.split(':')[-1])

    sub = get_subscriber(sub_user_id)
    if not sub:
        await query.answer(_("subscriber_not_found", user_id), show_alert=True)
        return

    accounts = get_accounts_by_owner(sub_user_id)
    last_added_raw = get_last_added_account_date(sub_user_id)
    last_added_str = _('not_available', user_id)
    if last_added_raw:
        try:
            last_added_dt = None
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %I:%M:%S %p'):
                try:
                    last_added_dt = datetime.strptime(last_added_raw, fmt)
                    break
                except ValueError:
                    pass
            if last_added_dt:
                 last_added_str = last_added_dt.strftime('%Y-%m-%d')
            else:
                 last_added_str = last_added_raw
        except Exception:
             last_added_str = last_added_raw

    name = f"ID: {sub_user_id}"
    try:
        chat = await context.bot.get_chat(sub_user_id)
        name = chat.full_name or chat.first_name
    except Exception:
        pass
    
    start_date = datetime.fromisoformat(sub['start_date']).strftime('%Y-%m-%d')
    end_date = datetime.fromisoformat(sub['end_date']).strftime('%Y-%m-%d')
    
    text = (_("subscriber_info_card_title", user_id) + "\n"
            + _("subscriber_name", user_id, name=name) + "\n"
            + _("subscriber_id", user_id, id=sub_user_id) + "\n\n"
            + _("subscription_period", user_id, start_date=start_date, end_date=end_date) + "\n"
            + _("current_accounts_count", user_id, count=len(accounts)) + "\n"
            + _("last_account_add", user_id, date=last_added_str))
            
    keyboard = [[InlineKeyboardButton(_("back_to_subscribers_list", user_id), callback_data="admin:sub_list")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)
    return BOT_ADMIN_MENU

async def admin_monitor_resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    text = _("monitoring_title", user_id)
    
    try:
        if not psutil:
            text += "\n" + _("psutil_not_installed", user_id)
        else:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            physical_cores = psutil.cpu_count(logical=False)
            logical_cores = psutil.cpu_count(logical=True)
            cpu_cores_text = _("cpu_cores", user_id, physical=physical_cores, logical=logical_cores)
            
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            con, cur = db_connect()
            cur.execute("SELECT COUNT(*) FROM accounts")
            total_accounts_row = cur.fetchone()
            total_accounts = total_accounts_row[0] if total_accounts_row else 0
            con.close()
            active_clients = len(CLIENT_POOL)

            boot_time_timestamp = psutil.boot_time()
            boot_dt = datetime.fromtimestamp(boot_time_timestamp)
            now_dt = datetime.now()
            uptime_delta = now_dt - boot_dt
            
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = _("uptime_format", user_id, days=days, hours=hours, minutes=minutes, seconds=seconds)

            text += (
                f"\n\n**{_('cpu_details', user_id)}:** `{cpu_cores_text}`"
                f"\n{_('cpu_usage', user_id, percent=cpu_usage)}"
                f"\n{_('ram_usage', user_id, percent=ram.percent, used=format_bytes(ram.used), total=format_bytes(ram.total))}"
                f"\n{_('disk_usage', user_id, percent=disk.percent, used=format_bytes(disk.used), total=format_bytes(disk.total))}\n"
                f"\n---"
                f"\n**{_('admin_stats_header', user_id)}**"
                f"\n- {_('total_accounts', user_id)}: `{total_accounts}`"
                f"\n- {_('active_clients_in_pool', user_id)}: `{active_clients}`"
                f"\n- {_('active_scheduled_tasks', user_id, count=len(scheduler.get_jobs()))}\n"
                f"\n---"
                f"\n**{_('system_uptime', user_id)}:**\n`{uptime_str}`"
            )
    
    except PermissionError:
        text += ("\n\n" + 
                "❌ **خطأ صلاحيات:**\n" +
                "لا يمكن الوصول لمعلومات النظام في هذه البيئة (مثل Pydroid).\n" +
                "هذه الميزة تعمل فقط على أنظمة Windows أو سيرفرات Linux.")
    except Exception as e:
        text += f"\n\n❌ **خطأ غير متوقع:**\n{e}"

    keyboard = [
        [InlineKeyboardButton(_("refresh_button", user_id), callback_data="admin:monitor")],
        [InlineKeyboardButton(_("restart_bot_button", user_id), callback_data="admin:restart_confirm")],
        [InlineKeyboardButton(_("cancel_all_tasks_button", user_id), callback_data="admin:cancel_tasks_confirm")],
        [InlineKeyboardButton(_("go_back_button", user_id), callback_data="bot_admin_menu")]
    ]
    
    # --- بداية التعديل ---
    try:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # نتجاهل هذا الخطأ لأنه يعني أن المستخدم يضغط تحديث بدون وجود تغيير
            pass
        else:
            # إذا كان خطأ مختلف، نظهره
            logger.error(f"Error updating monitor screen: {e}")
            await query.answer(f"Error: {e}", show_alert=True)
    # --- نهاية التعديل ---

    return BOT_ADMIN_MENU


async def admin_restart_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for confirmation before restarting the bot."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(_("yes_button", user_id), callback_data="admin:restart_execute")],
        [InlineKeyboardButton(_("no_button", user_id), callback_data="admin:monitor")]
    ]
    await query.message.edit_text(
        text=_("confirm_restart_prompt", user_id),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADMIN_RESTART_CONFIRM

async def admin_restart_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restarts the bot."""
    query = update.callback_query
    await query.message.edit_text(_("bot_restarting_message", query.from_user.id))
    # Restart the bot
    os.execv(sys.executable, ['python'] + sys.argv)

async def admin_cancel_tasks_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for confirmation before cancelling all scheduled tasks."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(_("yes_button", user_id), callback_data="admin:cancel_tasks_execute")],
        [InlineKeyboardButton(_("no_button", user_id), callback_data="admin:monitor")]
    ]
    await query.message.edit_text(
        text=_("confirm_cancel_all_tasks_prompt", user_id),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADMIN_CANCEL_TASKS_CONFIRM

async def admin_cancel_tasks_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels all scheduled jobs."""
    query = update.callback_query
    user_id = query.from_user.id
    scheduler.remove_all_jobs()
    await query.answer(_("all_tasks_cancelled_message", user_id), show_alert=True)
    # Refresh the monitor screen
    return await admin_monitor_resources(update, context)



async def admin_backup_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer(_("backup_preparing", user_id))
    
    backup_filename = f"backup_{DB_NAME}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        shutil.copy(DB_NAME, backup_path)
        with open(backup_path, 'rb') as backup_file:
            await query.message.reply_document(
                document=backup_file,
                filename=backup_filename,
                caption=_("backup_success", user_id)
            )
    except Exception as e:
        await query.message.reply_text(_("backup_failed", user_id, error=e))
    return BOT_ADMIN_MENU
    
async def admin_restore_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    keyboard = [[InlineKeyboardButton(_("cancel_button", user_id), callback_data="go_back")]]
    await query.message.edit_text(_("restore_warning", user_id), reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_RESTORE_CONFIRM

async def admin_restore_receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    user_id = update.effective_user.id
    if not doc or not doc.file_name.endswith('.db'):
        await update.message.reply_text(_("invalid_db_file", user_id))
        return ADMIN_RESTORE_CONFIRM

    msg = await update.message.reply_text(_("restore_in_progress", user_id))
    
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown for DB restore.")
    
    await asyncio.sleep(2)

    new_db_file = await context.bot.get_file(doc.file_id)
    await new_db_file.download_to_drive(DB_NAME)

    await msg.edit_text(_("restore_success_restart", user_id))
    
    return ConversationHandler.END


async def sub_activate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    keyboard = [[InlineKeyboardButton(_("go_back_button", user_id), callback_data="bot_admin_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(
        _("enter_user_id_for_sub", user_id),
        reply_markup=reply_markup
    )
    return SUB_GET_ID

async def sub_activate_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        target_user_id = int(update.message.text)
        context.user_data['sub_user_id'] = target_user_id
        await update.message.reply_text(_("enter_sub_days", user_id))
        return SUB_GET_DAYS
    except ValueError:
        await update.message.reply_text(_("invalid_id_input", user_id))
        return SUB_GET_ID

async def sub_activate_get_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        days = int(update.message.text)
        target_user_id = context.user_data['sub_user_id']

        start_date, end_date = add_subscriber(target_user_id, days)
        
        # الخطوة 1: إرسال رسالة التأكيد
        await update.message.reply_text(
            _("sub_activation_success", user_id, target_user_id=target_user_id, days=days, end_date=end_date.strftime('%Y-%m-%d')),
            parse_mode=constants.ParseMode.MARKDOWN
        )

        # الخطوة 2: إرسال إشعار للمستخدم
        notification_text = _("sub_activation_notification_to_user", target_user_id, days=days, end_date=end_date.strftime('%Y-%m-%d %H:%M'))
        try:
            await context.bot.send_message(chat_id=target_user_id, text=notification_text, parse_mode=constants.ParseMode.MARKDOWN)
        except TelegramError as e:
            await update.message.reply_text(_("failed_to_notify_user", user_id, error=e))

        # <== تم الإصلاح: طريقة العودة إلى قائمة الأدمن
        # بدلاً من محاولة تعديل رسالة قديمة، نرسل قائمة جديدة كرسالة مستقلة.
        await cleanup_conversation(context)
        
        # نحصل على لوحة مفاتيح الأدمن
        admin_keyboard = [
            [InlineKeyboardButton(_("add_subscription_button", user_id), callback_data="admin:sub_add"),
             InlineKeyboardButton(_("remove_subscription_button", user_id), callback_data="admin:sub_rem")],
            [InlineKeyboardButton(_("view_subscribers_button", user_id), callback_data="admin:sub_list")],
            [InlineKeyboardButton(_("custom_broadcast_button", user_id), callback_data="admin:broadcast_start")],
            [InlineKeyboardButton(_("monitor_resources_button", user_id), callback_data="admin:monitor")],
            [InlineKeyboardButton(_("backup_db_button", user_id), callback_data="admin:backup"),
             InlineKeyboardButton(_("restore_db_button", user_id), callback_data="admin:restore_start")],
            [InlineKeyboardButton(_("back_to_main_menu", user_id), callback_data="back_to_main")]
        ]
        
        # نرسل القائمة كرسالة جديدة
        await update.message.reply_text(
            _("admin_panel_title", user_id),
            reply_markup=InlineKeyboardMarkup(admin_keyboard)
        )
        
        return BOT_ADMIN_MENU # العودة إلى حالة قائمة الأدمن

    except ValueError:
        await update.message.reply_text(_("invalid_days_input", user_id))
        return SUB_GET_DAYS
    # <== إضافة معالجة للخطأ في حال عدم وجود sub_user_id
    except KeyError:
        await update.message.reply_text("حدث خطأ، يرجى البدء من جديد.")
        return await cancel_action(update, context)

async def sub_deactivate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    subs = get_all_subscribers()
    if not subs:
        await query.message.edit_text(_("no_subscribers", user_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", user_id), callback_data="go_back")]]))
        return BOT_ADMIN_MENU

    keyboard = []
    for sub in subs:
        end_date_str = datetime.fromisoformat(sub['end_date']).strftime('%Y-%m-%d')
        keyboard.append([InlineKeyboardButton(f"👤 {sub['user_id']} ({_('expires', user_id)}: {end_date_str})", callback_data=f"admin:sub_rem_confirm:{sub['user_id']}")])

    keyboard.append([InlineKeyboardButton(_("go_back_button", user_id), callback_data="bot_admin_menu")])
    await query.message.edit_text(_("choose_user_to_deactivate_sub", user_id), reply_markup=InlineKeyboardMarkup(keyboard))
    return BOT_ADMIN_MENU

async def sub_deactivate_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_user_id = query.from_user.id
    await query.answer()
    target_user_id = int(query.data.split(':')[-1])

    if remove_subscriber(target_user_id):
        # 1. نحصل على نص الرسالة المترجمة أولاً
        raw_success_message = _("sub_deactivation_success", admin_user_id)
        
        # 2. الآن نقوم بتعبئة النص بالمعلومات الصحيحة
        final_success_message = raw_success_message.format(user_id=target_user_id)
        
        await query.message.edit_text(
            final_success_message, 
            parse_mode=constants.ParseMode.MARKDOWN
        )
        
        try:
            notification_message = _("sub_deactivation_notification_to_user", target_user_id)
            await context.bot.send_message(chat_id=target_user_id, text=notification_message)
        except TelegramError:
            pass
    else:
        await query.message.edit_text(_("sub_not_found_to_deactivate", admin_user_id))

    await asyncio.sleep(2)
    return await mock_update_and_call(bot_admin_menu_start, update, context, "bot_admin_menu", push=False)


# --- قسم البث المخصص ---
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(_("broadcast_to_all", user_id), callback_data="broadcast_target:all")],
        [InlineKeyboardButton(_("broadcast_by_sub_date", user_id), callback_data="broadcast_target:by_date")],
        [InlineKeyboardButton(_("broadcast_by_accounts_count", user_id), callback_data="broadcast_target:by_accounts")],
        [InlineKeyboardButton(_("broadcast_to_specific_ids", user_id), callback_data="broadcast_target:by_ids")],
        [InlineKeyboardButton(_("go_back_button", user_id), callback_data="bot_admin_menu")]
    ]
    await query.message.edit_text(_("broadcast_menu_title", user_id), reply_markup=InlineKeyboardMarkup(keyboard))
    return BROADCAST_GET_TARGET_TYPE

async def broadcast_get_target_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    target_type = query.data.split(':')[1]
    context.user_data['broadcast_target_type'] = target_type
    
    # <== بداية التعديل: إنشاء زر الرجوع
    keyboard = [[InlineKeyboardButton(_("cancel_button", user_id), callback_data="admin:broadcast_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    prompt_text = ""
    if target_type == 'by_date':
        prompt_text = _("enter_date_range", user_id)
    elif target_type == 'by_accounts':
        prompt_text = _("enter_account_count_range", user_id)
    elif target_type == 'by_ids':
        prompt_text = _("enter_user_ids", user_id)
    
    # إضافة الزر إلى الرسالة
    await query.message.edit_text(prompt_text, reply_markup=reply_markup)
    # <== نهاية التعديل
    
    return BROADCAST_GET_TARGET_PARAMS


async def broadcast_get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    message = update.message
    user_id = update.effective_user.id

    target_type = context.user_data.get('broadcast_target_type')
    user_ids = []

    if query and query.data == 'broadcast_target:all':
        await query.answer()
        user_ids = [s['user_id'] for s in get_all_subscribers(only_active=True)]
        context.user_data['broadcast_target_type'] = 'all'

    elif message:
        text = message.text
        if target_type == 'by_date':
            try:
                start_str, end_str = [p.strip() for p in text.split('|')]
                user_ids = get_subs_by_date_range(start_str, end_str)
            except Exception:
                await message.reply_text(_("invalid_date_format", user_id))
                return BROADCAST_GET_TARGET_PARAMS
        elif target_type == 'by_accounts':
            try:
                min_str, max_str = [p.strip() for p in text.split('|')]
                user_ids = get_subs_by_account_count(int(min_str), int(max_str))
            except Exception:
                await message.reply_text(_("invalid_number_range_format", user_id))
                return BROADCAST_GET_TARGET_PARAMS
        elif target_type == 'by_ids':
            user_ids = [int(id_str) for id_str in re.split(r'\s+|,', text) if id_str.isdigit()]

# الآن، بدلاً من طلب رسالة، سنطلب إعادة توجيه
    reply_target = message or (query.message if query else None)
    if not reply_target: return ConversationHandler.END

    if not user_ids:
        await reply_target.reply_text(_("no_users_match_criteria", user_id))
        return BROADCAST_GET_TARGET_PARAMS

    context.user_data['broadcast_user_ids'] = user_ids
    
    # <== تعديل: تغيير الرسالة لتطلب إعادة التوجيه
    keyboard = [[InlineKeyboardButton(_("cancel_button", user_id), callback_data="admin:broadcast_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=user_id,
        text=_("users_selected_prompt_message", user_id, count=len(user_ids)),
        reply_markup=reply_markup
    )
    if query: await query.message.delete()
    
    # ننتقل إلى حالة جديدة تنتظر أي نوع من الرسائل
    return BROADCAST_GET_MESSAGE 


async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves the forwarded message and asks for final confirmation."""
    user_id = update.effective_user.id
    
    # تخزين معلومات الرسالة المعاد توجيهها
    context.user_data['broadcast_from_chat_id'] = update.message.chat_id
    context.user_data['broadcast_message_id'] = update.message.message_id
    
    user_ids = context.user_data.get('broadcast_user_ids', [])
    
    keyboard = [
        [InlineKeyboardButton(_("yes_send_now_button", user_id, count=len(user_ids)), callback_data="admin:broadcast_send")],
        [InlineKeyboardButton(_("cancel_button", user_id), callback_data="admin:broadcast_start")]
    ]
    
    # لم نعد بحاجة لمعاينة النص
    await update.message.reply_text(
        _("confirm_broadcast", user_id, count=len(user_ids)),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN
    )
    return BROADCAST_CONFIRM


async def broadcast_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwards the stored message to all targeted users."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # جلب معلومات الرسالة من الذاكرة
    from_chat_id = context.user_data.get('broadcast_from_chat_id')
    message_id = context.user_data.get('broadcast_message_id')
    user_ids_to_send = context.user_data.get('broadcast_user_ids')

    if not from_chat_id or not message_id or not user_ids_to_send:
        await query.message.edit_text(_("broadcast_error_no_data", user_id))
        return await mock_update_and_call(broadcast_start, update, context, "admin:broadcast_start")

    msg = await query.message.edit_text(_("broadcast_sending", user_id))
    success_count, fail_count = 0, 0

    for i, user_id_to_send in enumerate(user_ids_to_send):
        await progress_updater(msg, len(user_ids_to_send), i + 1, _("broadcast_sending_progress", user_id), user_id)
        try:
            # <== تعديل: استخدام forward_message بدلاً من send_message
            await context.bot.forward_message(
                chat_id=user_id_to_send,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
            success_count += 1
            await asyncio.sleep(0.1) # تأخير بسيط بين الرسائل
        except Exception:
            fail_count += 1

    await msg.edit_text(
        _("broadcast_completed", user_id, success_count=success_count, fail_count=fail_count),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("back_to_bulk_menu", user_id), callback_data="admin:broadcast_start")]])
    )
    await cleanup_conversation(context)
    return ConversationHandler.END


async def admin_smart_notifications(bot: "Application.bot"):
    logger.info("Running daily smart notifications job...")
    
    con, cur = db_connect()
    three_days_from_now = (datetime.now() + timedelta(days=3)).isoformat()
    now = datetime.now().isoformat()
    cur.execute("SELECT * FROM subscribers WHERE end_date BETWEEN ? AND ?", (now, three_days_from_now))
    expiring_soon_subs = cur.fetchall()
    
    admin_message_parts = [_("daily_admin_alerts", 0)]
    if expiring_soon_subs:
        admin_message_parts.append(_("expiring_soon_subscriptions", 0))
        for sub in expiring_soon_subs:
            end_date = datetime.fromisoformat(sub['end_date']).strftime('%Y-%m-%d')
            admin_message_parts.append(f"- `ID: {sub['user_id']}` {_('expires_on', 0)} `{end_date}`")
        
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(chat_id=admin_id, text="\n".join(admin_message_parts), parse_mode=constants.ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(_("failed_to_send_admin_notification", 0, admin_id=admin_id, error=e))

    cur.execute("SELECT DISTINCT owner_id FROM accounts WHERE status = 'NEEDS_LOGIN'")
    users_with_needing_login_accounts = [row['owner_id'] for row in cur.fetchall()]
    con.close()

    for user_id_to_notify in users_with_needing_login_accounts:
        accounts_needing_login = get_accounts_by_owner(user_id_to_notify, only_inactive=True)
        if accounts_needing_login:
            user_mention = f"@{user_id_to_notify}"
            try:
                chat_info = await bot.get_chat(user_id_to_notify)
                user_mention = chat_info.mention_html()
            except Exception:
                pass
                
            notification_body = _("user_account_needs_login_notification_body", user_id_to_notify, user_mention=user_mention)
            for acc in accounts_needing_login:
                notification_body += _("account_needs_login_list_item", user_id_to_notify, phone=acc['phone']) + "\n"
            notification_body += _("relogin_instructions", user_id_to_notify)

            try:
                await bot.send_message(chat_id=user_id_to_notify, text=_("user_account_needs_login_notification_title", user_id_to_notify) + "\n\n" + notification_body, parse_mode=constants.ParseMode.HTML)
                logger.info(f"Sent needs_login notification to user {user_id_to_notify}")
            except Exception as e:
                logger.error(f"Failed to send needs_login notification to user {user_id_to_notify}: {e}")

# ==============================================================================
# ||                   [جديد] قسم إدارة إيميلات الاستيراد                      ||
# ==============================================================================

# ... (الكود الموجود لديك) ...
async def manage_import_emails_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    owner_id = query.from_user.id
    if query: await query.answer()

    await push_state(context, manage_import_emails_start, 'manage_emails_start')

    emails = get_import_emails_by_owner(owner_id)
    text = _("manage_emails_title", owner_id)
    keyboard = [[InlineKeyboardButton(_("add_email_button", owner_id), callback_data="emails:add_start")]]

    if not emails:
        text += f"\n\n{_('no_import_emails', owner_id)}"
    else:
        for email_row in emails:
            keyboard.append([
                InlineKeyboardButton(email_row['email_address'], callback_data=f"noop"),
                InlineKeyboardButton(_("check_status_button", owner_id), callback_data=f"emails:check:{email_row['id']}"),
                InlineKeyboardButton(_("delete_button", owner_id), callback_data=f"emails:delete:{email_row['id']}")
            ])
        keyboard.append([InlineKeyboardButton(_("fetch_email_button", owner_id), callback_data="emails:fetch_start")])

    keyboard.append([InlineKeyboardButton(_("back_to_main_menu", owner_id), callback_data="back_to_main")])

    # --- هذا هو السطر الذي تم إصلاحه ---
    # تم تغيير .reply_text إلى .edit_text لتعديل الرسالة الحالية
    await query.message.edit_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode=constants.ParseMode.MARKDOWN
    )
    # --- نهاية الإصلاح ---

    return MANAGE_EMAILS_MENU

# ... (بقية الكود الموجود لديك) ...


# ... (الكود الموجود لديك) ...
async def handle_email_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    owner_id = query.from_user.id
    action, *params = query.data.split(':')[1:]
    
    if action == "add_start":
        await query.answer()
        await query.message.edit_text(_("enter_gmail_address", owner_id))
        return EMAILS_GET_ADDRESS

    elif action == "delete":
        email_id = int(params[0])
        if remove_import_email(email_id, owner_id):
            await query.answer(_("email_deleted_success", owner_id), show_alert=True)
        return await mock_update_and_call(manage_import_emails_start, update, context, 'manage_emails_start', push=False)

    elif action == "check":
        # لا تجب على الكويري هنا، بل بعد الحصول على النص النهائي
        # await query.answer(_("email_status_checking", owner_id), show_alert=False) # <== حذف هذا السطر أو جعله تعليق

        email_id = int(params[0])
        
        # رسالة مؤقتة تشير إلى أن الفحص جارٍ
        temp_msg = await query.message.edit_text(_("email_status_checking", owner_id))

        target_email = get_import_email_by_id(email_id, owner_id) 

        report_text = _("email_check_report_title", owner_id) + "\n\n"
        report_text += f"📧 **الإيميل:** `{target_email['email_address'] if target_email else 'غير موجود'}`\n"
        
        email_address = target_email['email_address'] if target_email else None
        
        status_message = ""
        is_email_working = False

        if not target_email:
            status_message = _("email_not_found", owner_id)
        else:
            encrypted_pass = target_email['app_password_encrypted']
            app_pass = decrypt_email_password_base64(encrypted_pass)
            
            if app_pass == "DECRYPTION_FAILED":
                status_message = _("decryption_failed", owner_id)
                logger.warning(f"Decryption failed for email {email_address} (owner: {owner_id}) during check.")
            else:
                try:
                    is_email_working = await check_email_credentials(email_address, app_pass)
                    status_message = _("email_status_ok", owner_id) if is_email_working else _("email_status_fail", owner_id)
                    if not is_email_working:
                        logger.info(f"Email check failed for {email_address} (owner: {owner_id}). Credentials likely invalid.")
                except Exception as e:
                    status_message = _("email_fetch_failed", owner_id, error=str(e)) 
                    logger.error(f"Unexpected error during email credential check for {email_address}: {e}")
        
        report_text += f"🔬 **{_('email_check_status_label', owner_id)}** `{status_message}`\n\n"

        # جلب الحسابات التي تستخدم هذا الإيميل كبريد استرداد
        if target_email and is_email_working: # نتحقق فقط إذا كان الإيميل موجوداً ويعمل بشكل صحيح
            linked_accounts = get_accounts_by_2fa_recovery_email(email_address, owner_id)
            report_text += f"🔗 **{_('email_check_used_by_label', owner_id)}** ({len(linked_accounts)} حساب):\n"
            if linked_accounts:
                for acc in linked_accounts:
                    account_name = acc['first_name'] or acc['username'] or _('unknown_name', owner_id)
                    report_text += _("email_check_account_list_item", owner_id, phone=acc['phone'], name=account_name) + "\n"
            else:
                report_text += _("email_check_no_accounts_found", owner_id) + "\n"
        elif target_email: # إذا كان موجوداً ولكنه لا يعمل
            report_text += f"🔗 **{_('email_check_used_by_label', owner_id)}** لا يمكن التحقق (الإيميل لا يعمل).\n"
        else: # إذا لم يتم العثور على الإيميل من الأساس
            report_text += f"🔗 **{_('email_check_used_by_label', owner_id)}** غير قابل للتطبيق (الإيميل غير موجود).\n"

        # إنشاء لوحة المفاتيح
        keyboard = [[InlineKeyboardButton(_("back_to_email_management_button", owner_id), callback_data="manage_emails_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # حذف الرسالة المؤقتة وإرسال الرسالة النهائية
        await temp_msg.delete()
        await query.message.reply_text(report_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)

        return MANAGE_EMAILS_MENU # البقاء في نفس حالة المحادثة
    

    elif action == "fetch_start":
        await query.answer()
        emails = get_import_emails_by_owner(owner_id)
        if not emails:
            await query.message.edit_text(_("no_emails_added", owner_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("back_to_main_menu", owner_id), callback_data="back_to_main")]]))
            return ConversationHandler.END

        keyboard_buttons = []
        for email_row in emails:
            keyboard_buttons.append(
                InlineKeyboardButton(email_row['email_address'], callback_data=f"fetch_email_exec:{email_row['id']}")
            )
        
        keyboard_markup = [keyboard_buttons[i:i + 2] for i in range(0, len(keyboard_buttons), 2)]
        keyboard_markup.append([InlineKeyboardButton(_("cancel_button", owner_id), callback_data='cancel_fetch_email')])

        await query.message.edit_text(_("select_email_to_fetch", owner_id), reply_markup=InlineKeyboardMarkup(keyboard_markup))
        return FETCH_EMAIL_SELECT 
# ... (بقية الكود الموجود لديك) ...


async def emails_get_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email_address = update.message.text
    if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email_address, re.IGNORECASE):
        await update.message.reply_text(_("invalid_email_format", update.effective_user.id))
        return EMAILS_GET_ADDRESS

    context.user_data['new_email_address'] = email_address
    await update.message.reply_text(_("enter_app_password", update.effective_user.id))
    return EMAILS_GET_APP_PASS

async def emails_get_app_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app_password = update.message.text
    email_address = context.user_data.get('new_email_address')
    owner_id = update.effective_user.id

    if not email_address:
        # Failsafe in case context is lost
        return await mock_update_and_call(manage_import_emails_start, update, context, 'manage_emails_start', push=False)

    msg = await update.message.reply_text(_("email_status_checking", owner_id))

    # Check credentials *before* adding to the database
    are_credentials_valid = await check_email_credentials(email_address, app_password)

    if are_credentials_valid:
        # If valid, clear context and add to DB
        context.user_data.pop('new_email_address', None)
        
        if add_import_email(owner_id, email_address, app_password):
            await msg.edit_text(_("email_added_success", owner_id))
        else:
            await msg.edit_text(_("email_already_exists", owner_id))
        
        # On success, go back to the main email menu
        await asyncio.sleep(2)
        return await mock_update_and_call(manage_import_emails_start, update, context, 'manage_emails_start', push=False)
        
    else:
        # If invalid, inform the user and ask for the password again
        await msg.edit_text(_("email_add_failed_credentials", owner_id))
        await asyncio.sleep(1)
        await update.message.reply_text(_("enter_app_password", owner_id))
        # Stay in the same state to re-collect the password
        return EMAILS_GET_APP_PASS

# ... (الكود الموجود لديك) ...


# --- دوال معالجة جلب الإيميل ---
# ... (الكود الموجود لديك) ...
# ... (الكود الموجود لديك) ...
async def fetch_email_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يجلب ويعرض آخر رسالة من الإيميل المحدد مع زر للرجوع."""
    query = update.callback_query
    owner_id = query.from_user.id
    email_id = int(query.data.split(':')[1])

    email_data = get_import_email_by_id(email_id, owner_id)
    if not email_data:
        await query.message.edit_text(_("email_not_found", owner_id), reply_markup=await get_main_keyboard(owner_id))
        return MANAGE_EMAILS_MENU

    email_address = email_data['email_address']
    app_password = decrypt_email_password_base64(email_data['app_password_encrypted'])

    if app_password == "DECRYPTION_FAILED":
        await query.message.edit_text(_("decryption_failed", owner_id), reply_markup=await get_main_keyboard(owner_id))
        return MANAGE_EMAILS_MENU

    msg = await query.message.edit_text(_("fetching_email", owner_id, email_address=email_address))

    # --- بداية التعديل ---
    # 1. إنشاء زر الرجوع
    keyboard = [[
        InlineKeyboardButton(
            _("back_to_email_selection_button", owner_id), 
            callback_data="emails:fetch_start" # هذا الأمر يعيد عرض قائمة الإيميلات
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        latest_email = await fetch_latest_email(email_address, app_password)
        await msg.delete() 

        if latest_email:
            body_content = latest_email['body']
            if len(body_content) > 500:
                body_content = body_content[:500] + "..."
            
            # 2. إرسال الرسالة مع زر الرجوع
            await update.effective_chat.send_message(
                _("email_fetch_success", 
                  user_id=owner_id,
                  email_address=email_address,
                  from_=latest_email['from'],
                  subject=latest_email['subject'],
                  date=latest_email['date'],
                  body=body_content),
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await update.effective_chat.send_message(
                _("email_fetch_no_messages", owner_id),
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"خطأ في جلب الرسالة: {e}")
        await msg.delete() 
        await update.effective_chat.send_message(
            _("email_fetch_failed", owner_id, error=str(e)),
            reply_markup=reply_markup
        )
    
    # 3. العودة إلى قائمة الإيميلات بدلاً من إنهاء المحادثة
    return MANAGE_EMAILS_MENU
    # --- نهاية التعديل ---

# ... (بقية الكود الموجود لديك) ...


# ==============================================================================
# ||                   [جديد] قسم التعيين الجماعي لـ 2FA                         ||
# ==============================================================================

async def bulk_2fa_choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    owner_id = query.from_user.id
    await query.answer()

    if not get_import_emails_by_owner(owner_id):
        await query.message.edit_text(
            _("bulk_2fa_no_emails_error", owner_id),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("back_to_bulk_menu", owner_id), callback_data="show_bulk_action_options")]])
        )
        return ConversationHandler.END

    selected_count = len(context.user_data.get('selected_accounts', []))
    keyboard = [
        [InlineKeyboardButton(_("2fa_mode_unified_user", owner_id), callback_data="2fa_mode:unified_user")],
        [InlineKeyboardButton(_("2fa_mode_random_unique", owner_id), callback_data="2fa_mode:random_unique")],
        [InlineKeyboardButton(_("2fa_mode_random_unified", owner_id), callback_data="2fa_mode:random_unified")],
        [InlineKeyboardButton(_("cancel_button", owner_id), callback_data="cancel_bulk_selection")]
    ]
    await query.message.edit_text(
        _("bulk_2fa_menu_title", owner_id, count=selected_count),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BULK_2FA_CHOOSE_MODE

async def bulk_2fa_handle_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    mode = query.data.split(':')[1]
    context.user_data['bulk_2fa_mode'] = mode

    if mode == 'unified_user':
        await query.message.edit_text(_("enter_unified_2fa_pass", query.from_user.id))
        return BULK_2FA_GET_UNIFIED_PASS
    else:
        await query.message.delete()
        return await execute_bulk_2fa(update, context)

# ... (الكود الموجود لديك) ...
async def execute_bulk_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = update.effective_user.id
    mode = context.user_data.get('bulk_2fa_mode')
    
    original_message = update.message or (update.callback_query.message if update.callback_query else None)
        
    unified_pass = None
    if mode == 'unified_user':
        unified_pass = update.message.text

    selected_accounts = list(context.user_data.get('selected_accounts', []))
    import_emails = get_import_emails_by_owner(owner_id)
    
    msg = await original_message.reply_text(_("bulk_2fa_starting", owner_id, count=len(selected_accounts)))

    email_pool = []
    num_accounts = len(selected_accounts)
    num_emails = len(import_emails)
    if num_emails > 0:
        accounts_per_email = math.ceil(num_accounts / num_emails)
        for email_row in import_emails: # تم تغيير اسم المتغير لتجنب التعارض مع مكتبة email
            email_pool.extend([email_row] * int(accounts_per_email))
        random.shuffle(email_pool)
    else: # إذا لم يكن هناك إيميلات استيراد، لا يمكننا تعيين 2FA ببريد استرداد
        await msg.edit_text(_("bulk_2fa_no_emails_error", owner_id))
        return ConversationHandler.END


    passwords_map = {}
    if mode == 'unified_user':
        for phone in selected_accounts: passwords_map[phone] = unified_pass
    elif mode == 'random_unified':
        random_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        for phone in selected_accounts: passwords_map[phone] = random_pass
    elif mode == 'random_unique':
        for phone in selected_accounts:
            passwords_map[phone] = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# ... (الكود الموجود لديك قبل حلقة for) ...

    report_data = []
    for i, phone in enumerate(selected_accounts):
        await progress_updater(msg, len(selected_accounts), i + 1, _("working_on_account", owner_id, current=i+1, total=len(selected_accounts), phone=phone), owner_id)
        
        password = passwords_map.get(phone)
        recovery_email_row = email_pool[i] if i < len(email_pool) else None
        
        status = "Failed"
        details = "No password or recovery email available."

        if password and recovery_email_row:
            recovery_email = recovery_email_row['email_address']
            app_pass = decrypt_email_password_base64(recovery_email_row['app_password_encrypted'])
            
            # 🚨🚨🚨 هنا هو التعديل الرئيسي: تعديل تعريف email_code_callback 🚨🚨🚨
            # يجب أن تقبل الدالة وسيطاً (عادةً يسمى is_resend)، حتى لو لم نستخدمه
            async def get_bulk_2fa_email_code_callback(is_resend=False): # <== أضف is_resend=False
                # 🚨 إضافة تأخير للسماح لوصول الكود عبر البريد
                await asyncio.sleep(3) # يمكنك زيادة هذا الوقت إذا استمرت المشكلة
                
                if app_pass == "DECRYPTION_FAILED":
                    logger.error(f"فشل فك ترميز كلمة مرور التطبيق لـ {recovery_email} أثناء جلب كود 2FA.")
                    raise EmailUnconfirmedError("فشل فك ترميز كلمة مرور التطبيق.")
                
                logger.info(f"جاري محاولة جلب كود 2FA لـ {phone} من {recovery_email} تلقائياً...")
                
                code = await find_telegram_code_in_gmail(recovery_email, app_pass)
                
                if not code:
                    logger.warning(f"فشل جلب كود 2FA لـ {phone} من {recovery_email} تلقائياً.")
                    raise EmailUnconfirmedError("فشل جلب الكود تلقائياً.")
                
                logger.info(f"تم جلب كود 2FA لـ {phone} بنجاح.")
                return code

            client = await get_telethon_client(phone, owner_id)
            try:
                await client.connect()
                if not await client.is_user_authorized(): raise Exception(_("account_needs_login_alert", owner_id))
                
                await client.edit_2fa(
                    new_password=password,
                    hint=DEFAULT_2FA_HINT,
                    email=recovery_email,
                    email_code_callback=get_bulk_2fa_email_code_callback
                )
                
                status = _("2fa_set_success", owner_id)
                details = _("2fa_email_verify_auto_success", owner_id)
                save_2fa_password(owner_id, phone, password, DEFAULT_2FA_HINT, recovery_email)

            except EmailUnconfirmedError as e:
                status = _("2fa_set_fail", owner_id)
                details = f"{_('2fa_email_verify_auto_fail', owner_id)} ({e})"
            except Exception as e:
                status = _("2fa_set_fail", owner_id)
                details = str(e)
        else:
             status = _("2fa_set_fail", owner_id)
             details = "لا توجد كلمة مرور أو إيميل استرداد متاح."

        report_data.append({
            "phone": phone,
            "password": password or "N/A",
            "recovery_email": recovery_email_row['email_address'] if recovery_email_row else "N/A",
            "status": status,
            "details": details
        })
        await asyncio.sleep(2)

# ... (بقية الكود الموجود لديك بعد الحلقة) ...

    # بناء نص التقرير النهائي
    report_text = f"{_('bulk_2fa_report_title', owner_id)}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report_text += "------------------------------------\n\n"
    for item in report_data:
        report_text += (f"Phone: {item['phone']}\nPassword: {item['password']}\nRecovery Email: {item['recovery_email']}\nStatus: {item['status']} - {item['details']}\n------------------------------------\n")
    
    # إرسال التقرير كملف
    output_file = io.BytesIO(report_text.encode('utf-8'))
    output_file.name = f"bulk_2fa_report_{owner_id}.txt"
    await context.bot.send_document(chat_id=owner_id, document=output_file, caption=_("bulk_2fa_report_title", owner_id))
    
    # حذف رسالة التقدم
    await msg.delete()
    
    # العودة إلى قائمة المهام الجماعية
    keyboard = [[InlineKeyboardButton(_("back_to_bulk_menu", owner_id), callback_data="show_bulk_action_options")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await original_message.reply_text(
        _("bulk_task_final_report", owner_id, action_title=_("bulk_2fa_button", owner_id), 
          success_count=sum(1 for item in report_data if item['status'] == _("2fa_set_success", owner_id)), 
          failure_count=sum(1 for item in report_data if item['status'] == _("2fa_set_fail", owner_id))),
        reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN
    )

    await cleanup_conversation(context)
    return ConversationHandler.END

# ... (بقية الكود الموجود لديك) ...


async def post_init(application: Application):
    """تحميل المهام المجدولة والإشعارات الذكية بعد تهيئة البوت."""
    await load_and_run_background_tasks(application.bot)
    if not scheduler.running:
        try:
            scheduler.start()
            logger.info("Scheduler started successfully.")
        except Exception as e:
            logger.error(f"FATAL: Could not start scheduler: {e}")
# ==============================================================================
# ||                   [جديد] قسم إدارة 2FA المطور                         ||
# ==============================================================================

# ... (الكود الموجود لديك) ...
async def tfa_management_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    owner_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    # 🚨 تغيير: لا نرد على الكويري هنا بعد، سنرسل رسالة جديدة
    # await query.answer() 

    # 🚨🚨🚨 إضافة: جلب كائن Telethon client هنا وتخزينه في context.user_data 🚨🚨🚨
    client = await get_telethon_client(phone, owner_id)
    context.user_data['client'] = client 
    
    # رسالة مؤقتة لبدء العملية، سيتم حذفها أو تعديلها لاحقاً
    # سنرسل رسالة جديدة بدلاً من محاولة تعديل رسالة الكويري لضمان تجنب "Message can't be edited"
    initial_message = await update.effective_chat.send_message(_("tfa_checking_status", owner_id))
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await initial_message.edit_text(_("account_needs_login_alert", owner_id))
            return MANAGE_ACCOUNT # أو العودة للقائمة الرئيسية

        password_info = await client(functions.account.GetPasswordRequest())
        context.user_data['tfa_password_info'] = password_info

        saved_2fa_info = get_2fa_password_info(owner_id, phone)
        
        recovery_email_display = _('tfa_no_recovery_email', owner_id)
        # 🚨 التعديل هنا: التأكد من أن recovery_email_display يعرض القيمة إذا كانت موجودة
        if saved_2fa_info and saved_2fa_info['recovery_email'] is not None: # <== أضف 'is not None'
            recovery_email_display = f"`{saved_2fa_info['recovery_email']}`"
# ... (بقية الكود) ...


        status_text = _("tfa_status_header", owner_id, phone=phone) + "\n"
        if password_info.has_password:
            status_text += f"- **{_('manage_2fa_button', owner_id)}:** {_('tfa_is_enabled', owner_id)}\n"
            status_text += f"- **{_('tfa_recovery_email', owner_id)}:** {recovery_email_display}"
        else:
            status_text += f"- **{_('manage_2fa_button', owner_id)}:** {_('tfa_is_disabled', owner_id)}"

        keyboard = [
            [InlineKeyboardButton(_("tfa_view_status_button", owner_id), callback_data="tfa_menu:view_status")],
            [InlineKeyboardButton(_("tfa_change_password_button", owner_id), callback_data="tfa_menu:change_pass")],
            [InlineKeyboardButton(_("tfa_change_email_button", owner_id), callback_data="tfa_menu:change_email")],
            [InlineKeyboardButton(_("tfa_disable_button", owner_id), callback_data="tfa_menu:disable")],
            [InlineKeyboardButton(_("go_back_button", owner_id), callback_data="go_back")]
        ]
        
        # 🚨 تغيير: تعديل الرسالة التي أرسلناها بدلاً من رسالة الكويري
        await initial_message.edit_text(text=status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error in tfa_management_menu_start: {e}", exc_info=True)
        # 🚨 تغيير: تعديل الرسالة التي أرسلناها في حالة الخطأ
        await initial_message.edit_text(_("unexpected_error", owner_id, error=e))
        return MANAGE_ACCOUNT

    return TFA_MENU
# ... (بقية الكود الموجود لديك) ...


# ... (الكود الموجود لديك) ...
async def tfa_verify_password_for_email_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    يتحقق من كلمة المرور التي أدخلها المستخدم. إذا كانت صحيحة،
    فإنه يحفظها في الـ context وينتقل لعرض قائمة الإيميلات.
    """
    current_password_str = update.message.text
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    client: TelegramClient = context.user_data['client']
    
    msg = await update.message.reply_text("⏳ جارٍ التحقق من كلمة المرور...")

    try:
        # أسهل طريقة للتحقق من كلمة المرور هي محاولة تغييرها إلى نفسها
        await client.edit_2fa(current_password=current_password_str, new_password=current_password_str)
        
        await msg.delete() 
        
        context.user_data['tfa_current_password_str'] = current_password_str
        # 🚨 حفظ كلمة المرور المدخلة في قاعدة بيانات البوت لاستخدامها مستقبلاً
        save_2fa_password(owner_id, phone, current_password_str, DEFAULT_2FA_HINT, None) # لا نغير بريد الاسترداد بعد
        
        # 🚨🚨🚨 التعديل هنا: الانتقال إلى عرض قائمة الإيميلات بعد التحقق بنجاح 🚨🚨🚨
        return await tfa_select_recovery_email_from_list(update, context)

    except PasswordHashInvalidError:
        await msg.edit_text("❌ كلمة المرور غير صحيحة. تم إلغاء العملية.")
        await asyncio.sleep(2)
        return await mock_update_and_call(tfa_management_menu_start, update, context, 'mng:manage_2fa', push=False)
        
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ غير متوقع: {e}")
        await asyncio.sleep(2)
        return await mock_update_and_call(tfa_management_menu_start, update, context, 'mng:manage_2fa', push=False)
# ... (بقية الكود الموجود لديك) ...


# ... (الكود الموجود لديك) ...
async def tfa_select_recovery_email_from_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يعرض قائمة الإيميلات المحفوظة للمستخدم ليختار منها."""
    owner_id = update.effective_user.id

    # تحديد الرسالة الأصلية التي سيتم الرد عليها (تجنباً لأخطاء التعديل)
    original_message = update.message or (update.callback_query.message if update.callback_query else None)
    if not original_message: return ConversationHandler.END

    saved_emails = get_import_emails_by_owner(owner_id)

    if not saved_emails:
        await original_message.reply_text( # 🚨 تغيير: استخدام original_message.reply_text
            _("tfa_no_import_emails_error", owner_id),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("go_back_button", owner_id), callback_data="go_back")]])
        )
        return TFA_MENU

    keyboard = []
    for email_row in saved_emails:
        keyboard.append([
            InlineKeyboardButton(email_row['email_address'], callback_data=f"tfa_execute_change_email:{email_row['id']}")
        ])
    keyboard.append([InlineKeyboardButton(_("cancel_button", owner_id), callback_data="go_back")])

    # 🚨 تغيير: استخدام original_message.reply_text
    await original_message.reply_text(
        _("tfa_select_email_title", owner_id),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    # 🚨 إضافة: حذف الرسالة الأصلية التي أدت إلى هذا التوجيه (إذا كانت من CallBackQuery)
    if update.callback_query and update.callback_query.message:
        try:
            await update.callback_query.message.delete()
        except BadRequest as e:
            logger.warning(f"Failed to delete original message in tfa_select_recovery_email_from_list: {e}")

    return TFA_MENU
# ... (بقية الكود) ...


# ... (الكود الموجود لديك قبل الدالة) ...
async def _execute_recovery_email_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [مُعدّل] ينفذ تغيير البريد باستخدام كلمة المرور النصية الصحيحة.
    """
    query = update.callback_query
    owner_id = query.from_user.id
    phone = context.user_data.get('selected_phone')
    client: TelegramClient = context.user_data['client']
    
    current_password_str = context.user_data.get('tfa_current_password_str')
    if not current_password_str:
        await query.message.edit_text("❌ خطأ: لم يتم العثور على كلمة المرور للتحقق. يرجى المحاولة مرة أخرى.")
        return await mock_update_and_call(tfa_management_menu_start, update, context, 'mng:manage_2fa', push=False)

    email_id = int(query.data.split(':')[1])
    email_row = get_import_email_by_id(email_id, owner_id)
    if not email_row:
        await query.message.edit_text("❌ لم يتم العثور على الإيميل المختار. يرجى المحاولة مرة أخرى.")
        return await mock_update_and_call(tfa_management_menu_start, update, context, 'mng:manage_2fa', push=False)


    new_email = email_row['email_address']
    app_pass = decrypt_email_password_base64(email_row['app_password_encrypted'])

    msg = await query.message.edit_text(_("tfa_changing_password", owner_id))

    async def get_single_2fa_email_code_callback(is_resend=False):
        await asyncio.sleep(3) # <== إضافة تأخير 5 ثوانٍ
        await msg.edit_text(_("2fa_email_verify_auto_attempt", owner_id))
        code = await find_telegram_code_in_gmail(new_email, app_pass)
        if not code:
            raise EmailUnconfirmedError("فشل جلب الكود تلقائياً من Gmail.")
        await msg.edit_text(_("2fa_email_verify_auto_success", owner_id))
        return code

    try:
        # 🚨🚨🚨 هنا هو التعديل الحاسم: نمرر فقط current_password_str و email (بدون new_password) 🚨🚨🚨
        await client.edit_2fa(
    current_password=current_password_str,
    new_password=current_password_str, # <== هذا هو السطر الجديد والمهم
    email=new_email,
    email_code_callback=get_single_2fa_email_code_callback
        )
        
        await msg.edit_text(_("tfa_email_change_success", owner_id))
        log_activity(phone, "تغيير بريد 2FA", "نجاح")
        save_2fa_password(owner_id, phone, current_password_str, DEFAULT_2FA_HINT, new_email)

    except EmailUnconfirmedError as e:
        await msg.edit_text(_("tfa_email_change_failed", owner_id, error=f"{_('2fa_email_verify_auto_fail', owner_id)} ({e})"))
        log_activity(phone, "فشل تغيير بريد 2FA", f"{_('2fa_email_verify_auto_fail', owner_id)} ({e})")
    except Exception as e:
        await msg.edit_text(_("tfa_email_change_failed", owner_id, error=str(e)))
        log_activity(phone, "فشل تغيير بريد 2FA", str(e))
    
    await asyncio.sleep(2)
    context.user_data.pop('tfa_current_password_str', None)
    return await mock_update_and_call(tfa_management_menu_start, update, context, 'mng:manage_2fa', push=False)
# ... (بقية الكود الموجود لديك) ...


    async def get_code_from_gmail():
        await msg.edit_text(_("2fa_email_verify_auto_attempt", owner_id))
        code = await find_telegram_code_in_gmail(new_email, app_pass)
        if not code:
            raise Exception("فشل جلب الكود تلقائياً من Gmail.")
        await msg.edit_text(_("2fa_email_verify_auto_success", owner_id))
        return code

    try:
        # ==> استخدام كلمة المرور النصية الصحيحة هنا
        await client.edit_2fa(
            current_password=current_password_str,
            email=new_email,
            email_code_callback=get_code_from_gmail
        )
        
        await msg.edit_text(_("tfa_email_change_success", owner_id))
        log_activity(phone, "تغيير بريد 2FA", "نجاح")

    except Exception as e:
        await msg.edit_text(_("tfa_email_change_failed", owner_id, error=str(e)))
        log_activity(phone, "فشل تغيير بريد 2FA", str(e))
    
    await asyncio.sleep(2)
    # مسح كلمة المرور من الذاكرة بعد الاستخدام
    context.user_data.pop('tfa_current_password_str', None)
    # العودة إلى قائمة 2FA
    return await mock_update_and_call(tfa_management_menu_start, update, context, 'mng:manage_2fa', push=False)


async def tfa_disable_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    owner_id = update.effective_user.id
    phone = context.user_data.get('selected_phone')
    client: TelegramClient = context.user_data['client']

    msg = await update.message.reply_text(_("tfa_changing_password", owner_id))
    try:
        # To disable, we set new_password to an empty string
        await client.edit_2fa(current_password=password, new_password="")
        await msg.edit_text(_("tfa_disable_success", owner_id))
        log_activity(phone, "تعطيل 2FA", "نجاح")
    except Exception as e:
        await msg.edit_text(_("tfa_disable_failed", owner_id, error=e))
        log_activity(phone, "فشل تعطيل 2FA", str(e))

    await asyncio.sleep(2)
    return await go_back(update, context)

# ... (ضع هذا الكود في مكان مناسب، مثلاً مع دوال معالجة الإيميل أو قبل دالة main مباشرة) ...

async def cancel_fetch_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the email selection and returns to the email management menu."""
    user_id = update.effective_user.id
    await update.callback_query.answer(_("action_cancelled", user_id))
    
    # --- بداية التعديل ---
    # تم حذف السطر الذي كان يقوم بحذف الرسالة، والذي كان يسبب الخطأ
    # try:
    #     await update.callback_query.message.delete()
    # except ...
    # --- نهاية التعديل ---
    
    # الآن نعود مباشرة إلى قائمة إدارة الإيميلات، والتي ستقوم بتعديل الرسالة الموجودة
    return await mock_update_and_call(manage_import_emails_start, update, context, 'manage_emails_start', push=False)


# ... (بقية الكود الموجود لديك) ...

# ==============================================================================
# ||                       أخيراً: الدالة الرئيسية لتشغيل البوت                  ||
# ==============================================================================

def main() -> None:
    """الدالة الرئيسية لتشغيل البوت وإعداد المعالجات."""
    init_db()
    builder = Application.builder().token(TOKEN)
    builder.post_init(post_init)
    application = builder.build()

    # --- معالجات عامة ---
    cancel_handler = CommandHandler("cancel", cancel_action)
    go_back_handler = CallbackQueryHandler(go_back, pattern='^go_back$')

    # --- تعريف المحادثات (يجب أن يكون هنا داخل الدالة) ---
    
    # هذا هو المعالج الجديد الذي يدمج بين أمر البداية واختيار اللغة
    # هذا هو المعالج الجديد الذي يدمج بين أمر البداية واختيار اللغة
    language_and_start_conv = ConversationHandler(
        # --- بداية التعديل ---
        # أضفنا نقطة دخول جديدة لأمر /lang
        entry_points=[
            CommandHandler("start", start_command),
            CommandHandler("lang", choose_language) # <-- هذا هو السطر الجديد
        ],
        # --- نهاية التعديل ---
        states={
            LANG_SELECT: [CallbackQueryHandler(set_language, pattern=r'^set_lang:(ar|en)$')],
        },
        fallbacks=[CommandHandler("start", start_command)], # للسماح للمستخدم بإعادة البدء
        per_user=True, per_message=False, allow_reentry=True
    )


    manage_emails_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(manage_import_emails_start, pattern='^manage_emails_start$')],
        states={
            MANAGE_EMAILS_MENU: [CallbackQueryHandler(handle_email_action, pattern=r'^emails:')],
            EMAILS_GET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, emails_get_address)],
            EMAILS_GET_APP_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, emails_get_app_pass)],
            FETCH_EMAIL_SELECT: [CallbackQueryHandler(fetch_email_execute, pattern=r'^fetch_email_exec:')],
        },
        fallbacks=[
            CommandHandler("start", start_command), # <-- تم التعديل
            cancel_handler, 
            go_back_handler, 
            CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$'),
            CallbackQueryHandler(cancel_fetch_email, pattern='^cancel_fetch_email$')
        ],
        per_user=True, per_message=False, allow_reentry=True
    )

    add_account_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_account_start, pattern='^add_account_start$'),
            CallbackQueryHandler(start_relogin_flow, pattern=r'^start_relogin_flow:')
        ],
        states={
            ADD_AWAIT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_process_input),
                              MessageHandler(filters.Document.FileExtension("session"), add_process_session_file)],
            ADD_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_get_code)],
            ADD_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_get_password)],
        },
        fallbacks=[CommandHandler("start", start_command), cancel_handler, go_back_handler], # <-- تم التعديل
        per_user=True, per_message=False, allow_reentry=True
    )

    manage_accounts_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(manage_accounts_start, pattern=r'^manage_accounts_start:?\d*$'),
            CallbackQueryHandler(tfa_management_menu_start, pattern=r'^mng:manage_2fa$'),
            CallbackQueryHandler(autoreply_menu_start, pattern=r'^autoreply:menu:'),
            CallbackQueryHandler(story_menu_start, pattern=r'^story:menu:'),
            CallbackQueryHandler(show_single_contact_menu, pattern=r'^s_contacts:menu$'),
        ],
        states={
            SELECT_ACCOUNT: [CallbackQueryHandler(select_account_for_management, pattern=r'^select_acc:')],
            MANAGE_ACCOUNT: [
                CallbackQueryHandler(handle_management_action, pattern=r'^mng:'),
                CallbackQueryHandler(tfa_management_menu_start, pattern=r'^mng:manage_2fa$'),
                CallbackQueryHandler(select_account_for_management, pattern=r'^select_acc:'),
                CallbackQueryHandler(show_single_contact_menu, pattern=r'^s_contacts:menu'),
            ],
            GET_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_new_name)],
            GET_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_new_bio)],
            GET_PHOTO: [MessageHandler(filters.PHOTO, process_new_photo)],
            SET_NEW_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_username)],
            ASSIGN_PROXY_SELECT_ACCOUNT: [CallbackQueryHandler(assign_proxy_to_selected_account, pattern=r'^proxy_assign:')],
            
            SINGLE_CONTACT_MENU: [
                CallbackQueryHandler(single_add_contacts_prompt, pattern=r'^s_contacts:add_prompt$'),
                CallbackQueryHandler(single_delete_contacts_confirm, pattern=r'^s_contacts:delete_confirm$'),
                CallbackQueryHandler(execute_single_export_contacts, pattern=r'^s_contacts:export$'),
            ],
            SINGLE_CONTACT_GET_LIST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, execute_single_add_contacts),
                MessageHandler(filters.Document.FileExtension("txt"), add_contacts_from_file)
            ],
            SINGLE_CONTACT_CONFIRM_DELETE: [CallbackQueryHandler(execute_single_delete_contacts, pattern=r'^s_contacts:execute_delete$')],

            SET_NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, tfa_change_password_start)],
            CONFIRM_NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, tfa_change_password_confirm)],
            TFA_GET_NEW_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tfa_set_new_pass)],
            TFA_GET_HINT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tfa_set_hint), CommandHandler("skip", tfa_skip_hint)],
            TFA_GET_RECOVERY_EMAIL: [MessageHandler(filters.Regex(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'), tfa_set_recovery_email)],
            TFA_GET_EMAIL_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tfa_confirm_email_code)],

            TFA_MENU: [
                CallbackQueryHandler(tfa_handle_submenu_action, pattern=r'^tfa_menu:'),
                CallbackQueryHandler(_execute_recovery_email_change, pattern=r'^tfa_execute_change_email:')
            ],
            TFA_CHANGE_EMAIL_GET: [MessageHandler(filters.TEXT & ~filters.COMMAND, tfa_verify_password_for_email_change)],
            TFA_DISABLE_GET_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tfa_disable_execute)],

            CLEANER_MENU_SINGLE: [CallbackQueryHandler(single_cleaner_confirm, pattern=r'^single_clean:confirm:')],
            CLEANER_CONFIRM_SINGLE: [CallbackQueryHandler(single_cleaner_execute, pattern=r'^single_clean:execute$')],

            AUTOREPLY_MENU: [CallbackQueryHandler(autoreply_handle_action, pattern=r'^autoreply:')],
            AUTOREPLY_GET_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, autoreply_get_keyword)],
            AUTOREPLY_GET_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, autoreply_get_response)],
        },
        fallbacks=[
            CommandHandler("start", start_command), # <-- تم التعديل
            cancel_handler, 
            go_back_handler,
            CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$'),
        ],
        per_user=True, per_message=False, allow_reentry=True
    )

    manage_proxies_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(manage_proxies_start, pattern=r'^manage_proxies_start:?\d*$')],
        states={
            MANAGE_PROXIES: [
                CallbackQueryHandler(proxy_details, pattern=r'^proxy_details:'),
                CallbackQueryHandler(delete_proxy, pattern=r'^proxy_delete:'),
                CallbackQueryHandler(add_proxy_start, pattern=r'^proxy_add_start$'),
            ],
            ADD_PROXY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_proxy_input)],
        },
        fallbacks=[CommandHandler("start", start_command), cancel_handler, go_back_handler, CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$')], # <-- تم التعديل
        per_user=True, per_message=False, allow_reentry=True
    )

    unified_bulk_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_bulk_action, pattern=r'^unified_bulk:(joiner|leaver|logout|members|cleaner|bulk_export|bulk_story|bulk_bio|bulk_name|bulk_photo|reset_sessions|add_contacts|delete_contacts|export_contacts|bulk_proxy|bulk_2fa)$'),
            CallbackQueryHandler(bulk_delete_options, pattern=r'^unified_bulk:deleter_start$')
        ],
        states={
            SELECT_ACCOUNTS_FOR_ACTION: [
                CallbackQueryHandler(select_accounts_for_bulk_action, pattern=r'^(multi_select:|select_accounts_for_bulk_action:page)'),
                CallbackQueryHandler(bulk_2fa_choose_mode, pattern=r'^bulk_confirm_selection:bulk_2fa_options$'),
                CallbackQueryHandler(route_bulk_confirmation, pattern=r'^bulk_confirm_selection:')
            ], 
            GET_LINK_FOR_BULK_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_bulk_join_leave)],
            BULK_GET_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_bulk_bio_change)],
            BULK_GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_bulk_name_change)],
            BULK_GET_PHOTO: [MessageHandler(filters.PHOTO, execute_bulk_photo_change)],
            BULK_CONTACTS_GET_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_bulk_add_contacts)],
            CONFIRM_BULK_NO_LINK_ACTION: [CallbackQueryHandler(execute_bulk_no_link, pattern=r'^execute_bulk_no_link$')],
            BULK_DELETE_OPTIONS: [CallbackQueryHandler(start_bulk_delete_with_type, pattern=r'^select_bulk_delete_type:')],
            BULK_EXPORT_CONFIRM: [CallbackQueryHandler(bulk_export_execute, pattern=r'^bulk_export_execute$')],
            SCRAPER_SELECT_TYPE: [CallbackQueryHandler(scraper_get_limit, pattern=r'^scraper_set_type:')],
            SCRAPER_GET_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, scraper_get_group_link)],
            CONFIRM_BULK_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_member_scraper)],
            CLEANER_OPTIONS: [CallbackQueryHandler(cleaner_confirm, pattern=r'cleaner_confirm:')],
            CLEANER_CONFIRM: [CallbackQueryHandler(cleaner_execute, pattern=r'cleaner_execute')],
            BULK_STORY_GET_FILE: [MessageHandler(filters.PHOTO | filters.VIDEO, bulk_story_get_caption)],
            BULK_STORY_GET_CAPTION: [
                CommandHandler("skip", bulk_story_skip_caption),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bulk_story_ask_privacy)
            ],
            BULK_STORY_ASK_PRIVACY: [CallbackQueryHandler(bulk_story_set_privacy, pattern=r'^bulk_story:set_privacy:')], 
            BULK_STORY_ASK_PERIOD: [CallbackQueryHandler(bulk_story_set_period, pattern=r'^bulk_story:set_period:')], 
            BULK_STORY_CONFIRM: [CallbackQueryHandler(execute_bulk_story_post, pattern=r'^bulk_story_execute$')],
            BULK_SELECT_PROXY: [CallbackQueryHandler(execute_bulk_proxy_assign, pattern=r'^bulk_assign_proxy:')],
            BULK_2FA_CHOOSE_MODE: [CallbackQueryHandler(bulk_2fa_handle_mode_selection, pattern=r'^2fa_mode:')],
            BULK_2FA_GET_UNIFIED_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_bulk_2fa)],
        },
        fallbacks=[
            CommandHandler("start", start_command), # <-- تم التعديل
            cancel_handler, 
            go_back_handler, 
            CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$'),
            CallbackQueryHandler(cancel_bulk_selection_action, pattern='^cancel_bulk_selection$'),
            CallbackQueryHandler(back_to_delete_options, pattern='^back_to_delete_options$'),
            CallbackQueryHandler(show_bulk_action_options, pattern='^show_bulk_action_options$'),
        ],
        per_user=True, per_message=False, allow_reentry=True
    )

    scheduler_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(scheduler_menu_start, pattern='^scheduler_menu_start$')],
        states={
            SCHEDULER_MENU: [
                CallbackQueryHandler(scheduler_add_start, pattern='^scheduler:add_start$'),
                CallbackQueryHandler(scheduler_handle_action, pattern=r'^scheduler:(delete|pause|resume):'),
            ],
            SCHEDULER_SELECT_TYPE: [CallbackQueryHandler(scheduler_set_type, pattern='^scheduler:set_type:'),],
            SELECT_ACCOUNTS_FOR_ACTION: [
                CallbackQueryHandler(select_accounts_for_bulk_action, pattern=r'^(multi_select:|select_accounts_for_bulk_action:page)'),
                CallbackQueryHandler(scheduler_get_target, pattern=r'^bulk_confirm_selection:scheduler_options$'),
                CallbackQueryHandler(scheduler_get_cron, pattern=r'^bulk_confirm_selection:no_link$') 
            ],
            SCHEDULER_GET_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, scheduler_get_content)],
            SCHEDULER_GET_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, scheduler_get_cron)],
            SCHEDULER_GET_CRON: [MessageHandler(filters.TEXT & ~filters.COMMAND, scheduler_save_task)]
        },
        fallbacks=[CommandHandler("start", start_command), cancel_handler, go_back_handler, CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$')], # <-- تم التعديل
        per_user=True, per_message=False, allow_reentry=True
    )

    story_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(story_menu_start, pattern=r'^story:menu:')],
        states={
            STORY_MENU: [CallbackQueryHandler(story_handle_action, pattern=r'^story:action:')],
            STORY_GET_FILE: [MessageHandler(filters.PHOTO | filters.VIDEO, story_get_file)],
            STORY_GET_CAPTION: [
                CommandHandler("skip", story_skip_caption),
                MessageHandler(filters.TEXT & ~filters.COMMAND, story_get_caption)
            ],
            STORY_ASK_PRIVACY: [CallbackQueryHandler(story_set_privacy, pattern=r'^story:set_privacy:')],
            STORY_ASK_PERIOD: [CallbackQueryHandler(story_set_period, pattern=r'^story:set_period:')],
        },
        fallbacks=[CommandHandler("start", start_command), cancel_handler, go_back_handler], # <-- تم التعديل
        per_user=True, per_message=False, allow_reentry=True
    )

    bot_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot_admin_menu_start, pattern='^bot_admin_menu$')],
        states={
            BOT_ADMIN_MENU: [
                CallbackQueryHandler(sub_activate_start, pattern='^admin:sub_add$'),
                CallbackQueryHandler(sub_deactivate_start, pattern='^admin:sub_rem$'),
                CallbackQueryHandler(sub_deactivate_confirm, pattern=r'^admin:sub_rem_confirm:'),
                CallbackQueryHandler(sub_list_all, pattern='^admin:sub_list$'),
                CallbackQueryHandler(sub_info_card, pattern=r'^admin:sub_info:'),
                CallbackQueryHandler(broadcast_start, pattern='^admin:broadcast_start$'),
                CallbackQueryHandler(admin_monitor_resources, pattern='^admin:monitor$'),
                CallbackQueryHandler(admin_backup_db, pattern='^admin:backup$'),
                CallbackQueryHandler(admin_restore_start, pattern='^admin:restore_start$'),
                CallbackQueryHandler(admin_restart_confirm, pattern=r'^admin:restart_confirm$'),
                CallbackQueryHandler(admin_cancel_tasks_confirm, pattern=r'^admin:cancel_tasks_confirm$'),
            ],
            SUB_GET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_activate_get_id)],
            SUB_GET_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_activate_get_days)],
            BROADCAST_GET_TARGET_TYPE: [
                CallbackQueryHandler(broadcast_get_message, pattern='^broadcast_target:all$'),
                CallbackQueryHandler(broadcast_get_target_params, pattern=r'^broadcast_target:(by_date|by_accounts|by_ids)$')
            ],
            BROADCAST_GET_TARGET_PARAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_get_message)],
            BROADCAST_GET_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_confirm)],
            BROADCAST_CONFIRM: [CallbackQueryHandler(broadcast_execute, pattern='^admin:broadcast_send')],
            ADMIN_RESTORE_CONFIRM: [MessageHandler(filters.Document.FileExtension("db"), admin_restore_receive_file)],
            ADMIN_RESTART_CONFIRM: [CallbackQueryHandler(admin_restart_execute, pattern='^admin:restart_execute$')],
            ADMIN_CANCEL_TASKS_CONFIRM: [CallbackQueryHandler(admin_cancel_tasks_execute, pattern='^admin:cancel_tasks_execute$')],
        },
        fallbacks=[CommandHandler("start", start_command), cancel_handler, go_back_handler, CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$'), # <-- تم التعديل
            CallbackQueryHandler(broadcast_start, pattern='^admin:broadcast_start$')
        ],
        per_user=True, per_message=False, allow_reentry=True
    )

    # --- إضافة المعالجات إلى التطبيق ---
    # تم حذف application.add_handler(lang_conv) لأنه تم دمجه
    application.add_handler(language_and_start_conv) # <-- المعالج المدمج الجديد
    application.add_handler(manage_emails_conv)
    application.add_handler(bot_admin_conv)
    application.add_handler(add_account_conv)
    application.add_handler(manage_accounts_conv)
    application.add_handler(story_conv)
    application.add_handler(manage_proxies_conv)
    application.add_handler(unified_bulk_conv)
    application.add_handler(scheduler_conv)

    # المعالجات العامة والمستقلة
    application.add_handler(CallbackQueryHandler(dashboard, pattern='^dashboard$'))
    application.add_handler(CallbackQueryHandler(show_management_options, pattern='^show_management_options$'))
    application.add_handler(CallbackQueryHandler(show_bulk_action_options, pattern='^show_bulk_action_options$'))
    application.add_handler(CallbackQueryHandler(show_scraper_menu, pattern='^scraper_menu$'))
    application.add_handler(CallbackQueryHandler(check_accounts_start, pattern='^check_accounts_start$'))
    application.add_handler(CallbackQueryHandler(export_accounts_csv, pattern='^export_csv$'))
    application.add_handler(CallbackQueryHandler(check_subscription_status, pattern='^check_subscription_status$'))
    application.add_handler(CallbackQueryHandler(handle_quick_action, pattern='^quick_action:'))
    application.add_handler(CallbackQueryHandler(close_message, pattern='^close_message$'))
    application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$'))
    
    print("=========================================================")
    print("||   بوت الإمبراطور (الإصدار 9.7 - إدارة 2FA) يعمل الآن...   ||")
    print("=========================================================")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main() 

