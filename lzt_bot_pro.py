# -*- coding: utf-8 -*-

# =====================================================================================
# LZT MARKET PRO BOT (V2.9 - Final Stability Release by Gemini)
# =====================================================================================
# هذا الملف يحتوي على كامل منطق البوت بعد إصلاحات شاملة للاستقرار،
# وتحديث آلية قراءة البيانات لتتوافق مع آخر تغييرات API، وحل مشاكل المزامنة.
# -------------------------------------------------------------------------------------
# المتطلبات: لتشغيل هذا البوت، تحتاج لتثبيت المكتبات التالية
# pip install python-telegram-bot --upgrade
# pip install httpx pandas matplotlib
# -------------------------------------------------------------------------------------

# --- 1. استيراد المكتبات (Imports) ---
import logging
import json
import asyncio
import sqlite3
import time
import os
import re
import html
import io
import traceback
from datetime import datetime, timedelta

# مكتبات تيليجرام
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError

# مكتبات خارجية
import httpx
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================================================
# --- 2. الإعدادات العامة والتهيئة (Global Setup & Config) ---
# =====================================================================================

# إعداد نظام تسجيل الأحداث (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
# تجاهل رسائل الـ INFO من المكتبات الأخرى لجعل الـ log أنظف
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

# [مهم] ضع التوكنات الخاصة بك هنا.
# تحذير: هذه الطريقة مناسبة للاستخدام الشخصي فقط. لا تشارك هذا الملف مع أي شخص.
CONFIG = {
    "TELEGRAM_TOKEN": "6821885261:AAEMomjEJxCYokKGyup_sEvjPA386sOk0Yk",
    "OWNER_ID": 6831264078,
    "LZT_API_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzUxMiJ9.eyJzdWIiOjkwMTgxNTIsImlzcyI6Imx6dCIsImlhdCI6MTc1MDg3Nzc1MywianRpIjoiODA1NzA1Iiwic2NvcGUiOiJiYXNpYyByZWFkIHBvc3QgY29udmVyc2F0ZSBwYXltZW50IGludm9pY2UgbWFya2V0In0.emhkaRaLTX3E2N44GeZPZ51Uw9-N1zAQ6zMuX751eMoOX52kZxHDD-Wsz3OdOlaoiVGXJNtFUeqxOSyvARc1H9LvOSW3kflcncRD2XM3GrkbrH_oL7e-T-qUy3S8IUP2hR0DWfPsc1L_WhqA_LEJf6Zsxh9BhmfJ9MrRLb5ne8Q"
}

# التحقق من وجود التوكنات الأساسية
if not CONFIG["TELEGRAM_TOKEN"] or not CONFIG["OWNER_ID"] or not CONFIG["LZT_API_TOKEN"]:
    logging.critical("أحد التوكنات (TELEGRAM_TOKEN, OWNER_ID, LZT_API_TOKEN) غير موجود. يرجى ملء البيانات في قسم CONFIG.")
    exit()


# تعريف أسماء الملفات وقيم المحادثات
DATABASE_FILE = 'lzt_data.db'
(
    # حالات محادثة البحث المتقدم
    SELECT_CATEGORY, SET_MAX_PRICE,
    # حالات محادثة إضافة قاعدة شراء
    ADD_RULE_CAT, ADD_RULE_PRICE, ADD_RULE_KEYWORDS
) = range(5)

# =====================================================================================
# --- 3. وحدة إدارة قاعدة البيانات (Database Module) ---
# =====================================================================================

def get_db_connection():
    """إنشاء اتصال مع قاعدة البيانات SQLite."""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """إنشاء الجداول اللازمة في قاعدة البيانات عند أول تشغيل."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # جدول المشتريات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
        item_id INTEGER PRIMARY KEY, title TEXT NOT NULL, price REAL NOT NULL, purchase_date INTEGER NOT NULL
    )''')
    # جدول المفضلة
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        item_id INTEGER PRIMARY KEY, title TEXT NOT NULL, price REAL, added_date INTEGER NOT NULL
    )''')
    # جدول قواعد الشراء التلقائي
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS autobuy_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        keywords TEXT,
        max_price REAL NOT NULL,
        is_active INTEGER DEFAULT 1,
        last_checked_ts INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()
    logging.info("تم فحص وتهيئة قاعدة البيانات بنجاح.")

def get_item_purchase_date(item: dict) -> int:
    """[تحسين V2.7] جلب تاريخ الشراء من المنتج، مع تجربة عدة مفاتيح محتملة لزيادة استقرار البوت."""
    possible_keys = ['purchase_date', 'item_update_date', 'item_publish_date', 'create_date', 'last_activity']
    for key in possible_keys:
        if key in item and item[key] is not None:
            return int(item[key])
            
    logging.warning(f"لم يتم العثور على مفتاح تاريخ صالح للمنتج ID {item.get('item_id')}. استخدام الوقت الحالي كقيمة افتراضية.")
    return int(time.time())

def add_purchase_batch(items):
    """[إصلاح V2.7] استخدام دالة مساعدة لجلب تاريخ الشراء بشكل آمن ومرن."""
    conn = get_db_connection()
    purchases_to_insert = [(item['item_id'], item['title'], item['price'], get_item_purchase_date(item)) for item in items]
    conn.cursor().executemany("INSERT OR IGNORE INTO purchases (item_id, title, price, purchase_date) VALUES (?, ?, ?, ?)", purchases_to_insert)
    conn.commit()
    conn.close()

def get_purchases_for_period(start_ts, end_ts):
    conn = get_db_connection()
    return conn.cursor().execute("SELECT purchase_date, price FROM purchases WHERE purchase_date BETWEEN ? AND ?", (start_ts, end_ts)).fetchall()

def get_purchases(limit=5, offset=0):
    conn = get_db_connection()
    return conn.cursor().execute("SELECT * FROM purchases ORDER BY purchase_date DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()

def get_purchases_count():
    conn = get_db_connection()
    return conn.cursor().execute("SELECT COUNT(*) FROM purchases").fetchone()[0]

def add_favorite(item_id, title, price):
    conn = get_db_connection()
    conn.cursor().execute("INSERT OR REPLACE INTO favorites (item_id, title, price, added_date) VALUES (?, ?, ?, ?)", (item_id, title, price, int(time.time())))
    conn.commit()
    conn.close()

def remove_favorite(item_id):
    conn = get_db_connection()
    conn.cursor().execute("DELETE FROM favorites WHERE item_id = ?", (item_id,))
    conn.commit()
    conn.close()

def is_favorite(item_id):
    conn = get_db_connection()
    result = conn.cursor().execute("SELECT 1 FROM favorites WHERE item_id = ?", (item_id,)).fetchone()
    conn.close()
    return result is not None

def get_favorites(limit=5, offset=0):
    conn = get_db_connection()
    return conn.cursor().execute("SELECT * FROM favorites ORDER BY added_date DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()

def get_favorites_count():
    conn = get_db_connection()
    return conn.cursor().execute("SELECT COUNT(*) FROM favorites").fetchone()[0]

def add_autobuy_rule(category_id, category_name, max_price, keywords=None):
    conn = get_db_connection()
    current_timestamp = int(time.time())
    conn.cursor().execute("INSERT INTO autobuy_rules (category_id, category_name, max_price, keywords, last_checked_ts) VALUES (?, ?, ?, ?, ?)",
                          (category_id, category_name, max_price, keywords, current_timestamp))
    conn.commit()
    conn.close()

def get_autobuy_rules():
    conn = get_db_connection()
    return conn.cursor().execute("SELECT * FROM autobuy_rules WHERE is_active = 1").fetchall()

def update_rule_last_check(rule_id, timestamp):
    conn = get_db_connection()
    conn.cursor().execute("UPDATE autobuy_rules SET last_checked_ts = ? WHERE id = ?", (timestamp, rule_id))
    conn.commit()
    conn.close()

def remove_autobuy_rule(rule_id):
    conn = get_db_connection()
    conn.cursor().execute("DELETE FROM autobuy_rules WHERE id = ?", (rule_id,))
    conn.commit()
    conn.close()

# =====================================================================================
# --- 4. وحدة عميل LZT API (API Client) ---
# =====================================================================================

class LZT_API_Client:
    """تم تحديث الـ base_url والمسارات لتتوافق مع API الجديد."""
    def __init__(self, token: str):
        self.base_url = "https://api.zelenka.guru"
        self.token = token
        self.client = httpx.AsyncClient(headers=self._get_headers(), timeout=30.0)

    def _get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
    
    async def close_session(self):
        if hasattr(self, 'client') and not self.client.is_closed:
            await self.client.aclose()
            logging.info("تم إغلاق جلسة httpx بنجاح.")

    async def _make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> (dict | None, str | None):
        url = f"{self.base_url}/{endpoint}"
        try:
            if method.upper() == 'GET':
                response = await self.client.get(url, params=params)
            elif method.upper() == 'POST':
                response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json(), None
        except httpx.HTTPStatusError as e:
            error_message = f"Code {e.response.status_code} - {e.response.text}"
            logging.error(f"API Error on {url}: {error_message}")
            if e.response.status_code in [401, 403]:
                return None, "توكن API غير صالح أو منتهي الصلاحية. يرجى تحديثه."
            if e.response.status_code == 404:
                return None, "المسار المطلوب غير موجود في الـ API."
            return None, error_message
        except Exception as e:
            logging.error(f"Connection Error on {url}: {e}")
            return None, "فشل الاتصال بالـ API. تحقق من اتصالك بالانترنت."

    async def get_user_profile(self):
        return await self._make_request('GET', "users/me")

    async def get_my_purchases(self, page: int = 1):
        params = {'item_state': 'purchased', 'page': page}
        return await self._make_request('GET', "market/", params=params)

    async def get_my_items_for_sale(self, user_id: int):
        return await self._make_request('GET', f"market/user/{user_id}/items")

    async def get_market_items(self, category_id: int = None, price_to: float = None, title: str = None, created_at: int = None, page: int = 1):
        params = {'order_by': 'pdate'}
        if category_id: params['category_id'] = category_id
        if price_to: params['price_to'] = price_to
        if title: params['title'] = title
        if created_at: params['created_since_timestamp'] = created_at
        if page > 1: params['page'] = page
        return await self._make_request('GET', "market/", params=params)

    async def get_item_details(self, item_id: int):
        return await self._make_request('GET', f"market/{item_id}")

    async def get_market_categories(self):
        data, error = await self._make_request('GET', "market/categories")
        if data and 'categories' in data:
            return data['categories'], error
        return None, error

# =====================================================================================
# --- 5. وحدة الأزرار والترجمة (Keyboards & Localization) ---
# =====================================================================================

STRINGS = {
    'ar': {
        'welcome': "👋 مرحباً بك في بوت LZT المطور (V2.9)!\nاختر من القائمة أو استخدم /help للمساعدة:",
        'help_text': ("أهلاً بك!\nإليك قائمة بالأوامر المتاحة:\n\n"
                      "*/start* - بدء البوت وعرض القائمة الرئيسية.\n"
                      "*/help* - عرض هذه الرسالة.\n"
                      "*/compare ID1 ID2* - مقارنة سريعة بين منتجين."),
        'back_btn': "⬅️ رجوع",
        'cancel_btn': "🔙 إلغاء",
        'next_btn': "التالي ⬅️",
        'prev_btn': "➡️ السابق",
        'page': "صفحة {current}/{total}",
        'loading': "⏳ جارٍ التحميل...",
        'error': "خطأ",
        'operation_cancelled': "تم إلغاء العملية.",
        'account_analysis': "👤 حسابي وتحليلاتي",
        'my_items_for_sale_btn': "📦 منتجاتي للبيع",
        'market_btn': "📈 السوق",
        'autobuy_btn': "🤖 الأتمتة (شراء تلقائي)",
        'favorites_btn': "❤️ مفضلاتي",
        'settings_btn': "⚙️ الإعدادات",
        'balance_stats': "💰 الرصيد والإحصائيات",
        'purchase_history': "📜 سجل المشتريات",
        'cashflow_chart': "📊 تحليل التدفق النقدي",
        'monthly_summary': "🧾 ملخص شهري",
        'lzt_profile': "ملف LZT.market الشخصي",
        'username': "اسم المستخدم",
        'balance': "الرصيد",
        'total_purchases': "إجمالي المشتريات",
        'positive_feedback': "التقييمات الإيجابية",
        'negative_feedback': "التقييمات السلبية",
        'registration_date': "تاريخ التسجيل",
        'no_purchases_synced': "لا يوجد مشتريات مسجلة. قم بالمزامنة أولاً.",
        'last_purchases': "سجل المشتريات",
        'price_label': "بسعر",
        'date_label': "بتاريخ",
        'generating_chart': "⏳ جارٍ إنشاء الرسم البياني...",
        'no_data_for_chart': "لا توجد بيانات كافية لآخر 30 يوماً لإنشاء الرسم البياني.",
        'cashflow_chart_title': "التدفق النقدي للمشتريات (آخر 30 يوماً)",
        'date_label_chart': "التاريخ",
        'spending_usd': "الإنفاق (دولار)",
        'cashflow_chart_caption': "هذا الرسم البياني يوضح إنفاقك اليومي.",
        'no_data_for_summary': "لا توجد مشتريات هذا الشهر لعرض ملخص.",
        'monthly_summary_title': "ملخص الشهر الحالي",
        'total_spent': "إجمالي المصروفات",
        'number_of_deals': "عدد الصفقات",
        'highest_deal': "أعلى صفقة",
        'loading_my_items': "⏳ جارٍ جلب منتجاتك...",
        'error_profile': "خطأ في جلب ملفك الشخصي",
        'no_items_for_sale': "ℹ️ ليس لديك أي منتجات معروضة للبيع حالياً.",
        'your_items_for_sale': "منتجاتك المعروضة للبيع",
        'view_my_items': "🏷️ عرض منتجاتي للبيع",
        'advanced_search': "🔎 بحث متقدم (فلاتر)",
        'random_item': "🎲 منتج عشوائي",
        'quick_analysis': "📊 تحليل سريع للسوق",
        'choosing_random_item': "🎲 جارٍ اختيار منتج عشوائي...",
        'cant_fetch_items': "❌ لم أتمكن من جلب المنتجات.",
        'analyzing_market': "📊 جارٍ إجراء تحليل سريع للسوق...",
        'cant_fetch_items_for_analysis': "❌ لم أتمكن من جلب المنتجات للتحليل.",
        'quick_analysis_title': "تحليل سريع لآخر المنتجات",
        'cheapest_item': "أرخص منتج",
        'most_viewed_item': "المنتج الأكثر مشاهدة",
        'with_views': "مع",
        'failed_to_fetch_categories': "❌ فشل في جلب أقسام السوق.",
        'choose_category_search': "1️⃣ اختر القسم المطلوب للبحث:",
        'category_chosen': "2️⃣ تم اختيار قسم: **{category_name}**.\n\nالآن، أرسل أقصى سعر (أو أرسل '0' للتخطي).",
        'price_must_be_number': "❌ السعر يجب أن يكون رقماً. حاول مجدداً.",
        'searching_with_filters': "⏳ جارٍ البحث بناءً على فلاترك...",
        'no_items_found_search': "ℹ️ لم يتم العثور على منتجات تطابق فلاتر البحث.",
        'search_results': "نتائج البحث",
        'seller_label': "البائع",
        'views_label': "المشاهدات",
        'description_label': "الوصف",
        'item_link_label': "رابط المنتج",
        'error_fetching_item_details': "❌ خطأ في جلب بيانات المنتج",
        'add_to_favorites': "❤️ إضافة للمفضلة",
        'remove_from_favorites': "💔 إزالة من المفضلة",
        'back_to_market': "« العودة للسوق",
        'back_to_main_menu': "⬅️ رجوع للقائمة الرئيسية",
        'added_to_favorites_alert': "❤️ تمت الإضافة للمفضلة",
        'removed_from_favorites_alert': "💔 تمت الإزالة من المفضلة",
        'favorites_list_empty': "قائمة المفضلات فارغة حالياً.",
        'favorites_list_title': "قائمة المفضلات",
        'autobuy_rules_description': "🤖 **قواعد الشراء التلقائي:**\n\nهنا يمكنك إدارة قواعد الشراء التلقائي. سيفحص البوت السوق كل 5 دقائق ويرسل لك إشعاراً بالمنتجات المطابقة.",
        'add_new_rule': "➕ إضافة قاعدة جديدة",
        'choose_category_rule': "1️⃣ اختر القسم المطلوب لقاعدة الشراء:",
        'category_chosen_rule': "2️⃣ تم اختيار قسم: **{category_name}**.\n\nالآن، أرسل أقصى سعر للشراء.",
        'set_keywords_prompt': "3️⃣ ممتاز. الآن أرسل كلمات مفتاحية للبحث (افصل بينها بفاصلة ,) أو أرسل 'تخطي' لتجاهل الكلمات المفتاحية.",
        'skip_keyword': "تخطي",
        'rule_added_success': "✅ تم إضافة قاعدة الشراء التلقائي بنجاح!",
        'updated_rules_list': "قائمة القواعد المحدثة:",
        'rule_deleted_alert': "✅ تم حذف القاعدة بنجاح",
        'sync_purchases': "🔄 مزامنة المشتريات",
        'syncing_purchases': "🔄 **بدء مزامنة المشتريات...**",
        'sync_progress': "🔄 **جارٍ المزامنة...**\nالصفحة: `{page}` | الجديد: `{new}` | الإجمالي: `{total}`",
        'sync_complete': "✅ اكتملت المزامنة!\nتمت مزامنة وحفظ **{count}** منتج جديد.",
        'sync_no_new': "✅ المزامنة مكتملة. لا توجد مشتريات جديدة لتسجيلها.",
        'sync_stopped': "⚠️ توقفت المزامنة. لم يوفر الـ API صفحات إضافية.",
        'change_token': "🔑 تغيير التوكن",
        'token_change_warning': "لتغيير التوكن، يجب تعديل متغير `CONFIG` في بداية الكود ثم إعادة تشغيل البوت.",
        'check_connection': "🧪 فحص الاتصال",
        'checking_connection': "⏳ جارٍ فحص الاتصال بـ LZT API...",
        'connection_success': "✅ **الاتصال بـ LZT API ناجح!**\nالرصيد الحالي: `{balance}` USD",
        'connection_fail': "**فشل الاتصال**\nالخطأ: `{error}`",
        'compare_usage': "استخدام خاطئ. أرسل: `/compare ID1 ID2`",
        'compare_fetching': "⏳ جارٍ جلب بيانات المنتجين للمقارنة...",
        'compare_error': "❌ لا يمكن مقارنة نفس المنتج بنفسه.",
        'compare_fail': "❌ فشل في جلب بيانات أحد المنتجين. تأكد من صحة الـ IDs.",
        'compare_title': "📊 مقارنة بين المنتجين",
        'feature': "الميزة",
        'item_1': "المنتج الأول",
        'item_2': "المنتج الثاني",
        'title': "العنوان",
        'price': "السعر",
        'seller': "البائع",
        'views': "المشاهدات",
        'autobuy_notification_title': "🤖 إشعار شراء تلقائي!",
        'autobuy_found_item': "تم العثور على منتج يطابق قاعدتك:\n\n*القاعدة:* `{rule_name}`\n*المنتج:* `{item_title}`\n*السعر:* `${item_price}`",
        'error_notify_user': "❌ حدث خطأ غير متوقع. تم إبلاغ المطور.",
    },
}

def get_text(context, key):
    return STRINGS['ar'].get(key, key)

def main_menu(context):
    s = lambda k: get_text(context, k)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s('account_analysis'), callback_data='nav_account')],
        [InlineKeyboardButton(s('my_items_for_sale_btn'), callback_data='nav_my_items')],
        [InlineKeyboardButton(s('market_btn'), callback_data='nav_market')],
        [InlineKeyboardButton(s('autobuy_btn'), callback_data='nav_autobuy')],
        [InlineKeyboardButton(s('favorites_btn'), callback_data='fav_list_0')],
        [InlineKeyboardButton(s('settings_btn'), callback_data='nav_admin')],
    ])

def account_menu(context):
    s = lambda k: get_text(context, k)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s('balance_stats'), callback_data='acc_stats')],
        [InlineKeyboardButton(s('purchase_history'), callback_data='pur_list_0')],
        [InlineKeyboardButton(s('cashflow_chart'), callback_data='acc_cashflow_chart')],
        [InlineKeyboardButton(s('monthly_summary'), callback_data='acc_monthly_summary')],
        [InlineKeyboardButton(s('back_btn'), callback_data='nav_main')],
    ])

def my_items_menu(context):
    s = lambda k: get_text(context, k)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s('view_my_items'), callback_data='my_items_for_sale')],
        [InlineKeyboardButton(s('back_btn'), callback_data='nav_main')],
    ])

def market_menu(context):
    s = lambda k: get_text(context, k)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s('advanced_search'), callback_data='market_advanced_search')],
        [InlineKeyboardButton(s('random_item'), callback_data='market_random')],
        [InlineKeyboardButton(s('quick_analysis'), callback_data='market_quick_analysis')],
        [InlineKeyboardButton(s('back_btn'), callback_data='nav_main')],
    ])

def autobuy_menu(context, rules):
    s = lambda k: get_text(context, k)
    buttons = [[InlineKeyboardButton(s('add_new_rule'), callback_data='autobuy_add_rule')]]
    for rule in rules:
        text = f"❌ {rule['category_name']} (≤ ${rule['max_price']})"
        buttons.append([InlineKeyboardButton(text, callback_data=f'autobuy_remove_{rule["id"]}')])
    buttons.append([InlineKeyboardButton(s('back_btn'), callback_data='nav_main')])
    return InlineKeyboardMarkup(buttons)

def admin_menu(context):
    s = lambda k: get_text(context, k)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s('sync_purchases'), callback_data='admin_sync_purchases')],
        [InlineKeyboardButton(s('change_token'), callback_data='admin_reload_token')],
        [InlineKeyboardButton(s('check_connection'), callback_data='admin_check_api')],
        [InlineKeyboardButton(s('back_btn'), callback_data='nav_main')],
    ])

def item_details_keyboard(context, item_id, is_fav, origin_menu='nav_market'):
    s = lambda k: get_text(context, k)
    fav_button = InlineKeyboardButton(s('remove_from_favorites'), callback_data=f'fav_remove_{item_id}_{origin_menu}') if is_fav else InlineKeyboardButton(s('add_to_favorites'), callback_data=f'fav_add_{item_id}_{origin_menu}')
    return InlineKeyboardMarkup([[fav_button], [InlineKeyboardButton(s('back_btn'), callback_data=origin_menu)]])

def back_to_main_menu_keyboard(context):
    s = lambda k: get_text(context, k)
    return InlineKeyboardMarkup([[InlineKeyboardButton(s('back_to_main_menu'), callback_data='nav_main')]])

def dynamic_categories_keyboard(context, categories, callback_prefix: str):
    s = lambda k: get_text(context, k)
    buttons = []
    row = []
    main_categories = [cat for cat in categories if cat.get('parent_category_id') == 0]
    for cat in main_categories:
        row.append(InlineKeyboardButton(cat['title'], callback_data=f'{callback_prefix}{cat["category_id"]}'))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(s('cancel_btn'), callback_data='cancel_conversation')])
    return InlineKeyboardMarkup(buttons)

def create_pagination_keyboard(context, base_callback, current_page, total_items, per_page=5):
    """دالة لإنشاء أزرار التنقل بين الصفحات."""
    s = lambda k: get_text(context, k)
    total_pages = (total_items + per_page - 1) // per_page
    buttons = []
    row = []
    
    if current_page > 0:
        row.append(InlineKeyboardButton(s('prev_btn'), callback_data=f'{base_callback}_{current_page - 1}'))

    if total_pages > 1:
        row.append(InlineKeyboardButton(s('page').format(current=current_page + 1, total=total_pages), callback_data='ignore'))

    if current_page < total_pages - 1:
        row.append(InlineKeyboardButton(s('next_btn'), callback_data=f'{base_callback}_{current_page + 1}'))
        
    if row:
        buttons.append(row)
    return buttons


# =====================================================================================
# --- 6. وحدة المهام الخلفية (Background Tasks) ---
# =====================================================================================

async def autobuy_scanner_task(application: Application):
    """مهمة خلفية لفحص قواعد الشراء التلقائي كل 5 دقائق."""
    await asyncio.sleep(15) # انتظار أولي قبل بدء الفحص
    logging.info("بدء مهمة فحص الشراء التلقائي في الخلفية...")
    api_client = application.bot_data['api_client']
    s = lambda k: get_text(application.bot_data, k)

    while True:
        try:
            logging.info("Autobuy scanner: Running check...")
            rules = get_autobuy_rules()
            if not rules:
                await asyncio.sleep(300) # فحص كل 5 دقائق
                continue

            for rule in rules:
                last_check_ts = rule['last_checked_ts']
                
                items_data, error = await api_client.get_market_items(
                    category_id=rule['category_id'],
                    price_to=rule['max_price'],
                    title=rule.get('keywords'),
                    created_at=last_check_ts
                )
                
                if error or not items_data.get('items'):
                    continue

                for item in items_data['items']:
                    notification_text = (
                        f"*{s('autobuy_notification_title')}*\n\n"
                        f"{s('autobuy_found_item').format(rule_name=rule['category_name'], item_title=html.escape(item['title']), item_price=item['price'])}"
                    )
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔍 عرض التفاصيل", callback_data=f'view_item_{item["item_id"]}_nav_autobuy')]])
                    await application.bot.send_message(
                        chat_id=CONFIG["OWNER_ID"],
                        text=notification_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                
                update_rule_last_check(rule['id'], int(time.time()))
                await asyncio.sleep(2)
        
        except Exception as e:
            logging.error(f"Autobuy scanner: Error processing rules: {e}")
            await error_handler(None, ContextTypes.DEFAULT_TYPE(application=application, chat_data={}, user_data={}, bot_data={}, error=e))
        
        finally:
            await asyncio.sleep(300) # فحص كل 5 دقائق


# =====================================================================================
# --- 7. معالجات الأوامر والأزرار (Handlers) ---
# =====================================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = lambda k: get_text(context, k)
    await update.message.reply_text(s('welcome'), reply_markup=main_menu(context))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = lambda k: get_text(context, k)
    await update.message.reply_text(s('help_text'), parse_mode=ParseMode.MARKDOWN)

async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = lambda k: get_text(context, k)
    args = context.args
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        await update.message.reply_text(s('compare_usage')); return
    if args[0] == args[1]:
        await update.message.reply_text(s('compare_error')); return
        
    msg = await update.message.reply_text(s('compare_fetching'))
    api = context.bot_data['api_client']
    item1_data, err1 = await api.get_item_details(int(args[0]))
    item2_data, err2 = await api.get_item_details(int(args[1]))

    if err1 or err2 or not item1_data.get('item') or not item2_data.get('item'):
        await msg.edit_text(s('compare_fail')); return

    item1, item2 = item1_data['item'], item2_data['item']
    def f(title): return (title[:25] + '...') if len(title) > 25 else title

    text = (f"<b>{s('compare_title')}</b>\n\n<pre>"
            f"{s('feature'):<10} | {s('item_1'):<12} | {s('item_2'):<12}\n"
            f"-----------------------------------------\n"
            f"{s('title'):<10} | {f(item1['title']):<12} | {f(item2['title']):<12}\n"
            f"{s('price'):<10} | ${item1['price']:<11.2f} | ${item2['price']:<11.2f}\n"
            f"{s('seller'):<10} | {item1['seller']['username']:<12} | {item2['seller']['username']:<12}\n"
            f"{s('views'):<10} | {item1['stats']['views']:<12} | {item2['stats']['views']:<12}\n</pre>")

    await msg.edit_text(text, parse_mode=ParseMode.HTML)

async def navigation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج مركزي لمعظم الأزرار في البوت."""
    query = update.callback_query
    await query.answer()
    action = query.data
    s = lambda k: get_text(context, k)

    nav_map = {
        'nav_main': (s('welcome'), main_menu(context)),
        'nav_account': (s('account_analysis'), account_menu(context)),
        'nav_my_items': (s('my_items_for_sale_btn'), my_items_menu(context)),
        'nav_market': (s('market_btn'), market_menu(context)),
        'nav_admin': (s('settings_btn'), admin_menu(context)),
    }

    if action in nav_map:
        text, keyboard = nav_map[action]
        await edit_or_send_message(query, text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    elif action == 'nav_autobuy': await autobuy_start(update, context)
    elif action.startswith('pur_list_'): await purchases_history(update, context)
    elif action.startswith('fav_list_'): await list_favorites(update, context)
    elif action == 'acc_stats': await account_stats(update, context)
    elif action == 'acc_cashflow_chart': await get_cashflow_chart(update, context)
    elif action == 'acc_monthly_summary': await get_monthly_summary(update, context)
    elif action == 'my_items_for_sale': await my_items_for_sale(update, context)
    elif action == 'market_random': await market_random_item(update, context)
    elif action == 'market_quick_analysis': await market_quick_analysis(update, context)
    elif action == 'admin_sync_purchases': await sync_purchases(update, context)
    elif action == 'admin_check_api': await check_api_connection(update, context)
    elif action == 'admin_reload_token': await reload_token(update, context)
    elif action.startswith('view_item_'): await view_item_details(update, context)
    elif action.startswith('fav_add_'): await add_favorite_handler(update, context)
    elif action.startswith('fav_remove_'): await remove_favorite_handler(update, context)
    elif action.startswith('autobuy_remove_'): await remove_autobuy_rule_handler(update, context)

async def edit_or_send_message(query: Update.callback_query, text: str, **kwargs):
    """[تحسين V2.8] تعديل الرسالة الحالية أو حذفها وإرسال واحدة جديدة إذا كانت لا تحتوي على نص (مثل الصور)."""
    try:
        # إذا كانت الرسالة تحتوي على نص، نقوم بتعديلها مباشرة
        if query.message.text:
            await query.edit_message_text(text, **kwargs)
        else:
            # إذا كانت الرسالة لا تحتوي على نص (صورة مثلاً)، نحذفها ونرسل رسالة جديدة
            await query.message.delete()
            await query.message.chat.send_message(text, **kwargs)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass # نتجاهل هذا الخطأ الشائع
        elif "message to edit not found" in str(e):
             await query.message.chat.send_message(text, **kwargs)
        else:
            raise # نرفع أي خطأ آخر

async def format_item_message(context, item, is_detailed=False):
    s = lambda k: get_text(context, k)
    link = item.get('item_url', f"https://zelenka.guru/market/{item.get('item_id', '')}")
    
    message = f"*{html.escape(item.get('title', 'N/A'))}*\n\n"
    message += f"💰 *{s('price')}:* `{item.get('price', 0)}` USD\n"
    if 'seller' in item:
        message += f"👤 *{s('seller_label')}:* `{item['seller'].get('username', 'N/A')}`\n"
    if 'stats' in item:
        message += f"👁️ *{s('views_label')}:* `{item['stats'].get('views', 0)}`\n"
    
    if is_detailed:
        description = item.get('item_description_parsed', {}).get('text', '')[:250]
        message += f"\n📝 *{s('description_label')}:*\n`{html.escape(description)}...`\n"

    message += f"\n🔗 [{s('item_link_label')}]({link})"
    return message

async def view_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    s = lambda k: get_text(context, k)
    parts = query.data.split('_')
    item_id = int(parts[2])
    origin_menu = "_".join(parts[3:]) if len(parts) > 3 else 'nav_market'

    await edit_or_send_message(query, s('loading'))
    api = context.bot_data['api_client']
    data, error = await api.get_item_details(item_id)

    if error or not data.get('item'):
        await edit_or_send_message(query, s('error_fetching_item_details'), reply_markup=back_to_main_menu_keyboard(context))
        return

    item = data['item']
    message = await format_item_message(context, item, is_detailed=True)
    keyboard = item_details_keyboard(context, item_id, is_favorite(item_id), origin_menu)
    
    await edit_or_send_message(query, message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard, disable_web_page_preview=True)

# --- معالجات قسم الحساب والتحليلات ---
async def account_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await edit_or_send_message(query, s('loading'))
    
    api = context.bot_data['api_client']
    data, error = await api.get_user_profile()
    if error or not data.get('user'):
        await edit_or_send_message(query, f"❌ {s('error')}: {error}", reply_markup=account_menu(context)); return
        
    user = data.get('user', {})
    counts = user.get('counts', {}) # جلب قاموس الإحصائيات
    
    reg_date = datetime.fromtimestamp(user.get('register_date', 0)).strftime('%Y-%m-%d')
    
    # [إصلاح V2.9] استخدام المفاتيح الصحيحة والجديدة من API
    balance_val = user.get('balance', 0)
    purchases_val = counts.get('market_purchases', 0)
    feedback_pos = user.get('feedback_positive', 0)
    feedback_neg = user.get('feedback_negative', 0)

    # [تحسين V2.9] إضافة نظام تحقق لتسجيل الأخطاء إذا كانت كل القيم صفراً
    if all(v == 0 for v in [balance_val, purchases_val, feedback_pos, feedback_neg]):
        logging.warning(f"All stats are zero. API response for user might have changed keys. Full user object: {user}")

    message = (f"👤 *{s('lzt_profile')}*\n\n"
               f"🏷️ *{s('username')}:* `{user.get('username', 'N/A')}`\n"
               f"💰 *{s('balance')}:* `{balance_val}` {user.get('currency_code', 'USD')}\n"
               f"📦 *{s('total_purchases')}:* `{purchases_val}`\n"
               f"📈 *{s('positive_feedback')}:* `{feedback_pos}`\n"
               f"📉 *{s('negative_feedback')}:* `{feedback_neg}`\n"
               f"📅 *{s('registration_date')}:* `{reg_date}`")
    await edit_or_send_message(query, message, parse_mode=ParseMode.MARKDOWN, reply_markup=account_menu(context))

async def my_items_for_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await edit_or_send_message(query, s('loading_my_items'))
    
    api = context.bot_data['api_client']
    user_data, user_error = await api.get_user_profile()
    if user_error or not user_data.get('user'):
        await edit_or_send_message(query, f"❌ {s('error_profile')}: {user_error}", reply_markup=my_items_menu(context)); return
    
    user_id = user_data['user']['user_id']
    items_data, items_error = await api.get_my_items_for_sale(user_id)
    
    if items_error:
        await edit_or_send_message(query, f"❌ {s('error')}: {items_error}", reply_markup=my_items_menu(context))
    elif not items_data.get('items'):
        await edit_or_send_message(query, s('no_items_for_sale'), reply_markup=my_items_menu(context))
    else:
        message = f"🏷️ *{s('your_items_for_sale')}:*\n\n"
        for item in items_data['items']:
            link = item.get('item_url', '#')
            message += f"🔹 [{html.escape(item.get('title', 'N/A'))}]({link}) - `{item.get('price', '?')}`$\n"
        await edit_or_send_message(query, message, parse_mode=ParseMode.MARKDOWN, reply_markup=my_items_menu(context), disable_web_page_preview=True)

async def purchases_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المشتريات مع دعم الصفحات."""
    query = update.callback_query; s = lambda k: get_text(context, k)
    page = int(query.data.split('_')[-1])
    per_page = 5
    offset = page * per_page
    
    purchases = get_purchases(limit=per_page, offset=offset)
    total_purchases = get_purchases_count()
    
    if total_purchases == 0:
        await edit_or_send_message(query, s('no_purchases_synced'), reply_markup=account_menu(context)); return

    message = f"📜 *{s('last_purchases')}:*\n\n"
    for p in purchases:
        p_date = datetime.fromtimestamp(p['purchase_date']).strftime('%Y-%m-%d')
        message += f"- `{html.escape(p['title'])}`\n  ({s('price_label')} *{p['price']}$* | {s('date_label')} *{p_date}*)\n"
    
    buttons = create_pagination_keyboard(context, 'pur_list', page, total_purchases, per_page)
    buttons.append([InlineKeyboardButton(s('back_btn'), callback_data='nav_account')])
    
    await edit_or_send_message(query, message, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))


async def get_cashflow_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await edit_or_send_message(query, s('generating_chart'))
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    purchases = get_purchases_for_period(start_date.timestamp(), end_date.timestamp())
    
    if not purchases:
        await edit_or_send_message(query, s('no_data_for_chart'), reply_markup=account_menu(context)); return

    df = pd.DataFrame(purchases, columns=['date', 'price'])
    df['date'] = pd.to_datetime(df['date'], unit='s').dt.date
    daily_spending = df.groupby('date')['price'].sum().reindex(pd.date_range(start=start_date.date(), end=end_date.date(), freq='D'), fill_value=0)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(daily_spending.index, daily_spending.values, marker='o', linestyle='-', color='#00aaff')
    ax.set_title(s('cashflow_chart_title'), fontsize=16, color='white', pad=20)
    ax.set_xlabel(s('date_label_chart'), color='white'); ax.set_ylabel(s('spending_usd'), color='white')
    ax.grid(True, linestyle='--', alpha=0.3); fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); buf.seek(0); plt.close(fig)
    
    await query.message.delete()
    await context.bot.send_photo(chat_id=query.from_user.id, photo=buf, caption=s('cashflow_chart_caption'), reply_markup=account_menu(context))

async def get_monthly_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    purchases = get_purchases_for_period(start_of_month.timestamp(), now.timestamp())
    if not purchases:
        await edit_or_send_message(query, s('no_data_for_summary'), reply_markup=account_menu(context)); return
    message = (f"🧾 *{s('monthly_summary_title')} ({now.strftime('%B %Y')})*\n\n"
               f"💸 *{s('total_spent')}:* `{sum(p['price'] for p in purchases):.2f}` USD\n"
               f"🔢 *{s('number_of_deals')}:* `{len(purchases)}`\n"
               f"🔝 *{s('highest_deal')}:* `{max(p['price'] for p in purchases):.2f}` USD")
    await edit_or_send_message(query, message, parse_mode=ParseMode.MARKDOWN, reply_markup=account_menu(context))

# --- معالجات قسم السوق ---
async def market_random_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await edit_or_send_message(query, s('choosing_random_item'))
    api = context.bot_data['api_client']
    
    items_data, error = await api.get_market_items()
    if error or not items_data.get('items'):
        await edit_or_send_message(query, s('cant_fetch_items'), reply_markup=market_menu(context)); return

    item = items_data['items'][0] 
    message = await format_item_message(context, item, is_detailed=False)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔍 عرض التفاصيل", callback_data=f'view_item_{item["item_id"]}_nav_market')],
                                     [InlineKeyboardButton(s('back_to_market'), callback_data='nav_market')]])
    await edit_or_send_message(query, message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard, disable_web_page_preview=True)

async def market_quick_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await edit_or_send_message(query, s('analyzing_market'))
    api = context.bot_data['api_client']

    items_data, error = await api.get_market_items()
    if error or not items_data.get('items'):
        await edit_or_send_message(query, s('cant_fetch_items_for_analysis'), reply_markup=market_menu(context)); return

    items = items_data['items']
    cheapest = min(items, key=lambda x: x['price'])
    most_viewed = max(items, key=lambda x: x['stats']['views'])

    message = (f"📊 *{s('quick_analysis_title')}*\n\n"
               f"📉 *{s('cheapest_item')}:*\n`{html.escape(cheapest['title'])}`\n({s('price_label')} *{cheapest['price']}$*)\n\n"
               f"👁️ *{s('most_viewed_item')}:*\n`{html.escape(most_viewed['title'])}`\n({s('with_views')} *{most_viewed['stats']['views']}*)")
    await edit_or_send_message(query, message, parse_mode=ParseMode.MARKDOWN, reply_markup=market_menu(context))

# --- معالجات المفضلة ---
async def list_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المفضلة مع دعم الصفحات."""
    query = update.callback_query; s = lambda k: get_text(context, k)
    page = int(query.data.split('_')[-1])
    per_page = 5
    offset = page * per_page
    
    favorites = get_favorites(limit=per_page, offset=offset)
    total_favorites = get_favorites_count()

    if total_favorites == 0:
        await edit_or_send_message(query, s('favorites_list_empty'), reply_markup=back_to_main_menu_keyboard(context)); return
    
    message = f"❤️ *{s('favorites_list_title')}*\n\n"
    buttons = []
    for fav in favorites:
        button_text = f"{fav['title']} (${fav['price']})"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"view_item_{fav['item_id']}_fav_list_{page}")])

    pagination_buttons = create_pagination_keyboard(context, 'fav_list', page, total_favorites, per_page)
    buttons.extend(pagination_buttons)
    buttons.append([InlineKeyboardButton(s('back_btn'), callback_data='nav_main')])
    
    await edit_or_send_message(query, message, reply_markup=InlineKeyboardMarkup(buttons))


async def add_favorite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    parts = query.data.split('_')
    item_id = int(parts[2])
    origin_menu = "_".join(parts[3:])

    api = context.bot_data['api_client']
    item_data, error = await api.get_item_details(item_id)
    if error or not item_data.get('item'):
        await query.answer(s('error_fetching_item_details'), show_alert=True); return
        
    item = item_data['item']
    add_favorite(item_id, item['title'], item['price'])
    await query.answer(s('added_to_favorites_alert'))
    
    keyboard = item_details_keyboard(context, item_id, is_favorite(item_id), origin_menu)
    await query.edit_message_reply_markup(keyboard)


async def remove_favorite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    parts = query.data.split('_')
    item_id = int(parts[2])
    origin_menu = "_".join(parts[3:])
    
    remove_favorite(item_id)
    await query.answer(s('removed_from_favorites_alert'))
    
    keyboard = item_details_keyboard(context, item_id, is_favorite(item_id), origin_menu)
    await query.edit_message_reply_markup(keyboard)

# --- معالجات الشراء التلقائي ---
async def autobuy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    rules = get_autobuy_rules()
    await edit_or_send_message(query,
        s('autobuy_rules_description'),
        reply_markup=autobuy_menu(context, rules),
        parse_mode=ParseMode.MARKDOWN
    )

async def remove_autobuy_rule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    rule_id = int(query.data.split('_')[-1])
    remove_autobuy_rule(rule_id)
    await query.answer(s('rule_deleted_alert'), show_alert=True)
    
    rules = get_autobuy_rules()
    await edit_or_send_message(query,
        s('updated_rules_list'),
        reply_markup=autobuy_menu(context, rules),
        parse_mode=ParseMode.MARKDOWN
    )

# --- معالجات الإعدادات ---
async def sync_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await edit_or_send_message(query, s('syncing_purchases'))
    
    api = context.bot_data['api_client']
    total_new_items = 0
    page = 1
    stopped_by_api = False
    
    while True:
        progress_message = s('sync_progress').format(page=page, new=0, total=total_new_items)
        await edit_or_send_message(query, progress_message)

        purchases_data, error = await api.get_my_purchases(page=page)
        if error or not purchases_data.get('items'):
            stopped_by_api = True
            break

        existing_ids = {p['item_id'] for p in get_purchases(limit=10000)}
        
        new_items = [item for item in purchases_data['items'] if item['item_id'] not in existing_ids]
        
        current_page_new = len(new_items)
        if current_page_new > 0:
            add_purchase_batch(new_items)
            total_new_items += current_page_new

        progress_message = s('sync_progress').format(page=page, new=current_page_new, total=total_new_items)
        await edit_or_send_message(query, progress_message)

        if not purchases_data.get('links', {}).get('next'):
            stopped_by_api = True
            break
        
        page += 1
        await asyncio.sleep(1.5)

    if total_new_items > 0:
        message = s('sync_complete').format(count=total_new_items)
    elif stopped_by_api and page > 1:
        message = s('sync_stopped')
    else:
        message = s('sync_no_new')
        
    await edit_or_send_message(query, message, reply_markup=admin_menu(context))

async def check_api_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await edit_or_send_message(query, s('checking_connection'))
    
    api = context.bot_data['api_client']
    profile, error = await api.get_user_profile()
    
    if error or not profile.get('user'):
        message = s('connection_fail').format(error=error)
    else:
        balance = profile.get('user', {}).get('balance', 0)
        message = s('connection_success').format(balance=balance)
        
    await edit_or_send_message(query, message, reply_markup=admin_menu(context))

async def reload_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await query.answer(s('token_change_warning'), show_alert=True)

# --- محادثات متعددة الخطوات (Conversations) ---
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; s = lambda k: get_text(context, k)
    message_text = s('operation_cancelled')
    
    if query:
        await edit_or_send_message(query, message_text)
        await query.message.chat.send_message(s('welcome'), reply_markup=main_menu(context))
    else:
        await update.message.reply_text(message_text)
        await update.message.reply_text(s('welcome'), reply_markup=main_menu(context))
        
    context.user_data.clear()
    return ConversationHandler.END

# 1. محادثة البحث المتقدم
async def advanced_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await query.answer()
    
    api = context.bot_data['api_client']
    categories, error = await api.get_market_categories()
    if error or not categories:
        await edit_or_send_message(query, s('failed_to_fetch_categories'), reply_markup=market_menu(context))
        return ConversationHandler.END
        
    context.user_data['categories_cache'] = {c['category_id']: c['title'] for c in categories}
    keyboard = dynamic_categories_keyboard(context, categories, callback_prefix='search_cat_')
    await edit_or_send_message(query, s('choose_category_search'), reply_markup=keyboard)
    return SELECT_CATEGORY

async def search_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await query.answer()
    
    category_id = int(query.data.replace('search_cat_', ''))
    category_name = context.user_data['categories_cache'].get(category_id, 'Unknown')
    context.user_data['search_filters'] = {'category_id': category_id}
    
    await edit_or_send_message(query,
        s('category_chosen').format(category_name=category_name),
        parse_mode=ParseMode.MARKDOWN
    )
    return SET_MAX_PRICE

async def search_set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = lambda k: get_text(context, k)
    price_text = update.message.text
    if not price_text.replace('.', '', 1).isdigit():
        await update.message.reply_text(s('price_must_be_number'))
        return SET_MAX_PRICE

    price = float(price_text)
    if price > 0:
        context.user_data['search_filters']['price_to'] = price
    
    await update.message.reply_text(s('searching_with_filters'))
    
    api = context.bot_data['api_client']
    filters = context.user_data['search_filters']
    items_data, error = await api.get_market_items(**filters)

    if error or not items_data.get('items'):
        await update.message.reply_text(s('no_items_found_search'), reply_markup=market_menu(context))
    else:
        await update.message.reply_text(f"🔎 *{s('search_results')}*", parse_mode=ParseMode.MARKDOWN)
        for item in items_data['items'][:5]: # عرض أول 5 نتائج فقط
            message = await format_item_message(context, item)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔍 عرض التفاصيل", callback_data=f'view_item_{item["item_id"]}_nav_market')]])
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard, disable_web_page_preview=True)
    
    context.user_data.clear()
    return ConversationHandler.END


# 2. محادثة إضافة قاعدة شراء تلقائي
async def autobuy_add_rule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await query.answer()

    api = context.bot_data['api_client']
    categories, error = await api.get_market_categories()
    if error or not categories:
        await edit_or_send_message(query, s('failed_to_fetch_categories'), reply_markup=autobuy_menu(context, get_autobuy_rules()))
        return ConversationHandler.END

    context.user_data['categories_cache'] = {c['category_id']: c['title'] for c in categories}
    keyboard = dynamic_categories_keyboard(context, categories, callback_prefix='rule_cat_')
    await edit_or_send_message(query, s('choose_category_rule'), reply_markup=keyboard)
    return ADD_RULE_CAT


async def rule_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; s = lambda k: get_text(context, k)
    await query.answer()

    category_id = int(query.data.replace('rule_cat_', ''))
    category_name = context.user_data['categories_cache'].get(category_id, 'Unknown')
    context.user_data['new_rule'] = {'category_id': category_id, 'category_name': category_name}
    
    await edit_or_send_message(query,
        s('category_chosen_rule').format(category_name=category_name),
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_RULE_PRICE

async def rule_set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = lambda k: get_text(context, k)
    price_text = update.message.text
    if not price_text.replace('.', '', 1).isdigit() or float(price_text) <= 0:
        await update.message.reply_text(s('price_must_be_number'))
        return ADD_RULE_PRICE

    context.user_data['new_rule']['max_price'] = float(price_text)
    await update.message.reply_text(s('set_keywords_prompt'), parse_mode=ParseMode.MARKDOWN)
    return ADD_RULE_KEYWORDS

async def rule_set_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = lambda k: get_text(context, k)
    keywords = update.message.text
    if keywords.lower() not in ['تخطي', 'skip']:
        context.user_data['new_rule']['keywords'] = keywords
    
    rule = context.user_data['new_rule']
    add_autobuy_rule(
        category_id=rule['category_id'],
        category_name=rule['category_name'],
        max_price=rule['max_price'],
        keywords=rule.get('keywords')
    )
    
    await update.message.reply_text(s('rule_added_success'))
    rules = get_autobuy_rules()
    await update.message.reply_text(
        s('updated_rules_list'),
        reply_markup=autobuy_menu(context, rules),
        parse_mode=ParseMode.MARKDOWN
    )
    
    context.user_data.clear()
    return ConversationHandler.END


# --- معالج الأخطاء و التدقيق ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء الذي يبلغ المستخدم والمالك."""
    s = lambda k: get_text(context, k) if context else STRINGS['ar'].get(k,k)
    logging.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(context.error, BadRequest) and "Message is not modified" in str(context.error):
        return # نتجاهل هذا الخطأ الشائع
        
    error_message_for_user = s('error_notify_user')
    try:
        if update and isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message_for_user
            )
    except Exception as e:
        logging.error(f"Failed to send error message to user: {e}")

    # إرسال تفاصيل الخطأ الكاملة للمالك
    owner_id = CONFIG.get('OWNER_ID')
    if owner_id and context and context.error:
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)
        error_message = (
            f"🔔 **خطأ في البوت** 🔔\n\n"
            f"حدث استثناء:\n"
            f"`{html.escape(str(context.error))}`\n\n"
            f"**Traceback:**\n"
            f"<pre>{html.escape(tb_string[:3500])}</pre>"
        )
        try:
            bot = context.bot if context.bot else Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build().bot
            await bot.send_message(
                chat_id=owner_id,
                text=error_message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
             logging.error(f"CRITICAL: Failed to send detailed error report to OWNER: {e}")


# =====================================================================================
# --- 8. نقطة الدخول الرئيسية للتطبيق (Main Execution) ---
# =====================================================================================

def main() -> None:
    """الدالة الرئيسية التي تهيئ وتشغل البوت."""
    initialize_database()
    
    application = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()
    application.bot_data['api_client'] = LZT_API_Client(CONFIG["LZT_API_TOKEN"])
    application.bot_data['owner_id'] = CONFIG["OWNER_ID"]

    search_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(advanced_search_start, pattern='^market_advanced_search$')],
        states={
            SELECT_CATEGORY: [CallbackQueryHandler(search_category_selected, pattern='^search_cat_')],
            SET_MAX_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_set_price)],
        },
        fallbacks=[CallbackQueryHandler(cancel_conversation, pattern='^cancel_conversation$'), CommandHandler('start', cancel_conversation)],
        per_message=False
    )

    autobuy_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(autobuy_add_rule_start, pattern='^autobuy_add_rule$')],
        states={
            ADD_RULE_CAT: [CallbackQueryHandler(rule_category_selected, pattern='^rule_cat_')],
            ADD_RULE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, rule_set_price)],
            ADD_RULE_KEYWORDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, rule_set_keywords)],
        },
        fallbacks=[CallbackQueryHandler(cancel_conversation, pattern='^cancel_conversation$'), CommandHandler('start', cancel_conversation)],
        per_message=False
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("compare", compare_command))
    application.add_handler(search_conv)
    application.add_handler(autobuy_conv)
    application.add_handler(CallbackQueryHandler(navigation_handler))
    application.add_error_handler(error_handler)
    
    async def post_init(app: Application):
        """دالة تعمل بعد تهيئة البوت وقبل بدء التشغيل الكامل."""
        logging.info("البوت الاحترافي المطور (V2.9) قيد التشغيل...")
        app.create_task(autobuy_scanner_task(app))
        
        try:
            await app.bot.send_message(chat_id=CONFIG["OWNER_ID"], text="✅ البوت (V2.9) بدأ التشغيل بنجاح!")
        except Exception as e:
            logging.warning(f"لم أتمكن من إرسال رسالة بدء التشغيل للمالك: {e}")

    application.post_init = post_init
    application.run_polling()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"حدث خطأ قاتل منع تشغيل البوت: {e}")
        traceback.print_exc()


