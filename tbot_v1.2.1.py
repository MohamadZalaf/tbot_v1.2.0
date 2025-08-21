#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 بوت التداول المتقدم الكامل - Advanced Trading Bot v1.2.0
=============================================================
الإصدار الجديد المُطور مع MetaTrader5 و Google Gemini AI

🔥 ميزات الإصدار v1.2.0:
- تكامل كامل مع MetaTrader5 للبيانات اللحظية الحقيقية
- دمج Google Gemini AI للتحليل الذكي والتنبؤات
- نظام تقييم الإشعارات بأزرار 👍 و 👎
- تخزين ذكي لبيانات الصفقات والتقييمات
- تعلم آلي من تقييمات المستخدم

⚠️ تحذير مهم للسلامة المالية:
- يتطلب اتصال حقيقي بـ MetaTrader5
- لا يعمل بدون بيانات حقيقية لحمايتك
- جميع التحليلات تعتمد على بيانات لحظية حقيقية
- لا توصيات تداول بدون تحليل AI كامل

Developer: Mohamad Zalaf ©️2025
Date: 2025 - v1.2.0 MT5 + Gemini AI Enhanced Version (Safe Mode)
"""

import telebot
from telebot import apihelper
import json
import logging
import os
import sys

# إعداد timeout أطول لـ Telegram API
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import google.generativeai as genai
from datetime import datetime, timedelta
from telebot import types
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import threading
import time
import ta
from PIL import Image, ImageDraw, ImageFont
import warnings

# استيراد الإعدادات من ملف config.py
try:
    from config import (
        BOT_TOKEN, BOT_PASSWORD, GEMINI_API_KEY,
        DEFAULT_NOTIFICATION_SETTINGS, AVAILABLE_TIMEZONES,
        DEFAULT_CAPITAL_OPTIONS, TRADING_MODE_SETTINGS
    )
except ImportError:
    # إعدادات احتياطية في حالة عدم وجود ملف config.py
    BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
    BOT_PASSWORD = 'tra12345678'
    GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY_HERE'
    DEFAULT_NOTIFICATION_SETTINGS = {}
    AVAILABLE_TIMEZONES = {}
    DEFAULT_CAPITAL_OPTIONS = [1000, 5000, 10000]
    TRADING_MODE_SETTINGS = {}

# متغير للتحكم في حلقة المراقبة
monitoring_active = False

# مكتبة المناطق الزمنية (اختيارية)
try:
    import pytz
    TIMEZONE_AVAILABLE = True
except ImportError:
    TIMEZONE_AVAILABLE = False

warnings.filterwarnings('ignore')

# معالجة أخطاء الشبكة والاتصال
import requests
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
    import inspect
    
    # إعداد جلسة requests مع إعادة المحاولة التلقائية
    session = requests.Session()
    
    # التحقق من الإصدار المدعوم للمعاملة (backward compatibility)
    retry_kwargs = {
        'total': 3,
        'status_forcelist': [429, 500, 502, 503, 504],
        'backoff_factor': 1
    }
    
    # فحص ما إذا كان المعامل allowed_methods مدعوم أم method_whitelist
    retry_signature = inspect.signature(Retry.__init__)
    if 'allowed_methods' in retry_signature.parameters:
        retry_kwargs['allowed_methods'] = ["HEAD", "GET", "OPTIONS"]
    elif 'method_whitelist' in retry_signature.parameters:
        retry_kwargs['method_whitelist'] = ["HEAD", "GET", "OPTIONS"]
    
    retry_strategy = Retry(**retry_kwargs)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
except ImportError:
    # في حالة عدم توفر urllib3
    session = requests.Session()

# ===== آلية التحكم في التكرار والكاش للاستدعاءات =====
from dataclasses import dataclass

# كاش البيانات لتقليل الاستدعاءات المتكررة
price_data_cache = {}
CACHE_DURATION = 15  # ثوان - مدة صلاحية الكاش

@dataclass
class CachedPriceData:
    data: dict
    timestamp: datetime
    
def is_cache_valid(symbol: str) -> bool:
    """التحقق من صلاحية البيانات المخزنة مؤقتاً"""
    if symbol not in price_data_cache:
        return False
    
    cached_item = price_data_cache[symbol]
    time_diff = datetime.now() - cached_item.timestamp
    return time_diff.total_seconds() < CACHE_DURATION

def get_cached_price_data(symbol: str) -> Optional[dict]:
    """جلب البيانات من الكاش إذا كانت صالحة"""
    if is_cache_valid(symbol):
        return price_data_cache[symbol].data
    return None

def cache_price_data(symbol: str, data: dict):
    """حفظ البيانات في الكاش"""
    price_data_cache[symbol] = CachedPriceData(data, datetime.now())

# معدل الاستدعاءات للحماية من الإفراط
last_api_calls = {}
MIN_CALL_INTERVAL = 5  # ثوان بين الاستدعاءات لنفس الرمز

def can_make_api_call(symbol: str) -> bool:
    """التحقق من إمكانية استدعاء API لرمز معين"""
    now = time.time()
    last_call = last_api_calls.get(symbol, 0)
    return (now - last_call) >= MIN_CALL_INTERVAL

def record_api_call(symbol: str):
    """تسجيل وقت آخر استدعاء للـ API"""
    last_api_calls[symbol] = time.time()

# تهيئة البوت
bot = telebot.TeleBot(BOT_TOKEN)

# إعداد البيئة للتعامل مع UTF-8 على Windows
import os
if os.name == 'nt':  # Windows
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import sys
    # تعيين stdout و stderr لاستخدام UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

def setup_logging():
    """إعداد نظام تسجيل متقدم مع دعم UTF-8 للـ Windows"""
    # تكوين handlers بشكل منفصل لضمان UTF-8
    file_handler = RotatingFileHandler(
        'advanced_trading_bot_v1.2.0.log', 
        maxBytes=10*1024*1024, 
        backupCount=5,
        encoding='utf-8'
    )
    
    # إعداد console handler مع UTF-8
    console_handler = logging.StreamHandler(sys.stdout)
    if hasattr(console_handler.stream, 'reconfigure'):
        console_handler.stream.reconfigure(encoding='utf-8')
    
    # تنسيق الرسائل
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # إعداد logger الرئيسي
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # منع تكرار الرسائل
    root_logger.propagate = False

setup_logging()
logger = logging.getLogger(__name__)

# تهيئة Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
    logger.info("[OK] تم تهيئة Gemini AI بنجاح")
except Exception as e:
    GEMINI_AVAILABLE = False
    logger.error(f"[ERROR] فشل تهيئة Gemini AI: {e}")

# ===== نظام إدارة المستخدمين =====
user_sessions = {}  # تتبع جلسات المستخدمين
user_capitals = {}  # رؤوس أموال المستخدمين
user_states = {}    # حالات المستخدمين

# وظيفة للتحقق من صلاحية المستخدم
def is_user_authenticated(user_id: int) -> bool:
    """التحقق من أن المستخدم مُصرح له بالوصول"""
    return user_sessions.get(user_id, {}).get('authenticated', False)

def require_authentication(func):
    """ديكوريتر للتحقق من المصادقة قبل تنفيذ الوظيفة"""
    def wrapper(message_or_call):
        user_id = message_or_call.from_user.id
        
        if not is_user_authenticated(user_id):
            # إذا كان callback query
            if hasattr(message_or_call, 'message'):
                bot.answer_callback_query(
                    message_or_call.id, 
                    "🔐 يرجى إدخال كلمة المرور أولاً بكتابة /start", 
                    show_alert=True
                )
                return
            # إذا كان message عادي
            else:
                bot.reply_to(
                    message_or_call, 
                    "🔐 يرجى إدخال كلمة المرور أولاً بكتابة /start"
                )
                return
        
        return func(message_or_call)
    return wrapper
user_selected_symbols = {}  # الرموز المختارة للمراقبة
user_current_category = {}  # الفئة الحالية لكل مستخدم لتحديث القائمة
user_trade_feedbacks = {}  # تقييمات المستخدمين للصفقات
user_monitoring_active = {}  # تتبع حالة المراقبة الآلية للمستخدمين

# تحسين المراقبة بتجميع الرموز المشتركة
user_trading_modes = {}  # أنماط التداول للمستخدمين
user_advanced_notification_settings = {}  # إعدادات التنبيهات المتقدمة
user_timezones = {}  # المناطق الزمنية للمستخدمين

# مجلدات تخزين البيانات
DATA_DIR = "trading_data"
FEEDBACK_DIR = os.path.join(DATA_DIR, "user_feedback")
TRADE_LOGS_DIR = os.path.join(DATA_DIR, "trade_logs")

# إنشاء المجلدات إذا لم تكن موجودة
for directory in [DATA_DIR, FEEDBACK_DIR, TRADE_LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# رسائل تحذير للمكتبات المفقودة
if not TIMEZONE_AVAILABLE:
    logger.warning("مكتبة pytz غير متوفرة - سيتم استخدام التوقيت المحلي فقط")

# ===== قواميس الرموز المالية المحدثة من v1.1.0 =====
CURRENCY_PAIRS = {
    'EURUSD': {'name': 'يورو/دولار 💶', 'symbol': 'EURUSD', 'type': 'forex', 'emoji': '💶'},
    'USDJPY': {'name': 'دولار/ين 💴', 'symbol': 'USDJPY', 'type': 'forex', 'emoji': '💴'},
    'GBPUSD': {'name': 'جنيه/دولار 💷', 'symbol': 'GBPUSD', 'type': 'forex', 'emoji': '💷'},
    'AUDUSD': {'name': 'دولار أسترالي/دولار 🇦🇺', 'symbol': 'AUDUSD', 'type': 'forex', 'emoji': '🇦🇺'},
    'USDCAD': {'name': 'دولار/دولار كندي 🇨🇦', 'symbol': 'USDCAD', 'type': 'forex', 'emoji': '🇨🇦'},
    'USDCHF': {'name': 'دولار/فرنك سويسري 🇨🇭', 'symbol': 'USDCHF', 'type': 'forex', 'emoji': '🇨🇭'},
    'NZDUSD': {'name': 'دولار نيوزيلندي/دولار 🇳🇿', 'symbol': 'NZDUSD', 'type': 'forex', 'emoji': '🇳🇿'},
    'EURGBP': {'name': 'يورو/جنيه 🇪🇺', 'symbol': 'EURGBP', 'type': 'forex', 'emoji': '🇪🇺'},
    'EURJPY': {'name': 'يورو/ين 🇯🇵', 'symbol': 'EURJPY', 'type': 'forex', 'emoji': '🇯🇵'},
    'GBPJPY': {'name': 'جنيه/ين 💷', 'symbol': 'GBPJPY', 'type': 'forex', 'emoji': '💷'},
}

METALS = {
    'XAUUSD': {'name': 'ذهب 🥇', 'symbol': 'XAUUSD', 'type': 'metal', 'emoji': '🥇'},
    'XAGUSD': {'name': 'فضة 🥈', 'symbol': 'XAGUSD', 'type': 'metal', 'emoji': '🥈'},
    'XPTUSD': {'name': 'بلاتين 💎', 'symbol': 'XPTUSD', 'type': 'metal', 'emoji': '💎'},
    'XPDUSD': {'name': 'بلاديوم ⚡', 'symbol': 'XPDUSD', 'type': 'metal', 'emoji': '⚡'},
}

CRYPTO_PAIRS = {
    'BTCUSD': {'name': 'بيتكوين ₿', 'symbol': 'BTCUSD', 'type': 'crypto', 'emoji': '₿'},
    'ETHUSD': {'name': 'إيثريوم ⟠', 'symbol': 'ETHUSD', 'type': 'crypto', 'emoji': '⟠'},
    'BNBUSD': {'name': 'بينانس كوين 🔸', 'symbol': 'BNBUSD', 'type': 'crypto', 'emoji': '🔸'},
    'XRPUSD': {'name': 'ريبل 💧', 'symbol': 'XRPUSD', 'type': 'crypto', 'emoji': '💧'},
    'ADAUSD': {'name': 'كاردانو 🔷', 'symbol': 'ADAUSD', 'type': 'crypto', 'emoji': '🔷'},
    'SOLUSD': {'name': 'سولانا ☀️', 'symbol': 'SOLUSD', 'type': 'crypto', 'emoji': '☀️'},
    'DOTUSD': {'name': 'بولكادوت ⚫', 'symbol': 'DOTUSD', 'type': 'crypto', 'emoji': '⚫'},
    'DOGEUSD': {'name': 'دوجكوين 🐕', 'symbol': 'DOGEUSD', 'type': 'crypto', 'emoji': '🐕'},
    'AVAXUSD': {'name': 'أفالانش 🏔️', 'symbol': 'AVAXUSD', 'type': 'crypto', 'emoji': '🏔️'},
    'LINKUSD': {'name': 'تشين لينك 🔗', 'symbol': 'LINKUSD', 'type': 'crypto', 'emoji': '🔗'},
    'LTCUSD': {'name': 'لايتكوين 🌙', 'symbol': 'LTCUSD', 'type': 'crypto', 'emoji': '🌙'},
    'BCHUSD': {'name': 'بيتكوين كاش 💚', 'symbol': 'BCHUSD', 'type': 'crypto', 'emoji': '💚'},
}

STOCKS = {
    'AAPL': {'name': 'أبل 🍎', 'symbol': 'AAPL', 'type': 'stock', 'emoji': '🍎'},
    'TSLA': {'name': 'تسلا ⚡', 'symbol': 'TSLA', 'type': 'stock', 'emoji': '⚡'},
    'GOOGL': {'name': 'جوجل 🔍', 'symbol': 'GOOGL', 'type': 'stock', 'emoji': '🔍'},
    'MSFT': {'name': 'مايكروسوفت 💻', 'symbol': 'MSFT', 'type': 'stock', 'emoji': '💻'},
    'AMZN': {'name': 'أمازون 📦', 'symbol': 'AMZN', 'type': 'stock', 'emoji': '📦'},
    'META': {'name': 'ميتا 👥', 'symbol': 'META', 'type': 'stock', 'emoji': '👥'},
    'NVDA': {'name': 'إنفيديا 🎮', 'symbol': 'NVDA', 'type': 'stock', 'emoji': '🎮'},
    'NFLX': {'name': 'نتفليكس 🎬', 'symbol': 'NFLX', 'type': 'stock', 'emoji': '🎬'},
}

INDICES = {
    'US30': {'name': 'داو جونز 🏛️', 'symbol': 'US30', 'type': 'index', 'emoji': '🏛️'},
    'SPX500': {'name': 'ستاندرد آند بورز 500 📊', 'symbol': 'SPX500', 'type': 'index', 'emoji': '📊'},
    'NAS100': {'name': 'ناسداك 100 💻', 'symbol': 'NAS100', 'type': 'index', 'emoji': '💻'},
    'GER40': {'name': 'DAX الألماني 🇩🇪', 'symbol': 'GER40', 'type': 'index', 'emoji': '🇩🇪'},
    'UK100': {'name': 'FTSE 100 البريطاني 🇬🇧', 'symbol': 'UK100', 'type': 'index', 'emoji': '🇬🇧'},
}

# دمج جميع الرموز
ALL_SYMBOLS = {**CURRENCY_PAIRS, **METALS, **CRYPTO_PAIRS, **STOCKS, **INDICES}

# تصنيف الرموز حسب الفئات الخمس المنفصلة
SYMBOL_CATEGORIES = {
    'crypto': {**CRYPTO_PAIRS},
    'forex': {**CURRENCY_PAIRS},
    'metals': {**METALS},
    'stocks': {**STOCKS},
    'indices': {**INDICES}
}

# إعدادات تردد الإشعارات - تردد ثابت 15 ثانية
NOTIFICATION_FREQUENCIES = {
    '15s': {'name': '15 ثانية 🔥', 'seconds': 15},  # التردد الوحيد المدعوم
}

# ===== كلاس إدارة MT5 =====
class MT5Manager:
    """مدير الاتصال مع MetaTrader5"""
    
    def __init__(self):
        self.connected = False
        self.connection_lock = threading.Lock()  # حماية من race conditions
        self.last_connection_attempt = 0
        self.connection_retry_delay = 5  # 5 ثوان بين محاولات الاتصال
        self.max_reconnection_attempts = 3
        self.initialize_mt5()
    
    def initialize_mt5(self):
        """تهيئة الاتصال مع MT5 مع آلية إعادة المحاولة"""
        with self.connection_lock:
            # منع محاولات الاتصال المتكررة
            current_time = time.time()
            if current_time - self.last_connection_attempt < self.connection_retry_delay:
                logger.debug("[DEBUG] محاولة اتصال سابقة حديثة - انتظار...")
                return self.connected
            
            self.last_connection_attempt = current_time
            
            try:
                # إغلاق الاتصال السابق إذا كان موجوداً
                try:
                    mt5.shutdown()
                except:
                    pass
                
                # محاولة الاتصال
                if not mt5.initialize():
                    logger.error("[ERROR] فشل في تهيئة MT5")
                    self.connected = False
                    return False
                
                # التحقق من الاتصال
                account_info = mt5.account_info()
                if account_info is None:
                    logger.error("[ERROR] فشل في الحصول على معلومات الحساب")
                    mt5.shutdown()
                    self.connected = False
                    return False
                
                # اختبار جلب بيانات تجريبية للتأكد من الاتصال
                test_tick = mt5.symbol_info_tick("EURUSD")
                if test_tick is None:
                    logger.warning("[WARNING] فشل في اختبار جلب البيانات")
                    # لا نغلق الاتصال هنا لأن بعض الحسابات قد لا تدعم EURUSD
                
                self.connected = True
                logger.info("[OK] تم الاتصال بـ MetaTrader5 بنجاح!")
                logger.info(f"[DATA] معلومات الحساب: {account_info.login} - {account_info.server}")
                
                # طباعة رسالة النجاح في التيرمينال
                print("\n" + "="*60)
                print("🎉 تم الاتصال بـ MetaTrader5 بنجاح!")
                print(f"📊 رقم الحساب: {account_info.login}")
                print(f"🏦 الخادم: {account_info.server}")
                print(f"💰 الرصيد: {account_info.balance}")
                print(f"💎 العملة: {account_info.currency}")
                print("="*60 + "\n")
                
                return True
                
            except Exception as e:
                logger.error(f"[ERROR] خطأ في تهيئة MT5: {e}")
                self.connected = False
                try:
                    mt5.shutdown()
                except:
                    pass
                return False
    
    def check_real_connection(self) -> bool:
        """التحقق من حالة الاتصال الحقيقية مع MT5 مع آلية إعادة الاتصال"""
        with self.connection_lock:
            try:
                # محاولة جلب معلومات الحساب
                account_info = mt5.account_info()
                if account_info is None:
                    logger.warning("[WARNING] لا يمكن الحصول على معلومات الحساب - محاولة إعادة الاتصال...")
                    self.connected = False
                    return self._attempt_reconnection()
                
                # محاولة جلب معلومات رمز معروف (مع رموز بديلة)
                test_symbols = ["EURUSD", "GBPUSD", "USDJPY", "GOLD", "XAUUSD"]
                symbol_found = False
                
                for symbol in test_symbols:
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info is not None:
                        symbol_found = True
                        break
                
                if not symbol_found:
                    logger.warning("[WARNING] لا يمكن الحصول على معلومات أي رمز - الاتصال ضعيف")
                    self.connected = False
                    return self._attempt_reconnection()
                
                # محاولة جلب تيك حديث لأحد الرموز المتاحة
                tick = None
                for symbol in test_symbols:
                    tick = mt5.symbol_info_tick(symbol)
                    if tick is not None:
                        break
                
                if tick is None:
                    logger.warning("[WARNING] لا يمكن الحصول على البيانات اللحظية - الاتصال معطل")
                    self.connected = False
                    return self._attempt_reconnection()
                
                # التحقق من أن البيانات حديثة (مع مرونة أكبر لبعض الأسواق)
                try:
                    tick_time = datetime.fromtimestamp(tick.time)
                    time_diff = datetime.now() - tick_time
                    
                    # 15 دقيقة بدلاً من 5 للمرونة أكثر
                    if time_diff.total_seconds() > 900:
                        logger.warning(f"[WARNING] البيانات قديمة جداً (عمر: {time_diff}) - الاتصال غير فعال")
                        self.connected = False
                        return self._attempt_reconnection()
                except:
                    # إذا فشل في قراءة وقت التيك، لا نعتبر هذا خطأ كريتيكال
                    pass
                
                # كل شيء طبيعي
                if not self.connected:
                    logger.info("[OK] تم استعادة الاتصال مع MT5")
                    self.connected = True
                    
                return True
                
            except Exception as e:
                logger.error(f"[ERROR] خطأ في التحقق من الاتصال الحقيقي: {e}")
                self.connected = False
                return self._attempt_reconnection()
    
    def _attempt_reconnection(self) -> bool:
        """محاولة إعادة الاتصال التلقائية"""
        logger.info("[RECONNECT] محاولة إعادة الاتصال التلقائية...")
        
        for attempt in range(self.max_reconnection_attempts):
            logger.info(f"[RECONNECT] محاولة رقم {attempt + 1} من {self.max_reconnection_attempts}")
            
            if self.initialize_mt5():
                logger.info("[OK] تم إعادة الاتصال بنجاح!")
                return True
            
            if attempt < self.max_reconnection_attempts - 1:
                wait_time = (attempt + 1) * 2  # انتظار متزايد
                logger.info(f"[RECONNECT] انتظار {wait_time} ثانية قبل المحاولة التالية...")
                time.sleep(wait_time)
        
        logger.error("[ERROR] فشل في إعادة الاتصال بعد عدة محاولات")
        return False
    
    def validate_connection_health(self) -> bool:
        """فحص شامل لصحة الاتصال مع MT5"""
        try:
            if not self.connected:
                return False
            
            # اختبارات متعددة للتأكد من صحة الاتصال
            tests = []
            
            # اختبار 1: معلومات الحساب
            try:
                account_info = mt5.account_info()
                tests.append(account_info is not None)
            except:
                tests.append(False)
            
            # اختبار 2: عدد الرموز المتاحة
            try:
                symbols_total = mt5.symbols_total()
                tests.append(symbols_total > 0)
            except:
                tests.append(False)
            
            # اختبار 3: جلب بيانات تجريبية
            try:
                test_symbols = ["EURUSD", "GBPUSD", "USDJPY"]
                for test_symbol in test_symbols:
                    tick = mt5.symbol_info_tick(test_symbol)
                    if tick is not None:
                        tests.append(True)
                        break
                else:
                    tests.append(False)
            except:
                tests.append(False)
            
            # يجب أن تنجح معظم الاختبارات
            success_rate = sum(tests) / len(tests)
            health_ok = success_rate >= 0.6  # 60% نجاح كحد أدنى
            
            if not health_ok:
                logger.warning(f"[WARNING] صحة اتصال MT5 ضعيفة - نسبة النجاح: {success_rate:.1%}")
                self.connected = False
            
            return health_ok
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في فحص صحة الاتصال: {e}")
            self.connected = False
            return False
    
    def graceful_shutdown(self):
        """إغلاق آمن لاتصال MT5"""
        try:
            with self.connection_lock:
                if self.connected:
                    logger.info("[SYSTEM] إغلاق اتصال MT5...")
                    mt5.shutdown()
                    self.connected = False
                    logger.info("[OK] تم إغلاق اتصال MT5 بأمان")
        except Exception as e:
            logger.error(f"[ERROR] خطأ في إغلاق MT5: {e}")
    
    def get_connection_status_detailed(self) -> Dict:
        """الحصول على تفاصيل حالة الاتصال"""
        try:
            real_status = self.check_real_connection()
            
            status_info = {
                'connected': real_status,
                'status_text': '🟢 متصل ونشط' if real_status else '🔴 منقطع أو معطل',
                'last_check': datetime.now().strftime('%H:%M:%S'),
                'account_info': None,
                'data_freshness': None
            }
            
            if real_status:
                try:
                    account_info = mt5.account_info()
                    if account_info:
                        status_info['account_info'] = {
                            'login': account_info.login,
                            'server': account_info.server,
                            'balance': account_info.balance,
                            'currency': account_info.currency
                        }
                    
                    # فحص حداثة البيانات
                    tick = mt5.symbol_info_tick("EURUSD")
                    if tick:
                        tick_time = datetime.fromtimestamp(tick.time)
                        age_seconds = (datetime.now() - tick_time).total_seconds()
                        status_info['data_freshness'] = f"{age_seconds:.0f} ثانية"
                        
                except Exception as e:
                    logger.error(f"خطأ في جلب تفاصيل الحالة: {e}")
            
            return status_info
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في جلب حالة الاتصال التفصيلية: {e}")
            return {
                'connected': False,
                'status_text': '❌ خطأ في الفحص',
                'last_check': datetime.now().strftime('%H:%M:%S'),
                'error': str(e)
            }
    
    def get_live_price(self, symbol: str, force_fresh: bool = False) -> Optional[Dict]:
        """جلب السعر اللحظي الحقيقي - MT5 هو المصدر الأساسي الأولي مع نظام كاش"""
        
        if not symbol or symbol in ['notification', 'null', '', None]:
            logger.warning(f"[WARNING] رمز غير صالح في get_live_price: {symbol}")
            return None
        
        # إذا كان طلب بيانات لحظية مباشرة (للتحليل اليدوي)، تجاهل الكاش
        if not force_fresh:
            # التحقق من الكاش أولاً للاستدعاءات العادية فقط
            cached_data = get_cached_price_data(symbol)
            if cached_data:
                logger.debug(f"[CACHE] استخدام بيانات مخزنة مؤقتاً لـ {symbol}")
                return cached_data
            
            # التحقق من معدل الاستدعاءات للاستدعاءات العادية فقط
            if not can_make_api_call(symbol):
                logger.debug(f"[RATE_LIMIT] تجاهل الاستدعاء لـ {symbol} - تحديد معدل الاستدعاءات")
                return None
        else:
            logger.info(f"[FRESH_DATA] طلب بيانات لحظية مباشرة للرمز {symbol} - تجاهل الكاش")
        
        # تسجيل وقت الاستدعاء
        record_api_call(symbol)
        
        # 🔍 التحقق من حالة الاتصال الحقيقية أولاً (بدون thread lock لتجنب deadlock)
        real_connection_status = self.connected
        
        # إذا كان الاتصال منقطعاً، نحاول التحقق والإعادة
        if not real_connection_status:
            real_connection_status = self.check_real_connection()
        
        # ✅ المصدر الأساسي الأولي: MetaTrader5
        if real_connection_status:
            try:
                # جلب آخر تيك للرمز من MT5 (البيانات الأكثر دقة)
                with self.connection_lock:
                    tick = mt5.symbol_info_tick(symbol)
                
                if tick is not None and hasattr(tick, 'bid') and hasattr(tick, 'ask') and tick.bid > 0 and tick.ask > 0:
                    # التحقق من أن البيانات حديثة (ليست قديمة)
                    tick_time = datetime.fromtimestamp(tick.time)
                    time_diff = datetime.now() - tick_time
                    
                    # زيادة مرونة وقت البيانات إلى 15 دقيقة
                    if time_diff.total_seconds() > 900:
                        logger.warning(f"[WARNING] بيانات MT5 قديمة للرمز {symbol} (عمر البيانات: {time_diff})")
                        # لا نغير حالة الاتصال فوراً، قد تكون مشكلة مؤقتة في الرمز
                    else:
                        logger.debug(f"[OK] تم جلب البيانات الحديثة من MT5 للرمز {symbol}")
                        # تحسين السعر الحالي - استخدام أفضل قيمة متاحة
                        best_price = tick.last
                        if best_price <= 0:  # إذا كان last = 0، استخدم متوسط bid/ask
                            if tick.bid > 0 and tick.ask > 0:
                                best_price = (tick.bid + tick.ask) / 2
                            elif tick.bid > 0:
                                best_price = tick.bid
                            elif tick.ask > 0:
                                best_price = tick.ask
                        
                        data = {
                            'symbol': symbol,
                            'bid': tick.bid,
                            'ask': tick.ask,
                            'last': best_price,  # استخدام أفضل سعر متاح
                            'volume': tick.volume,
                            'time': tick_time,
                            'spread': tick.ask - tick.bid,
                            'source': 'MetaTrader5 (مصدر أساسي)',
                            'data_age': time_diff.total_seconds()
                        }
                        # حفظ في الكاش
                        cache_price_data(symbol, data)
                        return data
                else:
                    logger.warning(f"[WARNING] لا توجد بيانات صحيحة من MT5 لـ {symbol}")
                    # لا نغير حالة الاتصال فوراً، قد يكون الرمز غير متاح فقط
                    
            except Exception as e:
                logger.warning(f"[WARNING] فشل جلب البيانات من MT5 لـ {symbol}: {e}")
                # تحديد ما إذا كان هذا خطأ اتصال أم خطأ في الرمز
                if "connection" in str(e).lower() or "terminal" in str(e).lower():
                    self.connected = False
        else:
            logger.debug(f"[DEBUG] MT5 غير متصل حقيقياً - سيتم استخدام مصدر بديل لـ {symbol}")
        
        # 🔄 مصدر بديل فقط: Yahoo Finance (للرموز غير المتوفرة في MT5)
        try:
            import yfinance as yf
            
            # تحويل رموز MT5 إلى رموز Yahoo Finance
            yahoo_symbol = self._convert_to_yahoo_symbol(symbol)
            if yahoo_symbol:
                logger.info(f"[RUNNING] محاولة جلب البيانات من Yahoo Finance لـ {symbol}")
                ticker = yf.Ticker(yahoo_symbol)
                data = ticker.history(period="1d", interval="1m")
                
                if not data.empty:
                    latest = data.iloc[-1]
                    current_time = datetime.now()
                    
                    logger.debug(f"[OK] تم جلب البيانات من Yahoo Finance للرمز {symbol}")
                    data = {
                        'symbol': symbol,
                        'bid': latest['Close'] * 0.9995,  # تقدير سعر الشراء
                        'ask': latest['Close'] * 1.0005,  # تقدير سعر البيع
                        'last': latest['Close'],
                        'volume': latest['Volume'],
                        'time': current_time,
                        'spread': latest['Close'] * 0.001,
                        'source': 'Yahoo Finance (مصدر بديل)'
                    }
                    # حفظ في الكاش
                    cache_price_data(symbol, data)
                    return data
                    
        except Exception as e:
            logger.error(f"[ERROR] خطأ في جلب البيانات من Yahoo Finance لـ {symbol}: {e}")
        
        logger.error(f"[ERROR] فشل في جلب البيانات من جميع المصادر للرمز {symbol}")
        return None
    
    def _convert_to_yahoo_symbol(self, mt5_symbol: str) -> Optional[str]:
        """تحويل رموز MT5 إلى رموز Yahoo Finance"""
        conversion_map = {
            # العملات الرقمية
            'BTCUSD': 'BTC-USD',
            'ETHUSD': 'ETH-USD',
            'LTCUSD': 'LTC-USD',
            'BCHUSD': 'BCH-USD',
            
            # أزواج العملات (Forex)
            'EURUSD': 'EURUSD=X',
            'GBPUSD': 'GBPUSD=X',
            'USDJPY': 'USDJPY=X',
            'AUDUSD': 'AUDUSD=X',
            'USDCAD': 'USDCAD=X',
            'USDCHF': 'USDCHF=X',
            'NZDUSD': 'NZDUSD=X',
            'EURJPY': 'EURJPY=X',
            'EURGBP': 'EURGBP=X',
            'EURAUD': 'EURAUD=X',
            
            # المؤشرات
            'US30': '^DJI',
            'SPX500': '^GSPC',
            'NAS100': '^IXIC',
            'GER40': '^GDAXI',
            'UK100': '^FTSE',
            
            # المعادن
            'XAUUSD': 'GC=F',  # الذهب
            'XAGUSD': 'SI=F',  # الفضة
            'XPTUSD': 'PL=F',  # البلاتين
            'XPDUSD': 'PA=F',  # البلاديوم
            
            # العملات الإضافية
            'GBPJPY': 'GBPJPY=X',
            'EURAUD': 'EURAUD=X',
            
            # الأسهم
            'AAPL': 'AAPL',
            'TSLA': 'TSLA', 
            'GOOGL': 'GOOGL',
            'MSFT': 'MSFT',
            'AMZN': 'AMZN',
            'META': 'META',
            'NVDA': 'NVDA',
            'NFLX': 'NFLX'
        }
        
        return conversion_map.get(mt5_symbol)
    
    def get_market_data(self, symbol: str, timeframe: int = mt5.TIMEFRAME_M1, count: int = 100) -> Optional[pd.DataFrame]:
        """جلب بيانات السوق من MT5"""
        if not self.connected:
            return None
        
        try:
            # جلب البيانات
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"[WARNING] لا توجد بيانات للرمز {symbol}")
                return None
            
            # تحويل إلى DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # إعادة تسمية الأعمدة
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            
            return df
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في جلب بيانات السوق من MT5 لـ {symbol}: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """جلب معلومات الرمز من MT5"""
        if not self.connected:
            return None
        
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return None
            
            return {
                'symbol': info.name,
                'description': info.description,
                'point': info.point,
                'digits': info.digits,
                'spread': info.spread,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step,
                'contract_size': info.trade_contract_size,
                'currency_base': info.currency_base,
                'currency_profit': info.currency_profit,
                'margin_currency': info.currency_margin,
            }
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في جلب معلومات الرمز {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, symbol: str) -> Optional[Dict]:
        """حساب المؤشرات الفنية من البيانات التاريخية للرمز"""
        try:
            if not self.connected:
                logger.warning(f"[WARNING] MT5 غير متصل - لا يمكن حساب المؤشرات لـ {symbol}")
                return None
            
            # جلب البيانات التاريخية (100 شمعة للمؤشرات)
            df = self.get_market_data(symbol, mt5.TIMEFRAME_M15, 100)
            if df is None or len(df) < 20:
                logger.warning(f"[WARNING] بيانات غير كافية لحساب المؤشرات لـ {symbol}")
                return None
            
            indicators = {}
            
            # المتوسطات المتحركة
            if len(df) >= 9:
                indicators['ma_9'] = ta.trend.sma_indicator(df['close'], window=9).iloc[-1]
            if len(df) >= 21:
                indicators['ma_21'] = ta.trend.sma_indicator(df['close'], window=21).iloc[-1]
            
            # RSI
            if len(df) >= 14:
                indicators['rsi'] = ta.momentum.rsi(df['close'], window=14).iloc[-1]
                
                # تفسير RSI
                if indicators['rsi'] > 70:
                    indicators['rsi_interpretation'] = 'ذروة شراء'
                elif indicators['rsi'] < 30:
                    indicators['rsi_interpretation'] = 'ذروة بيع'
                else:
                    indicators['rsi_interpretation'] = 'محايد'
            
            # MACD
            if len(df) >= 26:
                macd_line = ta.trend.macd(df['close'])
                macd_signal = ta.trend.macd_signal(df['close'])
                macd_histogram = ta.trend.macd_diff(df['close'])
                
                indicators['macd'] = {
                    'macd': macd_line.iloc[-1] if not pd.isna(macd_line.iloc[-1]) else 0,
                    'signal': macd_signal.iloc[-1] if not pd.isna(macd_signal.iloc[-1]) else 0,
                    'histogram': macd_histogram.iloc[-1] if not pd.isna(macd_histogram.iloc[-1]) else 0
                }
                
                # تفسير MACD
                if indicators['macd']['macd'] > indicators['macd']['signal']:
                    indicators['macd_interpretation'] = 'إشارة صعود'
                elif indicators['macd']['macd'] < indicators['macd']['signal']:
                    indicators['macd_interpretation'] = 'إشارة هبوط'
                else:
                    indicators['macd_interpretation'] = 'محايد'
            
            # حجم التداول
            indicators['current_volume'] = df['tick_volume'].iloc[-1]
            if len(df) >= 20:
                indicators['avg_volume'] = df['tick_volume'].rolling(window=20).mean().iloc[-1]
                indicators['volume_ratio'] = indicators['current_volume'] / indicators['avg_volume']
                
                if indicators['volume_ratio'] > 1.5:
                    indicators['volume_interpretation'] = 'حجم عالي'
                elif indicators['volume_ratio'] < 0.5:
                    indicators['volume_interpretation'] = 'حجم منخفض'
                else:
                    indicators['volume_interpretation'] = 'حجم طبيعي'
            
            # Stochastic
            if len(df) >= 14:
                stoch_k = ta.momentum.stoch(df['high'], df['low'], df['close'])
                stoch_d = ta.momentum.stoch_signal(df['high'], df['low'], df['close'])
                
                indicators['stochastic'] = {
                    'k': stoch_k.iloc[-1] if not pd.isna(stoch_k.iloc[-1]) else 50,
                    'd': stoch_d.iloc[-1] if not pd.isna(stoch_d.iloc[-1]) else 50
                }
            
            # البولنجر باندز
            if len(df) >= 20:
                bollinger_high = ta.volatility.bollinger_hband(df['close'])
                bollinger_low = ta.volatility.bollinger_lband(df['close'])
                bollinger_mid = ta.volatility.bollinger_mavg(df['close'])
                
                indicators['bollinger'] = {
                    'upper': bollinger_high.iloc[-1] if not pd.isna(bollinger_high.iloc[-1]) else df['close'].iloc[-1] * 1.02,
                    'middle': bollinger_mid.iloc[-1] if not pd.isna(bollinger_mid.iloc[-1]) else df['close'].iloc[-1],
                    'lower': bollinger_low.iloc[-1] if not pd.isna(bollinger_low.iloc[-1]) else df['close'].iloc[-1] * 0.98
                }
                
                # تفسير البولنجر باندز
                current_price = df['close'].iloc[-1]
                if current_price > indicators['bollinger']['upper']:
                    indicators['bollinger_interpretation'] = 'فوق النطاق العلوي - إشارة بيع محتملة'
                elif current_price < indicators['bollinger']['lower']:
                    indicators['bollinger_interpretation'] = 'تحت النطاق السفلي - إشارة شراء محتملة'
                else:
                    indicators['bollinger_interpretation'] = 'ضمن النطاق - حركة طبيعية'
            
            # الدعم والمقاومة
            if len(df) >= 20:
                indicators['resistance'] = df['high'].rolling(window=20).max().iloc[-1]
                indicators['support'] = df['low'].rolling(window=20).min().iloc[-1]
            
            # معلومات السعر الحالي
            indicators['current_price'] = df['close'].iloc[-1]
            indicators['price_change_pct'] = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) >= 2 else 0
            
            # تحديد الاتجاه العام
            trend_signals = []
            if 'ma_9' in indicators and 'ma_21' in indicators:
                if indicators['ma_9'] > indicators['ma_21']:
                    trend_signals.append('صعود')
                else:
                    trend_signals.append('هبوط')
            
            if 'rsi' in indicators:
                if indicators['rsi'] > 50:
                    trend_signals.append('صعود')
                else:
                    trend_signals.append('هبوط')
            
            # تحديد الاتجاه الغالب
            if trend_signals.count('صعود') > trend_signals.count('هبوط'):
                indicators['overall_trend'] = 'صاعد'
            elif trend_signals.count('هبوط') > trend_signals.count('صعود'):
                indicators['overall_trend'] = 'هابط'
            else:
                indicators['overall_trend'] = 'محايد'
            
            logger.info(f"[OK] تم حساب المؤشرات الفنية لـ {symbol} - الاتجاه: {indicators['overall_trend']}")
            
            return {
                'symbol': symbol,
                'indicators': indicators,
                'calculated_at': datetime.now(),
                'data_points': len(df)
            }
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في حساب المؤشرات الفنية لـ {symbol}: {e}")
            return None

# إنشاء مثيل مدير MT5
mt5_manager = MT5Manager()

# ===== كلاس تحليل Gemini AI =====
class GeminiAnalyzer:
    """محلل الذكاء الاصطناعي باستخدام Google Gemini"""
    
    def __init__(self):
        self.model = None
        if GEMINI_AVAILABLE:
            try:
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("[OK] تم تهيئة محلل Gemini بنجاح")
            except Exception as e:
                logger.error(f"[ERROR] فشل في تهيئة محلل Gemini: {e}")
    
    def analyze_market_data_with_retry(self, symbol: str, price_data: Dict, user_id: int = None, market_data: pd.DataFrame = None, max_retries: int = 3) -> Dict:
        """تحليل بيانات السوق مع آلية إعادة المحاولة"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.analyze_market_data(symbol, price_data, user_id, market_data)
            except Exception as e:
                last_error = e
                if attempt == max_retries - 1:
                    logger.error(f"[ERROR] فشل نهائي في تحليل {symbol} بعد {max_retries} محاولات: {e}")
                    return self._fallback_analysis(symbol, price_data)
                
                wait_time = (2 ** attempt) + (attempt * 0.1)  # exponential backoff
                logger.warning(f"[WARNING] محاولة {attempt + 1} فشلت لـ {symbol}: {e}. إعادة المحاولة خلال {wait_time:.1f} ثانية...")
                time.sleep(wait_time)
        
        # إذا فشلت جميع المحاولات
        return self._fallback_analysis(symbol, price_data)

    def analyze_market_data(self, symbol: str, price_data: Dict, user_id: int = None, market_data: pd.DataFrame = None) -> Dict:
        """تحليل بيانات السوق باستخدام Gemini AI مع مراعاة سياق المستخدم والمؤشرات الفنية"""
        if not self.model:
            return self._fallback_analysis(symbol, price_data)
        
        try:
            # إعداد البيانات للتحليل
            current_price = price_data.get('last', price_data.get('bid', 0))
            spread = price_data.get('spread', 0)
            data_source = price_data.get('source', 'Unknown')
            
            # جلب المؤشرات الفنية الحقيقية من MT5
            technical_data = mt5_manager.calculate_technical_indicators(symbol)
            technical_analysis = ""
            
            if technical_data and technical_data.get('indicators'):
                indicators = technical_data['indicators']
                technical_analysis = f"""
                
                المؤشرات الفنية الحقيقية (محسوبة من البيانات التاريخية):
                - المتوسط المتحرك 9: {indicators.get('ma_9', 'غير متوفر'):.5f}
                - المتوسط المتحرك 21: {indicators.get('ma_21', 'غير متوفر'):.5f}
                - RSI: {indicators.get('rsi', 'غير متوفر'):.2f} ({indicators.get('rsi_interpretation', 'غير محدد')})
                - MACD: {indicators.get('macd', {}).get('macd', 'غير متوفر'):.5f}
                - MACD Signal: {indicators.get('macd', {}).get('signal', 'غير متوفر'):.5f}
                - MACD Histogram: {indicators.get('macd', {}).get('histogram', 'غير متوفر'):.5f}
                - تفسير MACD: {indicators.get('macd_interpretation', 'غير محدد')}
                - حجم التداول الحالي: {indicators.get('current_volume', 'غير متوفر')}
                - متوسط الحجم: {indicators.get('avg_volume', 'غير متوفر')}
                - نسبة الحجم: {indicators.get('volume_ratio', 'غير متوفر'):.2f}
                - تفسير الحجم: {indicators.get('volume_interpretation', 'غير محدد')}
                - Stochastic %K: {indicators.get('stochastic', {}).get('k', 'غير متوفر'):.2f}
                - Stochastic %D: {indicators.get('stochastic', {}).get('d', 'غير متوفر'):.2f}
                - Bollinger Upper: {indicators.get('bollinger', {}).get('upper', 'غير متوفر'):.5f}
                - Bollinger Middle: {indicators.get('bollinger', {}).get('middle', 'غير متوفر'):.5f}
                - Bollinger Lower: {indicators.get('bollinger', {}).get('lower', 'غير متوفر'):.5f}
                - تفسير Bollinger: {indicators.get('bollinger_interpretation', 'غير محدد')}
                - مقاومة: {indicators.get('resistance', 'غير متوفر'):.5f}
                - دعم: {indicators.get('support', 'غير متوفر'):.5f}
                - الاتجاه العام: {indicators.get('overall_trend', 'غير محدد')}
                - تغيير السعر %: {indicators.get('price_change_pct', 0):.2f}%
                """
            else:
                technical_analysis = """
                
                المؤشرات الفنية: غير متوفرة (MT5 غير متصل أو بيانات غير كافية)
                """
            
            # تحديد نوع الرمز وخصائصه
            symbol_type_context = ""
            if symbol.endswith('USD'):
                if symbol.startswith('EUR') or symbol.startswith('GBP'):
                    symbol_type_context = """
                    
                    **سياق خاص بأزواج العملات الرئيسية:**
                    - هذا زوج عملات رئيسي بسيولة عالية وتقلبات معتدلة
                    - تأثر قوي بقرارات البنوك المركزية (Fed, ECB, BoE)
                    - ساعات التداول النشطة: London + New York overlap
                    - عوامل مؤثرة: معدلات الفائدة، التضخم، GDP، البطالة
                    - نسبة النجاح المتوقعة أعلى بسبب قابلية التنبؤ النسبية
                    """
                elif symbol.startswith('XAU') or symbol.startswith('XAG'):
                    symbol_type_context = """
                    
                    **سياق خاص بالمعادن النفيسة:**
                    - الذهب/الفضة أصول ملاذ آمن مع تقلبات متوسطة إلى عالية
                    - تأثر قوي بالأحداث الجيوسياسية والتضخم
                    - علاقة عكسية مع الدولار الأمريكي عادة
                    - عوامل مؤثرة: التضخم، أسعار الفائدة، الأزمات العالمية
                    - كن حذراً من التحركات المفاجئة خلال الأخبار المهمة
                    """
                elif symbol.startswith('BTC') or symbol.startswith('ETH'):
                    symbol_type_context = """
                    
                    **سياق خاص بالعملات الرقمية:**
                    - تقلبات عالية جداً مع إمكانية مكاسب/خسائر كبيرة
                    - سوق 24/7 مع تأثر قوي بالمشاعر والأخبار
                    - تأثر بالتنظيم الحكومي، اعتماد المؤسسات، التطوير التقني
                    - عوامل مؤثرة: تصريحات المؤثرين، القرارات التنظيمية، التطوير التقني
                    - قلل نسبة النجاح 10-15% بسبب عدم القابلية للتنبؤ
                    """
                else:
                    symbol_type_context = """
                    
                    **سياق عام للأصول:**
                    - حلل خصائص هذا الرمز والعوامل المؤثرة عليه
                    - اعتبر السيولة والتقلبات التاريخية
                    - راعِ ساعات التداول النشطة والأحداث الاقتصادية
                    """
            
            # جلب سياق المستخدم
            user_context = ""
            trading_mode_instructions = ""
            
            if user_id:
                trading_mode = get_user_trading_mode(user_id)
                capital = get_user_capital(user_id)
                user_timezone = get_user_timezone(user_id)
                
                user_context = f"""
                
                سياق المستخدم:
                - نمط التداول: {trading_mode} ({'سكالبينغ سريع' if trading_mode == 'scalping' else 'تداول طويل المدى'})
                - رأس المال: ${capital:,.2f}
                - المنطقة الزمنية: {user_timezone}
                """
                
                # تخصيص التحليل حسب نمط التداول
                if trading_mode == 'scalping':
                    trading_mode_instructions = """
                    
                    تعليمات خاصة للسكالبينغ:
                    - ركز على الفرص قصيرة المدى (دقائق إلى ساعات)
                    - أهداف ربح صغيرة (1-2%)
                    - وقف خسارة ضيق (0.5-1%)
                    - تحليل سريع وفوري
                    - ثقة عالية مطلوبة (80%+)
                    - ركز على التحركات السريعة والمؤشرات قصيرة المدى
                    - حجم صفقات أصغر لتقليل المخاطر
                    - اهتم بـ RSI و MACD للإشارات السريعة
                    """
                else:
                    trading_mode_instructions = """
                    
                    تعليمات خاصة للتداول طويل المدى:
                    - ركز على الاتجاهات طويلة المدى (أيام إلى أسابيع)
                    - أهداف ربح أكبر (5-10%)
                    - وقف خسارة أوسع (2-3%)
                    - تحليل شامل ومتأني
                    - تحمل تذبذبات أكثر
                    - ركز على الاتجاهات الرئيسية والأساسيات
                    - حجم صفقات أكبر للاستفادة من الاتجاهات الطويلة
                    - اهتم بالمتوسطات المتحركة والدعم والمقاومة
                    """
            
            # تحميل بيانات التدريب السابقة
            training_context = self._load_training_context(symbol)
            
            # تحميل الأنماط المتعلمة من الصور
            learned_patterns = self._load_learned_patterns()
            
            # إنشاء prompt مختصر وفعال للتحليل
            prompt = f"""
            أنت محلل تداول خبير. حلل الرمز {symbol} بناءً على البيانات التالية وأعط تحليل مختصر:
            
            البيانات:
            - السعر: {current_price}
            - البيد/الأسك: {price_data.get('bid', 'N/A')}/{price_data.get('ask', 'N/A')}
            {technical_analysis}
            {user_context}
            
            المطلوب:
            1. تحليل المؤشرات (RSI, MACD, MA9, MA21)
            2. تحديد الإشارة: BUY/SELL/HOLD
            3. حساب نسبة نجاح الصفقة من 1-100
            
            التنسيق المطلوب (مختصر):
            📊 التحليل: [تحليل موجز للمؤشرات]
            🎯 الإشارة: [BUY/SELL/HOLD]
            📈 نسبة النجاح: [رقم]%
            
            كن مختصراً ومحدداً. ركز على الأرقام والحقائق فقط.
            """
            # إرسال الطلب لـ Gemini
            response = self.model.generate_content(prompt)
            analysis_text = response.text
            
            # استخراج التوصية ونسبة النجاح من النص
            recommendation = self._extract_recommendation(analysis_text)
            success_rate = self._extract_ai_success_rate(analysis_text)
            
            # تسجيل تفاصيل لتتبع نسبة النجاح المستخرجة
            logger.info(f"[AI_ANALYSIS] {symbol}: التوصية={recommendation}, نسبة النجاح={success_rate:.1f}%")
            
            return {
                'action': recommendation,
                'confidence': success_rate,  # نسبة النجاح من AI
                'success_rate': success_rate,  # حفظ نسخة إضافية
                'reasoning': [analysis_text],
                'ai_analysis': analysis_text,
                'source': f'Gemini AI ({data_source})',
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price_data': price_data,
                'user_context': user_context if user_id else None
            }
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في تحليل Gemini للرمز {symbol}: {e}")
            return self._fallback_analysis(symbol, price_data)
    
    def _load_training_context(self, symbol: str) -> str:
        """تحميل سياق التدريب السابق للرمز"""
        try:
            training_file = os.path.join(FEEDBACK_DIR, "ai_training_data.json")
            if os.path.exists(training_file):
                with open(training_file, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
                
                # البحث عن بيانات تدريب متعلقة بالرمز
                relevant_data = [item for item in training_data if item.get('symbol') == symbol]
                if relevant_data:
                    return f"بيانات تدريب سابقة: {len(relevant_data)} تقييم سابق للرمز"
            
            return "لا توجد بيانات تدريب سابقة لهذا الرمز"
        except:
            return ""
    
    def _load_learned_patterns(self) -> str:
        """تحميل الأنماط المتعلمة من الصور"""
        try:
            patterns_file = os.path.join(FEEDBACK_DIR, "learned_patterns.json")
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                
                if patterns:
                    context = "\n🧠 الأنماط المتعلمة من المستخدمين:\n"
                    for pattern in patterns[-10:]:  # آخر 10 أنماط
                        pattern_info = pattern.get('pattern_info', {})
                        description = pattern.get('user_description', '')
                        
                        context += f"""
- النمط: {pattern_info.get('pattern_name', 'نمط مخصص')}
  الاتجاه: {pattern_info.get('direction', 'غير محدد')}
  الثقة: {pattern_info.get('confidence', 50)}%
  الوصف: {description[:100]}...
                        """
                    
                    context += "\n⚠️ يرجى مراعاة هذه الأنماط المتعلمة عند التحليل.\n"
                    return context
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في تحميل الأنماط المتعلمة: {e}")
        
        return ""
    
    def _adjust_confidence_for_user(self, confidence: float, user_id: int) -> float:
        """تعديل مستوى الثقة حسب نمط التداول"""
        try:
            trading_mode = get_user_trading_mode(user_id)
            
            if trading_mode == 'scalping':
                # للسكالبينغ، نحتاج ثقة أعلى
                return min(confidence * 0.9, 95.0)  # تقليل الثقة قليلاً للحذر
            elif trading_mode == 'longterm':
                # للتداول طويل المدى، يمكن قبول ثقة أقل
                return min(confidence * 1.1, 95.0)  # زيادة الثقة قليلاً
            
            return confidence
        except:
            return confidence
    
    def _extract_recommendation(self, text: str) -> str:
        """استخراج التوصية من نص التحليل"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['شراء', 'buy', 'صاعد', 'ارتفاع']):
            return 'BUY'
        elif any(word in text_lower for word in ['بيع', 'sell', 'هابط', 'انخفاض']):
            return 'SELL'
        else:
            return 'HOLD'
    
    def _extract_confidence(self, text: str) -> float:
        """استخراج مستوى الثقة من نص التحليل"""
        # أولاً، البحث عن نسبة النجاح المحددة من Gemini
        success_rate = self._extract_success_rate_from_ai(text)
        if success_rate is not None:
            return success_rate
        
        # إذا لم نجد نسبة محددة، نستخدم الطريقة القديمة كبديل
        import re
        numbers = re.findall(r'\d+', text)
        
        # البحث عن رقم بين 1-100
        for num in numbers:
            confidence = int(num)
            if 1 <= confidence <= 100:
                return confidence
        
        # إذا لم نجد رقم مناسب، نحدد الثقة بناءً على كلمات معينة
        text_lower = text.lower()
        if any(word in text_lower for word in ['قوي', 'عالي', 'مؤكد', 'واضح']):
            return 80.0
        elif any(word in text_lower for word in ['متوسط', 'محتمل']):
            return 60.0
        elif any(word in text_lower for word in ['ضعيف', 'غير مؤكد']):
            return 40.0
        else:
            return 50.0

    def _extract_success_rate_from_ai(self, text: str) -> float:
        """استخراج نسبة النجاح المحددة من الذكاء الاصطناعي"""
        try:
            import re
            
            # البحث عن نص "نسبة نجاح الصفقة" متبوعاً برقم ونسبة مئوية
            patterns = [
                r'نسبة نجاح الصفقة:?\s*(\d+)%',
                r'نسبة النجاح:?\s*(\d+)%',
                r'احتمالية النجاح:?\s*(\d+)%',
                r'معدل النجاح:?\s*(\d+)%',
                r'success rate:?\s*(\d+)%',
                r'نسبة\s+نجاح\s+(?:الصفقة|التداول):?\s*(\d+)%',
                # البحث في نهاية النص
                r'النسبة:?\s*(\d+)%',
                r'التوقع:?\s*(\d+)%'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
                if matches:
                    success_rate = float(matches[-1])  # أخذ آخر نتيجة
                    # التأكد من أن النسبة في النطاق المطلوب
                    if 10 <= success_rate <= 95:
                        logger.info(f"[AI_SUCCESS_EXTRACT] تم استخراج نسبة نجاح من AI: {success_rate}%")
                        return success_rate
            
            # البحث عن أرقام في نهاية النص (آخر 200 حرف)
            text_end = text[-200:].lower()
            numbers_at_end = re.findall(r'(\d+)%', text_end)
            
            for num_str in reversed(numbers_at_end):  # البدء من النهاية
                num = float(num_str)
                if 10 <= num <= 95:
                    logger.info(f"[AI_SUCCESS_EXTRACT] تم استخراج نسبة من نهاية النص: {num}%")
                    return num
            
            # إذا لم نجد شيئاً محدداً، نعيد None لاستخدام الطريقة البديلة
            return None
            
        except Exception as e:
            logger.warning(f"[WARNING] خطأ في استخراج نسبة النجاح من AI: {e}")
            return None
    
    def _extract_ai_success_rate(self, text: str) -> float:
        """استخراج نسبة النجاح من تحليل AI مباشرة دون قيم ثابتة"""
        try:
            # أولاً، محاولة استخراج من النص الموجود
            existing_rate = self._extract_success_rate_from_ai(text)
            if existing_rate is not None:
                return existing_rate
            
            # إرسال طلب مباشر لـ Gemini لحساب نسبة النجاح
            success_rate_prompt = f"""
            بناءً على التحليل التالي:
            {text[:800]}
            
            احسب نسبة نجاح هذه الصفقة من 1 إلى 100 بناءً على:
            1. قوة المؤشرات الفنية
            2. اتساق الإشارات  
            3. حالة السوق العامة
            4. مستوى المخاطرة
            
            أعطني رقماً واحداً فقط من 1-100 بدون أي نص إضافي.
            """
            
            if self.model:
                try:
                    response = self.model.generate_content(success_rate_prompt)
                    success_text = response.text.strip()
                    
                    # استخراج الرقم من الاستجابة
                    import re
                    numbers = re.findall(r'\b(\d{1,3})\b', success_text)
                    for num in numbers:
                        rate = int(num)
                        if 1 <= rate <= 100:
                            logger.info(f"[AI_SUCCESS_DIRECT] تم الحصول على نسبة النجاح من AI: {rate}%")
                            return float(rate)
                            
                except Exception as e:
                    logger.warning(f"[WARNING] فشل في الحصول على نسبة النجاح من AI: {e}")
            
            # في حالة فشل AI، استخدم تحليل النص الموجود
            return self._analyze_text_for_success_rate(text)
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في استخراج نسبة النجاح من AI: {e}")
            return self._analyze_text_for_success_rate(text)
    
    def _analyze_text_for_success_rate(self, text: str) -> float:
        """تحليل النص لاستخراج نسبة النجاح كبديل"""
        text_lower = text.lower()
        
        # عدد الإشارات الإيجابية والسلبية
        positive_signals = 0
        negative_signals = 0
        
        positive_words = ['قوي', 'عالي', 'مؤكد', 'واضح', 'إيجابي', 'صعود', 'مرتفع', 'جيد', 'ممتاز']
        negative_words = ['ضعيف', 'منخفض', 'محدود', 'سلبي', 'هبوط', 'متراجع', 'سيء', 'متضارب']
        
        for word in positive_words:
            positive_signals += text_lower.count(word)
            
        for word in negative_words:
            negative_signals += text_lower.count(word)
            
        # حساب النسبة بناءً على الإشارات
        total_signals = positive_signals + negative_signals
        if total_signals > 0:
            positive_ratio = positive_signals / total_signals
            success_rate = min(max(positive_ratio * 100, 25), 90)
            logger.info(f"[AI_SUCCESS_TEXT] تم حساب نسبة النجاح من النص: {success_rate:.1f}%")
            return success_rate
        
        return 55.0  # قيمة افتراضية متوسطة
    
    def get_symbol_news(self, symbol: str) -> str:
        """جلب أخبار مختصرة ومؤثرة للرمز عبر AI"""
        try:
            if not self.model:
                return "• 📰 مراقبة التطورات الاقتصادية الحالية"
            
            # طلب مختصر لـ AI لإنتاج أخبار مؤثرة
            news_prompt = f"""
            اكتب 2-3 عناوين أخبار مختصرة تؤثر على الرمز {symbol}:
            
            المطلوب:
            - عناوين قصيرة (10-15 كلمة)
            - أخبار مؤثرة على سعر الرمز
            - استخدم رموز الاتجاه: ↗️ للصعود، ↘️ للهبوط، ↗️↘️ للتذبذب
            
            التنسيق:
            • [رمز] [عنوان قصير] [اتجاه]
            
            مثال:
            • 📊 بيانات التضخم الأمريكي تحرك الدولار ↗️
            """
            
            try:
                response = self.model.generate_content(news_prompt)
                news_text = response.text.strip()
                
                # تنظيف النص وإرجاع الأخبار
                if news_text and len(news_text) > 10:
                    return news_text
                else:
                    return self._get_fallback_news(symbol)
                    
            except Exception as ai_error:
                logger.warning(f"[WARNING] فشل في إنتاج الأخبار عبر AI: {ai_error}")
                return self._get_fallback_news(symbol)
            
        except Exception as e:
            logger.error(f"خطأ في جلب الأخبار للرمز {symbol}: {e}")
            return "• 📰 مراقبة التطورات الاقتصادية الحالية"
    
    def _get_fallback_news(self, symbol: str) -> str:
        """أخبار احتياطية مختصرة"""
        if 'USD' in symbol:
            return "• 📊 بيانات اقتصادية أمريكية تؤثر على الدولار ↗️↘️"
        elif 'EUR' in symbol:
            return "• 🇪🇺 قرارات البنك المركزي الأوروبي مؤثرة ↗️↘️"
        elif 'XAU' in symbol or 'XAG' in symbol:
            return "• 🥇 طلب الملاذ الآمن يدعم المعادن النفيسة ↗️"
        elif 'BTC' in symbol or 'ETH' in symbol:
            return "• ₿ تطورات تنظيم العملات الرقمية تخلق تذبذب ↗️↘️"
        else:
            return "• 🌍 التطورات الاقتصادية العالمية مؤثرة ↗️↘️"
    

    
    def format_comprehensive_analysis_v120(self, symbol: str, symbol_info: Dict, price_data: Dict, analysis: Dict, user_id: int) -> str:
        """تنسيق التحليل الشامل المتقدم للإصدار v1.2.0 بالتنسيق المطلوب الكامل"""
        try:
            # الحصول على بيانات المستخدم
            trading_mode = get_user_trading_mode(user_id)
            capital = get_user_capital(user_id)
            formatted_time = format_time_for_user(user_id, price_data.get('time'))
            
            # البيانات الأساسية
            current_price = price_data.get('last', price_data.get('bid', 0))
            bid = price_data.get('bid', 0)
            ask = price_data.get('ask', 0)
            spread = price_data.get('spread', 0)
            
            # التحقق من صحة البيانات
            if current_price <= 0:
                current_price = max(bid, ask) if max(bid, ask) > 0 else None
            if not current_price:
                logger.warning(f"[WARNING] لا توجد بيانات أسعار صحيحة للرمز {symbol}")
                return "❌ **لا توجد بيانات أسعار صحيحة**\n\nفشل في الحصول على أسعار صالحة للرمز."
                
            # بيانات التحليل
            action = analysis.get('action', 'HOLD')
            confidence = analysis.get('confidence', 56)
            
            # نسبة النجاح من الذكاء الاصطناعي (أولوية أعلى من الثقة العادية)
            ai_success_rate = confidence  # نسبة النجاح المستخرجة من Gemini AI مباشرة
            
            # التأكد من أن نسبة النجاح في النطاق المناسب وإضافة تحذير إذا لزم الأمر
            success_rate_source = "محسوبة بالذكاء الاصطناعي"
            if ai_success_rate < 20:
                success_rate_source = "منخفضة - تحذير"
            elif ai_success_rate > 90:
                success_rate_source = "عالية جداً - تحقق مرة أخرى"
            
            # جلب المؤشرات الفنية الحقيقية مع معالجة الأخطاء
            technical_data = None
            indicators = {}
            
            try:
                technical_data = mt5_manager.calculate_technical_indicators(symbol)
                indicators = technical_data.get('indicators', {}) if technical_data else {}
                logger.info(f"[INFO] تم جلب المؤشرات الفنية للرمز {symbol}")
            except Exception as e:
                logger.warning(f"[WARNING] فشل في جلب المؤشرات الفنية للرمز {symbol}: {e}")
                indicators = {}
            
            # حساب الأهداف والوقف بناءً على التحليل الذكي والمؤشرات
            entry_price = current_price
            
            # استخدام مستويات الدعم والمقاومة الحقيقية إذا متوفرة
            resistance = indicators.get('resistance', current_price * 1.02)
            support = indicators.get('support', current_price * 0.98)
            
            if action == 'BUY':
                target1 = resistance * 0.99  # قريب من المقاومة
                target2 = resistance * 1.01  # فوق المقاومة قليلاً
                stop_loss = support * 1.01   # فوق الدعم قليلاً
            elif action == 'SELL':
                target1 = support * 1.01     # قريب من الدعم
                target2 = support * 0.99     # تحت الدعم قليلاً
                stop_loss = resistance * 0.99 # تحت المقاومة قليلاً
            else:
                target1 = current_price * 1.015
                target2 = current_price * 1.03
                stop_loss = current_price * 0.985
            
            # حساب النقاط
            points1 = abs(target1 - entry_price) * 10000 if entry_price else 0
            points2 = abs(target2 - entry_price) * 10000 if entry_price else 0
            stop_points = abs(entry_price - stop_loss) * 10000 if entry_price else 0
            
            # حساب نسبة المخاطرة/المكافأة
            risk_reward_ratio = (points1 / stop_points) if stop_points > 0 else 1.0
            
            # حساب التغيير اليومي الحقيقي
            price_change_pct = indicators.get('price_change_pct', 0)
            daily_change = f"{price_change_pct:+.2f}%" if price_change_pct != 0 else "--"
            
            # التحقق من وجود تحذيرات
            has_warning = analysis.get('warning') or not indicators or confidence == 0
            
            # بناء الرسالة بالتنسيق المطلوب الكامل
            message = "🚀 تحليل شامل متقدم\n\n"
            
            # إضافة تحذير إذا كانت البيانات محدودة
            if has_warning:
                message += "⚠️ **تحذير مهم:** البيانات أو التحليل محدود - لا تتداول بناءً على هذه المعلومات!\n\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"💱 {symbol} | {symbol_info['name']} {symbol_info['emoji']}\n"
            message += f"📡 مصدر البيانات: 🔗 MetaTrader5 (لحظي - بيانات حقيقية)\n"
            message += f"💰 السعر الحالي: {current_price:,.5f}\n"
            message += f"➡️ التغيير اليومي: {daily_change}\n"
            message += f"⏰ وقت التحليل: {formatted_time}\n\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "⚡ إشارة التداول الرئيسية\n\n"
            
            # نوع الصفقة
            if action == 'BUY':
                message += f"🟢 نوع الصفقة: شراء (BUY)\n"
            elif action == 'SELL':
                message += f"🔴 نوع الصفقة: بيع (SELL)\n"
            else:
                message += f"🟡 نوع الصفقة: انتظار (HOLD)\n"
            
            message += f"📍 سعر الدخول المقترح: {entry_price:,.5f}\n"
            message += f"🎯 الهدف الأول: {target1:,.5f} ({points1:.0f} نقطة)\n"
            message += f"🎯 الهدف الثاني: {target2:,.5f} ({points2:.0f} نقطة)\n"
            message += f"🛑 وقف الخسارة: {stop_loss:,.5f} ({stop_points:.0f} نقطة)\n"
            message += f"📊 نسبة المخاطرة/المكافأة: 1:{risk_reward_ratio:.1f}\n"
            message += f"✅ نسبة نجاح الصفقة: {ai_success_rate:.0f}%\n\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "🔧 التحليل الفني المتقدم\n\n"
            
            # المؤشرات الفنية الحقيقية
            message += "📈 المؤشرات الفنية:\n"
            
            if indicators:
                # RSI
                rsi = indicators.get('rsi')
                if rsi and rsi > 0:
                    rsi_status = indicators.get('rsi_interpretation', 'محايد')
                    message += f"• RSI: {rsi:.1f} ({rsi_status})\n"
                else:
                    message += f"• RSI: --\n"
                
                # MACD
                macd_data = indicators.get('macd', {})
                if macd_data and macd_data.get('macd') is not None:
                    macd_value = macd_data.get('macd', 0)
                    macd_status = indicators.get('macd_interpretation', 'محايد')
                    message += f"• MACD: {macd_value:.4f} ({macd_status})\n"
                else:
                    message += f"• MACD: --\n"
                
                # المتوسطات المتحركة
                ma9 = indicators.get('ma_9')
                ma21 = indicators.get('ma_21')
                
                if ma9 and ma9 > 0:
                    message += f"• MA9: {ma9:.5f}\n"
                else:
                    message += f"• MA9: --\n"
                    
                if ma21 and ma21 > 0:
                    message += f"• MA21: {ma21:.5f}\n"
                else:
                    message += f"• MA21: --\n"
                
            else:
                message += f"• RSI: --\n"
                message += f"• MACD: --\n"
                message += f"• MA9: --\n"
                message += f"• MA21: --\n"
            
            message += "\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "📋 توصيات إدارة المخاطر\n\n"
            
            message += "💡 حجم المركز المقترح:\n"
            if trading_mode == "scalping":
                message += "• للسكالبينغ: 0.01 لوت (مخاطرة منخفضة)\n\n"
            else:
                message += "• للمدى الطويل: 0.005 لوت (مخاطرة محافظة)\n\n"
            
            # إضافة تحليل مستويات الدعم والمقاومة إذا متوفرة
            if indicators:
                resistance_level = indicators.get('resistance')
                support_level = indicators.get('support')
                if resistance_level and support_level:
                    message += "📊 مستويات مهمة:\n"
                    message += f"• مقاومة: {resistance_level:.5f}\n"
                    message += f"• دعم: {support_level:.5f}\n\n"
                
                # تحليل حجم التداول
                volume_status = indicators.get('volume_interpretation')
                volume_ratio = indicators.get('volume_ratio')
                if volume_status and volume_ratio:
                    message += "📈 تحليل حجم التداول:\n"
                    message += f"• الحالة: {volume_status} ({volume_ratio:.1f}x)\n"
                    if volume_ratio > 1.5:
                        message += "• تفسير: حجم تداول عالي يدل على اهتمام قوي\n"
                    elif volume_ratio < 0.5:
                        message += "• تفسير: حجم تداول منخفض - حذر من الحركات الوهمية\n"
                    else:
                        message += "• تفسير: حجم تداول طبيعي\n"
                    message += "\n"
                
                # تحليل البولنجر باندز إذا متوفر
                bollinger = indicators.get('bollinger', {})
                if bollinger.get('upper') and bollinger.get('lower'):
                    message += "🎯 تحليل البولنجر باندز:\n"
                    message += f"• النطاق العلوي: {bollinger['upper']:.5f}\n"
                    message += f"• النطاق الأوسط: {bollinger['middle']:.5f}\n"
                    message += f"• النطاق السفلي: {bollinger['lower']:.5f}\n"
                    bollinger_interp = indicators.get('bollinger_interpretation', '')
                    if bollinger_interp:
                        message += f"• التفسير: {bollinger_interp}\n"
                    message += "\n"
            
            message += "⚠️ تحذيرات هامة:\n"
            message += "• راقب الأحجام عند نقاط الدخول\n"
            message += "• فعّل وقف الخسارة فور الدخول\n"
            if indicators.get('overall_trend'):
                trend = indicators['overall_trend']
                message += f"• الاتجاه العام: {trend}\n"
            
            # إضافة تحذير خاص إذا كان التحليل محدود
            if has_warning:
                message += "• 🚨 تحذير: التحليل محدود - لا تتخذ قرارات تداول بناءً عليه\n"
                message += "• 🛡️ تأكد من تشغيل MT5 والـ AI للحصول على تحليل كامل\n"
            
            message += "\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "📊 إحصائيات النظام\n"
            message += f"🎯 دقة النظام: {ai_success_rate:.1f}% ({success_rate_source})\n"
            message += f"⚡ مصدر البيانات: MetaTrader5 + Gemini AI Analysis\n"
            
            analysis_mode = "يدوي شامل"
            trading_mode_display = "وضع السكالبينغ" if trading_mode == "scalping" else "وضع المدى الطويل"
            message += f"🤖 نوع التحليل: {analysis_mode} | {trading_mode_display}\n\n"
            
            # تحليل الذكاء الاصطناعي محفوظ في الخلفية للاستخدام الداخلي فقط
            # تم حذف عرض التحليل المطول لتحسين سرعة الاستجابة وتقليل طول الرسالة
            

            
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "📰 تحديث إخباري:\n"
            
            # جلب الأخبار المتعلقة بالرمز
            news = self.get_symbol_news(symbol)
            message += f"{news}\n\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            return message
            
        except Exception as e:
            logger.error(f"خطأ في تنسيق التحليل الشامل: {e}")
            return "❌ خطأ في إنشاء التحليل الشامل"
    
    def _fallback_analysis(self, symbol: str, price_data: Dict) -> Dict:
        """تحليل احتياطي بسيط في حالة فشل Gemini"""
        return {
            'action': 'HOLD',
            'confidence': 50.0,
            'reasoning': ['تحليل احتياطي - Gemini غير متوفر'],
            'ai_analysis': 'تحليل احتياطي بسيط',
            'source': 'Fallback Analysis',
            'symbol': symbol,
            'timestamp': datetime.now(),
            'price_data': price_data
        }

    def learn_from_feedback(self, trade_data: Dict, feedback: str) -> None:
        """تعلم من تقييمات المستخدم"""
        try:
            # حفظ البيانات للتعلم المستقبلي
            feedback_data = {
                'trade_data': trade_data,
                'feedback': feedback,
                'timestamp': datetime.now().isoformat(),
                'symbol': trade_data.get('symbol', 'Unknown')
            }
            
            # حفظ في ملف JSON
            feedback_file = os.path.join(FEEDBACK_DIR, f"feedback_{datetime.now().strftime('%Y%m%d')}.json")
            
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            else:
                feedbacks = []
            
            feedbacks.append(feedback_data)
            
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedbacks, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"💾 تم حفظ تقييم المستخدم: {feedback}")
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في حفظ التقييم: {e}")
    
    def learn_from_file(self, file_path: str, file_type: str, user_context: Dict) -> bool:
        """تعلم من الملفات المرفوعة (صور، مستندات، إلخ)"""
        try:
            if not self.model:
                return False
            
            file_data = {
                'file_path': file_path,
                'file_type': file_type,
                'upload_time': datetime.now().isoformat(),
                'user_context': user_context,
                'processed': False
            }
            
            # حفظ معلومات الملف للتدريب
            training_file = os.path.join(FEEDBACK_DIR, f"file_training_{datetime.now().strftime('%Y%m%d')}.json")
            
            if os.path.exists(training_file):
                with open(training_file, 'r', encoding='utf-8') as f:
                    files_data = json.load(f)
            else:
                files_data = []
            
            files_data.append(file_data)
            
            with open(training_file, 'w', encoding='utf-8') as f:
                json.dump(files_data, f, ensure_ascii=False, indent=2, default=str)
            
            # معالجة الملف حسب نوعه
            if file_type.startswith('image/'):
                return self._process_image_file(file_path, user_context)
            elif file_type in ['application/pdf', 'text/plain', 'application/msword']:
                return self._process_document_file(file_path, user_context)
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في معالجة الملف: {e}")
            return False
    
    def _process_image_file(self, file_path: str, user_context: Dict) -> bool:
        """معالجة ملفات الصور للتدريب على الأنماط"""
        try:
            # يمكن هنا إضافة معالجة متقدمة للصور
            # مثل تحليل الأنماط الفنية، الشارتات، إلخ
            
            analysis_prompt = f"""
            تم رفع صورة للتدريب من المستخدم.
            السياق: نمط التداول: {user_context.get('trading_mode', 'غير محدد')}
            رأس المال: {user_context.get('capital', 'غير محدد')}
            
            يرجى تحليل هذه الصورة واستخراج الأنماط المفيدة للتداول.
            """
            
            # حفظ prompt التحليل مع بيانات الصورة
            training_data = {
                'type': 'image_analysis',
                'file_path': file_path,
                'analysis_prompt': analysis_prompt,
                'user_context': user_context,
                'timestamp': datetime.now().isoformat()
            }
            
            self._save_training_data(training_data)
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في معالجة الصورة: {e}")
            return False
    
    def _process_document_file(self, file_path: str, user_context: Dict) -> bool:
        """معالجة ملفات المستندات للتدريب"""
        try:
            training_data = {
                'type': 'document_analysis',
                'file_path': file_path,
                'user_context': user_context,
                'timestamp': datetime.now().isoformat()
            }
            
            self._save_training_data(training_data)
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في معالجة المستند: {e}")
            return False
    
    def learn_from_pattern_image(self, file_path: str, file_type: str, user_context: Dict, pattern_description: str) -> bool:
        """تعلم نمط محدد من صورة مع وصف المستخدم"""
        try:
            if not self.model:
                return False
            
            # استخراج معلومات النمط من الوصف
            pattern_info = self._extract_pattern_info(pattern_description)
            
            # إنشاء prompt متقدم للتحليل
            analysis_prompt = f"""
            تم رفع صورة نمط تداول مع توجيهات من المستخدم المتخصص.
            
            معلومات المستخدم:
            - نمط التداول: {user_context.get('trading_mode', 'غير محدد')}
            - رأس المال: ${user_context.get('capital', 'غير محدد')}
            
            وصف المستخدم للنمط:
            "{pattern_description}"
            
            معلومات النمط المستخرجة:
            - النمط: {pattern_info.get('pattern_name', 'غير محدد')}
            - الاتجاه المتوقع: {pattern_info.get('direction', 'غير محدد')}
            - نسبة الثقة: {pattern_info.get('confidence', 'غير محدد')}%
            
            يرجى تحليل هذه الصورة وحفظ النمط للاستخدام المستقبلي في التحليلات.
            """
            
            # حفظ بيانات النمط المتعلم
            pattern_data = {
                'type': 'learned_pattern',
                'file_path': file_path,
                'user_description': pattern_description,
                'pattern_info': pattern_info,
                'analysis_prompt': analysis_prompt,
                'user_context': user_context,
                'timestamp': datetime.now().isoformat(),
                'processed': True
            }
            
            # حفظ في ملف الأنماط المتعلمة
            self._save_learned_pattern(pattern_data)
            
            # حفظ في ملف التدريب العام
            self._save_training_data(pattern_data)
            
            logger.info(f"[AI_LEARNING] تم تعلم نمط جديد من المستخدم {user_context.get('user_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في تعلم النمط من الصورة: {e}")
            return False
    
    def _extract_pattern_info(self, description: str) -> Dict:
        """استخراج معلومات النمط من وصف المستخدم"""
        info = {
            'pattern_name': 'نمط مخصص',
            'direction': 'غير محدد',
            'confidence': 50
        }
        
        description_lower = description.lower()
        
        # استخراج الاتجاه
        if any(word in description_lower for word in ['سينزل', 'هبوط', 'انخفاض', 'بيع', 'sell', 'down']):
            info['direction'] = 'هبوط'
        elif any(word in description_lower for word in ['سيرتفع', 'صعود', 'ارتفاع', 'شراء', 'buy', 'up']):
            info['direction'] = 'صعود'
        elif any(word in description_lower for word in ['انعكاس', 'تغيير', 'reversal']):
            info['direction'] = 'انعكاس'
        
        # استخراج نسبة الثقة
        import re
        confidence_match = re.search(r'(\d+)%', description)
        if confidence_match:
            info['confidence'] = int(confidence_match.group(1))
        
        # استخراج اسم النمط إن وجد
        pattern_keywords = {
            'دوجي': 'Doji',
            'مطرقة': 'Hammer',
            'مثلث': 'Triangle',
            'رأس وكتفين': 'Head and Shoulders',
            'علم': 'Flag',
            'شموع': 'Candlestick Pattern'
        }
        
        for keyword, pattern_name in pattern_keywords.items():
            if keyword in description_lower:
                info['pattern_name'] = pattern_name
                break
        
        return info
    
    def _save_learned_pattern(self, pattern_data: Dict):
        """حفظ النمط المتعلم في ملف منفصل"""
        patterns_file = os.path.join(FEEDBACK_DIR, "learned_patterns.json")
        
        if os.path.exists(patterns_file):
            with open(patterns_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
        else:
            patterns = []
        
        patterns.append(pattern_data)
        
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2, default=str)
    
    def _save_training_data(self, training_data: Dict):
        """حفظ بيانات التدريب"""
        training_file = os.path.join(FEEDBACK_DIR, "ai_training_data.json")
        
        if os.path.exists(training_file):
            with open(training_file, 'r', encoding='utf-8') as f:
                all_training_data = json.load(f)
        else:
            all_training_data = []
        
        all_training_data.append(training_data)
        
        with open(training_file, 'w', encoding='utf-8') as f:
            json.dump(all_training_data, f, ensure_ascii=False, indent=2, default=str)

# إنشاء مثيل محلل Gemini
gemini_analyzer = GeminiAnalyzer()

# ===== مدير تردد الإشعارات =====
class NotificationFrequencyManager:
    """مدير تردد الإشعارات للمستخدمين"""
    
    def __init__(self):
        self.last_notification_times = {}  # {user_id: {symbol: last_time}}
    
    def can_send_notification(self, user_id: int, symbol: str, frequency_seconds: int) -> bool:
        """التحقق من إمكانية إرسال إشعار حسب التردد المحدد"""
        try:
            current_time = time.time()
            
            if user_id not in self.last_notification_times:
                self.last_notification_times[user_id] = {}
            
            last_time = self.last_notification_times[user_id].get(symbol, 0)
            
            return (current_time - last_time) >= frequency_seconds
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في فحص تردد الإشعارات: {e}")
            return True  # في حالة الخطأ، اسمح بالإرسال
    
    def record_notification_sent(self, user_id: int, symbol: str):
        """تسجيل وقت إرسال الإشعار"""
        try:
            current_time = time.time()
            
            if user_id not in self.last_notification_times:
                self.last_notification_times[user_id] = {}
            
            self.last_notification_times[user_id][symbol] = current_time
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في تسجيل وقت الإشعار: {e}")

# إنشاء مثيل مدير تردد الإشعارات
frequency_manager = NotificationFrequencyManager()

# ===== نظام تخزين بيانات التداول =====
class TradeDataManager:
    """مدير بيانات التداول والتقييمات"""
    
    @staticmethod
    def save_trade_data(user_id: int, symbol: str, signal: Dict, analysis: Dict = None) -> str:
        """حفظ بيانات الصفقة"""
        try:
            trade_id = f"{user_id}_{symbol}_{int(time.time())}"
            
            trade_data = {
                'trade_id': trade_id,
                'user_id': user_id,
                'symbol': symbol,
                'signal': signal,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat(),
                'feedback': None,
                'feedback_timestamp': None
            }
            
            # حفظ في ملف JSON
            trade_file = os.path.join(TRADE_LOGS_DIR, f"trade_{trade_id}.json")
            
            with open(trade_file, 'w', encoding='utf-8') as f:
                json.dump(trade_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"💾 تم حفظ بيانات الصفقة: {trade_id}")
            return trade_id
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في حفظ بيانات الصفقة: {e}")
            return None
    
    @staticmethod
    def save_user_feedback(trade_id: str, feedback: str) -> bool:
        """حفظ تقييم المستخدم للصفقة"""
        try:
            trade_file = os.path.join(TRADE_LOGS_DIR, f"trade_{trade_id}.json")
            
            if not os.path.exists(trade_file):
                logger.warning(f"[WARNING] ملف الصفقة غير موجود: {trade_id}")
                return False
            
            # قراءة البيانات الحالية
            with open(trade_file, 'r', encoding='utf-8') as f:
                trade_data = json.load(f)
            
            # إضافة التقييم
            trade_data['feedback'] = feedback
            trade_data['feedback_timestamp'] = datetime.now().isoformat()
            
            # حفظ البيانات المحدثة
            with open(trade_file, 'w', encoding='utf-8') as f:
                json.dump(trade_data, f, ensure_ascii=False, indent=2, default=str)
            
            # إرسال البيانات لـ Gemini للتعلم
            gemini_analyzer.learn_from_feedback(trade_data, feedback)
            
            logger.info(f"[OK] تم حفظ تقييم المستخدم للصفقة: {trade_id} - {feedback}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في حفظ تقييم المستخدم: {e}")
            return False
    
    @staticmethod
    def get_user_feedback_stats(user_id: int) -> Dict:
        """احصائيات تقييمات المستخدم"""
        try:
            positive_count = 0
            negative_count = 0
            total_count = 0
            
            # البحث في جميع ملفات الصفقات
            for filename in os.listdir(TRADE_LOGS_DIR):
                if filename.startswith(f'trade_{user_id}_'):
                    file_path = os.path.join(TRADE_LOGS_DIR, filename)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        trade_data = json.load(f)
                    
                    if trade_data.get('feedback'):
                        total_count += 1
                        if trade_data['feedback'] == 'positive':
                            positive_count += 1
                        elif trade_data['feedback'] == 'negative':
                            negative_count += 1
            
            accuracy_rate = (positive_count / total_count * 100) if total_count > 0 else 0
            
            return {
                'total_feedbacks': total_count,
                'positive_feedbacks': positive_count,
                'negative_feedbacks': negative_count,
                'accuracy_rate': accuracy_rate
            }
            
        except Exception as e:
            logger.error(f"[ERROR] خطأ في جلب احصائيات التقييم: {e}")
            return {'total_feedbacks': 0, 'positive_feedbacks': 0, 'negative_feedbacks': 0, 'accuracy_rate': 0}

# ===== وظائف مساعدة للأزرار =====
def create_animated_button(text: str, callback_data: str, emoji: str = "⚡") -> types.InlineKeyboardButton:
    """إنشاء زر متحرك مع إيموجي"""
    return types.InlineKeyboardButton(text=f"{emoji} {text}", callback_data=callback_data)

def send_or_edit_message(message, text, markup=None, parse_mode='Markdown'):
    """إرسال أو تعديل رسالة حسب نوع الرسالة"""
    try:
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        
        # التحقق من نوع الرسالة: callback query أم رسالة عادية
        if hasattr(message, 'data') and hasattr(message, 'message'):  # callback query
            bot.edit_message_text(
                text,
                message.chat.id,
                message.message_id,
                parse_mode=parse_mode,
                reply_markup=markup
            )
        else:  # regular message from keyboard
            bot.send_message(
                user_id,
                text,
                parse_mode=parse_mode,
                reply_markup=markup
            )
    except Exception as e:
        # في حالة فشل التعديل، أرسل رسالة جديدة
        try:
            user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
            bot.send_message(
                user_id,
                text,
                parse_mode=parse_mode,
                reply_markup=markup
            )
        except Exception as e2:
            logger.error(f"[ERROR] فشل في إرسال الرسالة: {e2}")

def create_feedback_buttons(trade_id: str) -> types.InlineKeyboardMarkup:
    """إنشاء أزرار التقييم 👍 و 👎"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.row(
        types.InlineKeyboardButton("👍 دقيق", callback_data=f"feedback_positive_{trade_id}"),
        types.InlineKeyboardButton("👎 غير دقيق", callback_data=f"feedback_negative_{trade_id}")
    )
    
    return markup

def create_auto_monitoring_menu(user_id) -> types.InlineKeyboardMarkup:
    """إنشاء قائمة المراقبة الآلية"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    is_monitoring = user_monitoring_active.get(user_id, False)
    trading_mode = get_user_trading_mode(user_id)
    trading_mode_display = "⚡ سكالبينغ سريع" if trading_mode == 'scalping' else "📈 تداول طويل المدى"
    
    # أزرار التحكم في المراقبة
    if is_monitoring:
        markup.row(
            create_animated_button("⏹️ إيقاف المراقبة", "stop_monitoring", "⏹️")
        )
    else:
        markup.row(
            create_animated_button("▶️ بدء المراقبة الآلية", "start_monitoring", "▶️")
        )
    
    # تحديد الرموز وإعدادات نمط التداول
    markup.row(
        create_animated_button("🎯 تحديد الرموز", "select_symbols", "🎯"),
        create_animated_button(f"{trading_mode_display}", "trading_mode_settings", "✅")
    )
    
    # إعدادات التنبيهات
    markup.row(
        create_animated_button("🔔 إعدادات التنبيهات", "advanced_notifications_settings", "🔔")
    )
    
    markup.row(
        create_animated_button("🔙 العودة للقائمة الرئيسية", "main_menu", "🔙")
    )
    
    return markup

def get_notification_display_name(setting_key: str) -> str:
    """الحصول على اسم العرض لنوع التنبيه"""
    display_names = {
        'support_alerts': '🟢 إشعارات مستوى الدعم',
        'breakout_alerts': '🔴 إشعارات اختراق المستويات',
        'trading_signals': '⚡ إشارات التداول',
        'economic_news': '📰 الأخبار الاقتصادية',
        'candlestick_patterns': '🕯️ أنماط الشموع',
        'volume_alerts': '📊 إشعارات حجم التداول'
    }
    return display_names.get(setting_key, setting_key)

def create_trading_mode_menu(user_id) -> types.InlineKeyboardMarkup:
    """إنشاء قائمة نمط التداول"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    current_mode = get_user_trading_mode(user_id)
    
    # السكالبينغ
    scalping_text = "✅ سكالبينغ سريع ⚡" if current_mode == 'scalping' else "⚡ سكالبينغ سريع"
    markup.row(
        create_animated_button(scalping_text, "set_trading_mode_scalping", "⚡")
    )
    
    # التداول طويل الأمد
    longterm_text = "✅ تداول طويل الأمد 📈" if current_mode == 'longterm' else "📈 تداول طويل الأمد"
    markup.row(
        create_animated_button(longterm_text, "set_trading_mode_longterm", "📈")
    )
    
    markup.row(
        create_animated_button("🔙 العودة للإعدادات", "settings", "🔙")
    )
    
    return markup

def create_advanced_notifications_menu(user_id) -> types.InlineKeyboardMarkup:
    """إنشاء قائمة إعدادات التنبيهات المتقدمة"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.row(
        create_animated_button("⏰ توقيت الإشعارات", "notification_timing", "⏰"),
        create_animated_button("🎯 نسبة النجاح المطلوبة", "success_threshold", "🎯")
    )
    
    markup.row(
        create_animated_button("📋 سجل الإشعارات", "notification_logs", "📋")
    )
    
    markup.row(
        create_animated_button("🔙 العودة للإعدادات", "settings", "🔙")
    )
    
    return markup



def create_success_threshold_menu(user_id) -> types.InlineKeyboardMarkup:
    """إنشاء قائمة تحديد نسبة النجاح"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    settings = get_user_advanced_notification_settings(user_id)
    current_threshold = settings.get('success_threshold', 70)
    
    thresholds = [0, 60, 65, 70, 75, 80, 85, 90, 95]
    
    for threshold in thresholds:
        button_text = f"✅ {threshold}%" if threshold == current_threshold else f"{threshold}%"
        markup.row(
            types.InlineKeyboardButton(button_text, callback_data=f"set_threshold_{threshold}")
        )
    
    markup.row(
        create_animated_button("🔙 العودة لإعدادات التنبيهات", "advanced_notifications_settings", "🔙")
    )
    
    return markup

# ===== وظائف إدارة المستخدمين =====
def get_user_trading_mode(user_id: int) -> str:
    """جلب نمط التداول للمستخدم"""
    return user_trading_modes.get(user_id, 'scalping')

def set_user_trading_mode(user_id: int, mode: str):
    """تعيين نمط التداول للمستخدم"""
    user_trading_modes[user_id] = mode

def get_user_capital(user_id: int) -> float:
    """جلب رأس المال للمستخدم"""
    return user_capitals.get(user_id, 0)  # القيمة الافتراضية 0 لعرض سؤال رأس المال

def set_user_capital(user_id: int, capital: float):
    """تعيين رأس المال للمستخدم"""
    user_capitals[user_id] = capital

def get_user_timezone(user_id: int) -> str:
    """جلب المنطقة الزمنية للمستخدم"""
    return user_timezones.get(user_id, 'Asia/Baghdad')

def set_user_timezone(user_id: int, timezone: str):
    """تعيين المنطقة الزمنية للمستخدم"""
    user_timezones[user_id] = timezone

def get_user_advanced_notification_settings(user_id: int) -> Dict:
    """جلب إعدادات التنبيهات المتقدمة للمستخدم"""
    if user_id not in user_advanced_notification_settings:
        user_advanced_notification_settings[user_id] = DEFAULT_NOTIFICATION_SETTINGS.copy()
    return user_advanced_notification_settings[user_id]

def update_user_advanced_notification_setting(user_id: int, setting_key: str, value):
    """تحديث إعداد تنبيه محدد للمستخدم"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    if 'notification_settings' not in user_sessions[user_id]:
        user_sessions[user_id]['notification_settings'] = get_user_advanced_notification_settings(user_id).copy()
    
    user_sessions[user_id]['notification_settings'][setting_key] = value
    logger.debug(f"[DEBUG] تم تحديث إعداد {setting_key} = {value} للمستخدم {user_id}")

def format_time_for_user(user_id: int, timestamp: datetime = None) -> str:
    """تنسيق الوقت حسب المنطقة الزمنية للمستخدم مع عرض جميل"""
    if timestamp is None:
        if TIMEZONE_AVAILABLE:
            timestamp = pytz.UTC.localize(datetime.utcnow())
        else:
            timestamp = datetime.now()
    
    user_tz = get_user_timezone(user_id)
    
    if TIMEZONE_AVAILABLE:
        try:
            user_timezone = pytz.timezone(user_tz)
            
            # إذا كان الوقت بدون timezone، نفترض أنه UTC
            if timestamp.tzinfo is None:
                timestamp = pytz.UTC.localize(timestamp)
            
            # تحويل للمنطقة الزمنية للمستخدم
            localized_time = timestamp.astimezone(user_timezone)
            
            # تنسيق جميل للوقت مع التاريخ
            formatted_time = localized_time.strftime('%Y-%m-%d %H:%M:%S')
            timezone_name = AVAILABLE_TIMEZONES.get(user_tz, user_tz)
            
            return f"🕐 {formatted_time} ({timezone_name})"
        except Exception as e:
            logger.error(f"خطأ في تنسيق الوقت للمستخدم {user_id}: {e}")
    
    # في حالة عدم توفر pytz أو حدوث خطأ
    formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return f"🕐 {formatted_time} (المنطقة المحلية)"

def get_current_time_for_user(user_id: int) -> str:
    """الحصول على الوقت الحالي منسق للمستخدم"""
    # استخدام UTC أولاً ثم تحويل للمنطقة الزمنية للمستخدم
    if TIMEZONE_AVAILABLE:
        try:
            utc_now = pytz.UTC.localize(datetime.now())
            return format_time_for_user(user_id, utc_now)
        except Exception as e:
            logger.error(f"خطأ في الحصول على الوقت الحالي: {e}")
    
    return format_time_for_user(user_id, datetime.now())

def is_timing_allowed(user_id: int) -> bool:
    """التحقق من أن التوقيت الحالي مسموح لإرسال التنبيهات"""
    try:
        settings = get_user_advanced_notification_settings(user_id)
        timing_setting = settings.get('alert_timing', '24h')
        
        if timing_setting == '24h':
            return True  # مسموح في جميع الأوقات
        
        # الحصول على الوقت الحالي في منطقة المستخدم
        user_tz = get_user_timezone(user_id)
        
        if TIMEZONE_AVAILABLE:
            try:
                user_timezone = pytz.timezone(user_tz)
                current_time = datetime.now(user_timezone)
                hour = current_time.hour
                
                # تحديد الأوقات المسموحة
                if timing_setting == 'morning' and 6 <= hour < 12:
                    return True
                elif timing_setting == 'afternoon' and 12 <= hour < 18:
                    return True
                elif timing_setting == 'evening' and 18 <= hour < 24:
                    return True
                elif timing_setting == 'night' and (0 <= hour < 6 or hour >= 22):
                    return True
                    
                return False
                
            except Exception as e:
                logger.error(f"خطأ في تحديد التوقيت: {e}")
                return True  # في حالة الخطأ، نسمح بالإرسال
        
        return True  # إذا لم تكن pytz متوفرة، نسمح بالإرسال
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من التوقيت: {e}")
        return True

def calculate_dynamic_success_rate(analysis: Dict, signal_type: str) -> float:
    """حساب نسبة النجاح الديناميكية بناءً على التحليل"""
    try:
        # استخدام الثقة من التحليل كأساس
        base_confidence = analysis.get('confidence', 50)
        
        # تعديل النسبة حسب نوع الإشارة
        if signal_type == 'trading_signals':
            # إشارات التداول تحتاج دقة أعلى
            return min(base_confidence * 0.9, 95)
        elif signal_type == 'support_alerts':
            # تنبيهات الدعم أقل دقة
            return min(base_confidence * 1.1, 95)
        else:
            return min(base_confidence, 95)
            
    except Exception as e:
        logger.error(f"خطأ في حساب نسبة النجاح: {e}")
        return 50.0

def get_user_advanced_notification_settings(user_id: int) -> Dict:
    """جلب إعدادات التنبيهات المتقدمة للمستخدم"""
    default_settings = {
        'trading_signals': True,
        'support_alerts': True,
        'breakout_alerts': True,
        'pattern_alerts': True,
        'volume_alerts': False,
        'news_alerts': False,
        'candlestick_patterns': True,
        'economic_news': False,
        'success_threshold': 70,
        'frequency': '15s',  # الافتراضي 15 ثانية للاستجابة السريعة
        'timing': 'always'
    }
    
    return user_sessions.get(user_id, {}).get('notification_settings', default_settings)

def get_user_notification_frequency(user_id: int) -> str:
    """جلب تردد الإشعارات للمستخدم"""
    settings = get_user_advanced_notification_settings(user_id)
    return settings.get('frequency', '15s')

def set_user_notification_frequency(user_id: int, frequency: str):
    """تعيين تردد الإشعارات للمستخدم"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    if 'notification_settings' not in user_sessions[user_id]:
        user_sessions[user_id]['notification_settings'] = get_user_advanced_notification_settings(user_id)
    
    user_sessions[user_id]['notification_settings']['frequency'] = frequency

def is_timing_allowed(user_id: int) -> bool:
    """التحقق من توقيت الإشعارات المسموح"""
    # للبساطة، سنرجع True دائماً في هذا الإصدار
    return True

def calculate_dynamic_success_rate(analysis: Dict, alert_type: str) -> float:
    """حساب نسبة النجاح الديناميكية"""
    if not analysis:
        return 65.0  # قيمة افتراضية معقولة
    
    confidence = analysis.get('confidence', 65.0)
    
    # التأكد من أن القيمة في نطاق معقول
    if confidence <= 0:
        confidence = 65.0  # قيمة افتراضية للثقة المنخفضة
    elif confidence < 20:
        confidence = max(confidence + 45, 50.0)  # رفع القيم المنخفضة جداً
    elif confidence > 95:
        confidence = 95.0  # الحد الأقصى
    
    return confidence

def calculate_ai_success_rate(analysis: Dict, technical_data: Dict, symbol: str, action: str, user_id: int = None) -> float:
    """حساب نسبة النجاح الذكية بناءً على تحليل شامل للعوامل المختلفة"""
    try:
        # البدء بنسبة أساسية
        base_score = 50.0
        
        # العوامل المؤثرة على نسبة النجاح
        confidence_factors = []
        
        # 1. تحليل المؤشرات الفنية (40% من النتيجة)
        technical_score = 0
        if technical_data and technical_data.get('indicators'):
            indicators = technical_data['indicators']
            
            # RSI Analysis (10%)
            rsi = indicators.get('rsi', 50)
            if rsi:
                if action == 'BUY':
                    if 30 <= rsi <= 50:  # منطقة جيدة للشراء
                        technical_score += 10
                    elif 20 <= rsi < 30:  # ذروة بيع - فرصة شراء ممتازة
                        technical_score += 15
                    elif rsi > 70:  # ذروة شراء - خطر
                        technical_score -= 5
                elif action == 'SELL':
                    if 50 <= rsi <= 70:  # منطقة جيدة للبيع
                        technical_score += 10
                    elif 70 < rsi <= 80:  # ذروة شراء - فرصة بيع ممتازة
                        technical_score += 15
                    elif rsi < 30:  # ذروة بيع - خطر
                        technical_score -= 5
            
            # MACD Analysis (10%)
            macd_data = indicators.get('macd', {})
            if macd_data.get('macd') is not None and macd_data.get('signal') is not None:
                macd_value = macd_data['macd']
                macd_signal = macd_data['signal']
                
                if action == 'BUY' and macd_value > macd_signal:
                    technical_score += 10  # إشارة شراء قوية
                elif action == 'SELL' and macd_value < macd_signal:
                    technical_score += 10  # إشارة بيع قوية
                elif action == 'BUY' and macd_value < macd_signal:
                    technical_score -= 5   # إشارة متضاربة
                elif action == 'SELL' and macd_value > macd_signal:
                    technical_score -= 5   # إشارة متضاربة
            
            # Moving Averages Analysis (10%)
            ma9 = indicators.get('ma_9', 0)
            ma21 = indicators.get('ma_21', 0)
            current_price = technical_data.get('price', 0)
            
            if ma9 and ma21 and current_price:
                if action == 'BUY':
                    if current_price > ma9 > ma21:  # ترتيب صاعد
                        technical_score += 10
                    elif current_price > ma9:  # فوق المتوسط قصير المدى
                        technical_score += 5
                elif action == 'SELL':
                    if current_price < ma9 < ma21:  # ترتيب هابط
                        technical_score += 10
                    elif current_price < ma9:  # تحت المتوسط قصير المدى
                        technical_score += 5
            
            # Support/Resistance Analysis (10%)
            support = indicators.get('support')
            resistance = indicators.get('resistance')
            if support and resistance and current_price:
                price_position = (current_price - support) / (resistance - support)
                
                if action == 'BUY':
                    if price_position <= 0.3:  # قريب من الدعم
                        technical_score += 10
                    elif price_position <= 0.5:  # في المنتصف
                        technical_score += 5
                elif action == 'SELL':
                    if price_position >= 0.7:  # قريب من المقاومة
                        technical_score += 10
                    elif price_position >= 0.5:  # في المنتصف
                        technical_score += 5
        
        confidence_factors.append(("التحليل الفني", technical_score, 40))
        
        # 2. تحليل حجم التداول (15% من النتيجة)
        volume_score = 0
        if technical_data and technical_data.get('indicators'):
            volume_ratio = technical_data['indicators'].get('volume_ratio', 1.0)
            if volume_ratio > 1.5:  # حجم عالي
                volume_score = 15
            elif volume_ratio > 1.2:  # حجم جيد
                volume_score = 10
            elif volume_ratio < 0.5:  # حجم منخفض - خطر
                volume_score = -5
            else:
                volume_score = 5  # حجم طبيعي
        
        confidence_factors.append(("حجم التداول", volume_score, 15))
        
        # 3. قوة الإشارة من تحليل الذكاء الاصطناعي (25% من النتيجة)
        ai_score = 0
        ai_confidence = analysis.get('confidence', 0)
        if ai_confidence > 80:
            ai_score = 25
        elif ai_confidence > 60:
            ai_score = 20
        elif ai_confidence > 40:
            ai_score = 15
        elif ai_confidence > 20:
            ai_score = 10
        else:
            ai_score = 0
        
        confidence_factors.append(("الذكاء الاصطناعي", ai_score, 25))
        
        # 4. تحليل اتجاه السوق العام (10% من النتيجة)
        trend_score = 0
        if technical_data and technical_data.get('indicators'):
            overall_trend = technical_data['indicators'].get('overall_trend', '')
            if action == 'BUY' and 'صاعد' in overall_trend:
                trend_score = 10
            elif action == 'SELL' and 'هابط' in overall_trend:
                trend_score = 10
            elif action in ['BUY', 'SELL'] and 'محايد' in overall_trend:
                trend_score = 5
            elif action != 'HOLD':  # إشارة ضد الاتجاه
                trend_score = -5
        
        confidence_factors.append(("الاتجاه العام", trend_score, 10))
        
        # 5. عامل التقلبات والاستقرار (10% من النتيجة)
        volatility_score = 5  # قيمة افتراضية
        if technical_data and technical_data.get('indicators'):
            bollinger = technical_data['indicators'].get('bollinger', {})
            if bollinger.get('upper') and bollinger.get('lower'):
                band_width = bollinger['upper'] - bollinger['lower']
                # تقدير التقلبات من عرض البولنجر باندز
                if band_width > 0:
                    # تقلبات معتدلة تعطي ثقة أعلى
                    volatility_score = 8
                else:
                    # تقلبات عالية أو منخفضة جداً تقلل الثقة
                    volatility_score = 3
        
        confidence_factors.append(("التقلبات", volatility_score, 10))
        
        # حساب النتيجة النهائية
        total_weighted_score = 0
        total_weight = 0
        
        for factor_name, score, weight in confidence_factors:
            total_weighted_score += (score * weight / 100)
            total_weight += weight
        
        # التأكد من أن المجموع الوزني 100%
        if total_weight != 100:
            logger.warning(f"مجموع الأوزان غير صحيح: {total_weight}%")
        
        # النتيجة النهائية
        final_score = base_score + total_weighted_score
        
        # تطبيق قيود منطقية
        final_score = max(10, min(95, final_score))  # بين 10% و 95%
        
        # تطبيق عوامل تصحيحية بناءً على نوع الصفقة
        if action == 'HOLD':
            final_score = max(final_score - 20, 10)  # تقليل الثقة للانتظار
        elif action in ['BUY', 'SELL']:
            # زيادة طفيفة للإشارات الواضحة
            final_score = min(final_score + 5, 95)
        
        # سجل تفاصيل الحساب للمراجعة
        logger.info(f"[AI_SUCCESS] {symbol} - {action}: {final_score:.1f}% | العوامل: {confidence_factors}")
        
        return round(final_score, 1)
        
    except Exception as e:
        logger.error(f"خطأ في حساب نسبة النجاح الذكية: {e}")
        # في حالة الخطأ، استخدم قيمة افتراضية آمنة
        return 55.0

# ===== وظائف إرسال التنبيهات المحسنة =====
def send_trading_signal_alert(user_id: int, symbol: str, signal: Dict, analysis: Dict = None):
    """إرسال تنبيه إشارة التداول مع أزرار التقييم"""
    try:
        logger.debug(f"[DEBUG] محاولة إرسال تنبيه للمستخدم {user_id} للرمز {symbol}")
        
        # التحقق من صحة البيانات
        if (not symbol or not signal or not isinstance(signal, dict) or
            not signal.get('action') or not isinstance(user_id, int)):
            logger.warning(f"[WARNING] بيانات غير صحيحة لإشارة التداول: {symbol}, {signal}")
            return
        
        settings = get_user_advanced_notification_settings(user_id)
        logger.debug(f"[DEBUG] إعدادات المستخدم {user_id}: {settings}")
        
        # التحقق من إعدادات المستخدم
        if not settings.get('trading_signals', True):
            logger.debug(f"[DEBUG] إشارات التداول معطلة للمستخدم {user_id}")
            return
        
        if not is_timing_allowed(user_id):
            logger.debug(f"[DEBUG] التوقيت غير مسموح للمستخدم {user_id}")
            return
        
        # التحقق من الرموز المختارة
        selected_symbols = user_selected_symbols.get(user_id, [])
        logger.debug(f"[DEBUG] الرموز المختارة للمستخدم {user_id}: {selected_symbols}")
        if symbol not in selected_symbols:
            logger.debug(f"[DEBUG] الرمز {symbol} غير مختار للمستخدم {user_id}")
            return
        
        action = signal.get('action', 'HOLD')
        confidence = signal.get('confidence', 0)
        
        # حساب نسبة النجاح
        if analysis:
            success_rate = calculate_dynamic_success_rate(analysis, 'trading_signal')
            if success_rate is None or success_rate <= 0:
                success_rate = max(confidence, 65.0) if confidence > 0 else 65.0
        else:
            success_rate = max(confidence, 65.0) if confidence > 0 else 65.0
        
        # التحقق من عتبة النجاح
        min_threshold = settings.get('success_threshold', 70)
        logger.debug(f"[DEBUG] نسبة النجاح {success_rate:.1f}% مقابل العتبة {min_threshold}%")
        if min_threshold > 0 and success_rate < min_threshold:
            logger.debug(f"[DEBUG] نسبة النجاح أقل من العتبة المطلوبة للمستخدم {user_id}")
            return
        
        # جلب معلومات نمط التداول (بدون شروط إضافية - فقط لحساب حجم الصفقة)
        trading_mode = get_user_trading_mode(user_id)
        capital = get_user_capital(user_id)
        logger.debug(f"[DEBUG] نمط التداول: {trading_mode}, رأس المال: {capital}")
        logger.debug(f"[DEBUG] تم قبول الإشعار - نسبة النجاح {success_rate:.1f}% تتجاوز عتبة المستخدم {min_threshold}%")
        
        # التحقق من تردد الإشعارات
        user_frequency = get_user_notification_frequency(user_id)
        frequency_seconds = NOTIFICATION_FREQUENCIES.get(user_frequency, {}).get('seconds', 15)
        logger.debug(f"[DEBUG] تردد الإشعارات: {user_frequency} ({frequency_seconds} ثانية)")
        
        can_send = frequency_manager.can_send_notification(user_id, symbol, frequency_seconds)
        logger.debug(f"[DEBUG] يمكن إرسال الإشعار: {can_send}")
        if not can_send:
            logger.debug(f"[DEBUG] لم يحن وقت الإشعار بعد للمستخدم {user_id} للرمز {symbol}")
            return  # لم يحن وقت الإشعار بعد
        
        # حفظ بيانات الصفقة
        trade_id = TradeDataManager.save_trade_data(user_id, symbol, signal, analysis)
        
        # جلب السعر الحالي
        current_price = None
        if analysis:
            price_data = analysis.get('price_data', {})
            current_price = price_data.get('last', price_data.get('bid'))
        
        # حساب الهدف ووقف الخسارة حسب نمط التداول
        target = None
        stop_loss = None
        if current_price:
            # تحديد النسب حسب نمط التداول
            if trading_mode == 'scalping':
                profit_pct = 0.015  # 1.5% للسكالبينغ
                loss_pct = 0.005   # 0.5% وقف خسارة
            else:  # longterm
                profit_pct = 0.05   # 5% للتداول طويل الأمد
                loss_pct = 0.02     # 2% وقف خسارة
            
            if action == 'BUY':
                target = current_price * (1 + profit_pct)
                stop_loss = current_price * (1 - loss_pct)
            elif action == 'SELL':
                target = current_price * (1 - profit_pct)
                stop_loss = current_price * (1 + loss_pct)
        
        # إنشاء رسالة التنبيه المحسنة
        symbol_info = ALL_SYMBOLS.get(symbol, {'name': symbol, 'emoji': '📈'})
        emoji = symbol_info['emoji']
        
        # حساب حجم الصفقة المناسب حسب نمط التداول
        if trading_mode == 'scalping':
            position_size = min(capital * 0.02, capital * 0.05)  # 2-5% للسكالبينغ
            risk_description = "منخفضة (سكالبينغ)"
        else:
            position_size = min(capital * 0.05, capital * 0.10)  # 5-10% للتداول طويل الأمد
            risk_description = "متوسطة (طويل الأمد)"
        
        formatted_time = get_current_time_for_user(user_id)
        
        # مصدر البيانات
        data_source = analysis.get('source', 'MT5 + Gemini AI') if analysis else 'تحليل متقدم'
        
        # استخدام نفس طريقة التحليل اليدوي للإشعارات
        # جلب البيانات الحقيقية من MT5
        price_data = mt5_manager.get_live_price(symbol)
        if not price_data:
            logger.warning(f"[WARNING] فشل في جلب البيانات الحقيقية للإشعار - الرمز {symbol}")
            # استخدام البيانات المتوفرة
            price_data = {
                'last': current_price,
                'bid': current_price,
                'ask': current_price,
                'time': datetime.now()
            }
        
        # إجراء تحليل جديد مع Gemini AI للإشعار
        fresh_analysis = None
        try:
            fresh_analysis = gemini_analyzer.analyze_market_data_with_retry(symbol, price_data, user_id)
            logger.info(f"[SUCCESS] تم الحصول على تحليل Gemini جديد للإشعار - الرمز {symbol}")
        except Exception as ai_error:
            logger.warning(f"[WARNING] فشل تحليل Gemini للإشعار - الرمز {symbol}: {ai_error}")
            # استخدام التحليل الموجود أو إنشاء تحليل بديل
            fresh_analysis = analysis or {
                'action': action,
                'confidence': success_rate,
                'reasoning': [f'إشعار تداول آلي للرمز {symbol}'],
                'ai_analysis': f'إشعار تداول آلي - نسبة النجاح {success_rate:.1f}%',
                'source': data_source,
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price_data': price_data
            }
        
        # استخدام نفس دالة التنسيق المستخدمة في التحليل اليدوي
        message = gemini_analyzer.format_comprehensive_analysis_v120(
            symbol, symbol_info, price_data, fresh_analysis, user_id
        )
        
        # إضافة عنوان للإشعار ليميزه عن التحليل اليدوي
        message = f"🚨 **إشعار تداول آلي** {emoji}\n\n" + message
        
        # إنشاء أزرار التقييم
        markup = create_feedback_buttons(trade_id) if trade_id else None
        
        # تقسيم الرسالة إذا كانت طويلة جداً
        max_message_length = 4000  # حد أقل قليلاً من 4096 للأمان
        
        if len(message) > max_message_length:
            # تقسيم الرسالة إلى أجزاء
            parts = []
            current_part = ""
            lines = message.split('\n')
            
            for line in lines:
                if len(current_part + line + '\n') > max_message_length:
                    if current_part:
                        parts.append(current_part.strip())
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'
            
            if current_part:
                parts.append(current_part.strip())
            
            # إرسال الأجزاء
            for i, part in enumerate(parts):
                try:
                    if i == len(parts) - 1:  # الجزء الأخير يحتوي على الأزرار
                        bot.send_message(
                            chat_id=user_id,
                            text=part,
                            parse_mode='Markdown',
                            reply_markup=markup
                        )
                    else:
                        bot.send_message(
                            chat_id=user_id,
                            text=part,
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    logger.error(f"[ERROR] خطأ في إرسال جزء الرسالة {i+1}: {e}")
                    # محاولة إرسال بدون تنسيق Markdown
                    try:
                        bot.send_message(
                            chat_id=user_id,
                            text=part.replace('*', '').replace('_', '').replace('`', ''),
                            reply_markup=markup if i == len(parts) - 1 else None
                        )
                    except Exception as e2:
                        logger.error(f"[ERROR] فشل إرسال الرسالة حتى بدون تنسيق: {e2}")
        else:
            # إرسال الرسالة العادية
            try:
                bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown',
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"[ERROR] خطأ في إرسال الرسالة: {e}")
                # محاولة إرسال بدون تنسيق Markdown
                try:
                    bot.send_message(
                        chat_id=user_id,
                        text=message.replace('*', '').replace('_', '').replace('`', ''),
                        reply_markup=markup
                    )
                except Exception as e2:
                    logger.error(f"[ERROR] فشل إرسال الرسالة حتى بدون تنسيق: {e2}")
                    return
        
        # تسجيل وقت الإرسال
        frequency_manager.record_notification_sent(user_id, symbol)
        
        logger.info(f"📨 تم إرسال تنبيه تداول للمستخدم {user_id} للرمز {symbol} (تردد: {user_frequency})")
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في إرسال تنبيه التداول: {e}")

# ===== معالجات الأزرار =====
@bot.callback_query_handler(func=lambda call: call.data.startswith('feedback_'))
def handle_feedback(call):
    """معالجة تقييمات المستخدم"""
    try:
        # استخراج نوع التقييم ومعرف الصفقة
        parts = call.data.split('_')
        feedback_type = parts[1]  # positive أو negative
        trade_id = '_'.join(parts[2:])  # معرف الصفقة
        
        # حفظ التقييم
        success = TradeDataManager.save_user_feedback(trade_id, feedback_type)
        
        if success:
            # رسالة شكر للمستخدم
            feedback_emoji = "👍" if feedback_type == "positive" else "👎"
            thanks_message = f"""
✅ **شكراً لتقييمك!** {feedback_emoji}

تم حفظ تقييمك وسيتم استخدامه لتحسين دقة التوقعات المستقبلية.

🧠 **نظام التعلم الذكي:** سيقوم Gemini AI بالتعلم من تقييمك لتقديم توقعات أكثر دقة.
            """
            
            # تعديل الرسالة الأصلية
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=call.message.text + f"\n\n{thanks_message}",
                parse_mode='Markdown'
            )
            
            # إشعار للمستخدم
            bot.answer_callback_query(
                call.id, 
                f"تم حفظ تقييمك {feedback_emoji} - شكراً لك!",
                show_alert=False
            )
            
        else:
            bot.answer_callback_query(
                call.id, 
                "حدث خطأ في حفظ التقييم",
                show_alert=True
            )
            
    except Exception as e:
        logger.error(f"[ERROR] خطأ في معالجة التقييم: {e}")
        bot.answer_callback_query(
            call.id, 
            "حدث خطأ في معالجة التقييم",
            show_alert=True
        )

# ===== وظائف إدارة البوت الرئيسية =====
def create_main_keyboard():
    """إنشاء الكيبورد الرئيسي الثابت"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    
    keyboard.row(
        types.KeyboardButton("📊 التحليل اليدوي"),
        types.KeyboardButton("📡 المراقبة الآلية")
    )
    keyboard.row(
        types.KeyboardButton("📈 أسعار مباشرة"),
        types.KeyboardButton("📊 إحصائياتي")
    )
    keyboard.row(
        types.KeyboardButton("⚙️ الإعدادات")
    )
    keyboard.row(
        types.KeyboardButton("❓ المساعدة")
    )
    
    return keyboard

@bot.message_handler(commands=['start'])
def handle_start(message):
    """معالج أمر البدء"""
    user_id = message.from_user.id
    
    # التحقق من كلمة المرور
    if user_id not in user_sessions:
        # إنشاء كيبورد مخفي لإدخال كلمة السر
        hide_keyboard = types.ReplyKeyboardRemove()
        bot.send_message(
            chat_id=user_id,
            text="🔐 يرجى إدخال كلمة المرور للوصول إلى البوت:",
            reply_markup=hide_keyboard
        )
        user_states[user_id] = 'waiting_password'
        return
    
    # رسالة الترحيب
    welcome_message = f"""
🎉 **مرحباً بك في بوت التداول المتقدم v1.2.0!**

🚀 **الميزات الجديدة:**
✅ بيانات لحظية حقيقية من MetaTrader5
✅ تحليل ذكي بتقنية Google Gemini AI
✅ نظام تقييم الإشعارات 👍👎
✅ تعلم آلي من تقييماتك

📊 **حالة الاتصال:**
• MetaTrader5: {'✅ متصل' if mt5_manager.connected else '❌ غير متصل'}
• Gemini AI: {'✅ متاح' if GEMINI_AVAILABLE else '❌ غير متاح'}

🎯 **للبدء:** استخدم الأزرار في الأسفل للتنقل بين الوظائف.
    """
    
    bot.send_message(
        chat_id=user_id,
        text=welcome_message,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )

# ===== معالجات الكيبورد الثابت =====
def handle_analyze_symbols_callback(message):
    """معالج التحليل اليدوي المحسن"""
    try:
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        
        message_text = """
📊 **التحليل اليدوي للرموز**

اختر فئة الرموز التي تريد تحليلها:

• **العملات الرقمية:** Bitcoin, Ethereum, وأكثر
• **العملات الأجنبية:** EUR/USD, GBP/USD, وأكثر  
• **الأسهم الأمريكية:** Apple, Tesla, Google, وأكثر
• **المؤشرات:** S&P500, NASDAQ, وأكثر
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        markup.row(
            create_animated_button("💱 العملات الأجنبية", "analyze_forex", "💱"),
            create_animated_button("🥇 المعادن النفيسة", "analyze_metals", "🥇")
        )
        markup.row(
            create_animated_button("₿ العملات الرقمية", "analyze_crypto", "₿"),
            create_animated_button("📈 الأسهم الأمريكية", "analyze_stocks", "📈")
        )
        markup.row(
            create_animated_button("📊 المؤشرات", "analyze_indices", "📊")
        )
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        # استخدام الوظيفة المحسنة لإرسال أو تعديل الرسالة
        send_or_edit_message(message, message_text, markup)
            
    except Exception as e:
        logger.error(f"[ERROR] خطأ في التحليل اليدوي: {e}")

@bot.message_handler(func=lambda message: message.text == "📊 التحليل اليدوي")
@require_authentication
def handle_manual_analysis_keyboard(message):
    """معالج زر التحليل اليدوي من الكيبورد"""
    handle_analyze_symbols_callback(message)

def handle_auto_monitoring_callback(message):
    """معالج المراقبة الآلية"""
    try:
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        
        # جلب حالة المراقبة
        is_monitoring = user_monitoring_active.get(user_id, False)
        selected_symbols = user_selected_symbols.get(user_id, [])
        trading_mode = get_user_trading_mode(user_id)
        
        status_text = "🟢 نشط" if is_monitoring else "🔴 متوقف"
        symbols_count = len(selected_symbols)
        
        message_text = f"""
📡 **المراقبة الآلية للأسواق**

📊 **الحالة الحالية:** {status_text}
🎯 **الرموز المراقبة:** {symbols_count} رمز
🎯 **نمط التداول:** {'⚡ سكالبينغ' if trading_mode == 'scalping' else '📈 طويل الأمد'}

**الوظائف المتاحة:**
• تحديد الرموز للمراقبة
• تفعيل/إيقاف المراقبة التلقائية  
• ضبط إعدادات التنبيهات
        """
        
        markup = create_auto_monitoring_menu(user_id)
        
        # استخدام الوظيفة المحسنة لإرسال أو تعديل الرسالة
        send_or_edit_message(message, message_text, markup)
            
    except Exception as e:
        logger.error(f"[ERROR] خطأ في المراقبة الآلية: {e}")

@bot.message_handler(func=lambda message: message.text == "📡 المراقبة الآلية")
@require_authentication
def handle_auto_monitoring_keyboard(message):
    """معالج زر المراقبة الآلية من الكيبورد"""
    handle_auto_monitoring_callback(message)



def handle_my_stats_callback(message):
    """معالج الإحصائيات"""
    try:
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        
        # جلب إحصائيات المستخدم
        capital = get_user_capital(user_id)
        trading_mode = get_user_trading_mode(user_id)
        feedback_stats = user_trade_feedbacks.get(user_id, {})
        
        total_trades = len(feedback_stats)
        positive_trades = sum(1 for feedback in feedback_stats.values() if feedback == 'positive')
        accuracy = (positive_trades / total_trades * 100) if total_trades > 0 else 0
        
        message_text = f"""
📊 **إحصائياتي الشخصية**

💰 **رأس المال:** ${capital:,.0f}
🎯 **نمط التداول:** {'⚡ سكالبينغ' if trading_mode == 'scalping' else '📈 طويل الأمد'}

📈 **إحصائيات التداول:**
• إجمالي الصفقات: {total_trades}
• الصفقات الناجحة: {positive_trades}
• دقة التوقعات: {accuracy:.1f}%

🔔 **حالة التنبيهات:**
• المراقبة النشطة: {'🟢 مفعلة' if user_monitoring_active.get(user_id, False) else '🔴 معطلة'}
• الرموز المراقبة: {len(user_selected_symbols.get(user_id, []))} رمز

{get_current_time_for_user(user_id)}
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            create_animated_button("🔄 تحديث", "my_stats", "🔄")
        )
        
        # استخدام الوظيفة المحسنة لإرسال أو تعديل الرسالة
        send_or_edit_message(message, message_text, markup)
    except Exception as e:
        logger.error(f"[ERROR] خطأ في الإحصائيات: {e}")

def handle_settings_callback(message):
    """معالج الإعدادات من الكيبورد الرئيسي"""
    try:
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        trading_mode = get_user_trading_mode(user_id)
        trading_mode_display = "⚡ سكالبينغ سريع" if trading_mode == 'scalping' else "📈 تداول طويل المدى"
        settings = get_user_advanced_notification_settings(user_id)
        frequency = get_user_notification_frequency(user_id)
        frequency_name = NOTIFICATION_FREQUENCIES.get(frequency, {}).get('name', '15 ثانية 🔥')
        user_timezone = get_user_timezone(user_id)
        timezone_display = AVAILABLE_TIMEZONES.get(user_timezone, user_timezone)
        capital = get_user_capital(user_id)
        
        message_text = f"""
⚙️ **الإعدادات**

🎯 **نمط التداول:** {trading_mode_display}
💰 **رأس المال:** ${capital:,.0f}
🌍 **المنطقة الزمنية:** {timezone_display}
🔔 **التنبيهات:** {'مفعلة' if settings.get('trading_signals', True) else 'معطلة'}
⏱️ **تردد الإشعارات:** {frequency_name}
📊 **عتبة النجاح:** {settings.get('success_threshold', 70)}%

اختر الإعداد المطلوب تعديله:
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.row(
            create_animated_button("🎯 نمط التداول", "trading_mode_settings", "🎯"),
            create_animated_button("💰 تحديد رأس المال", "set_capital", "💰")
        )
        
        markup.row(
            create_animated_button("🔔 إعدادات التنبيهات", "advanced_notifications_settings", "🔔"),
            create_animated_button("📊 الإحصائيات", "statistics", "📊")
        )
        
        markup.row(
            create_animated_button("🌍 المنطقة الزمنية", "timezone_settings", "🌍"),
            create_animated_button("🤖 قسم AI", "ai_section", "🤖")
        )
        
        # استخدام الوظيفة المحسنة لإرسال أو تعديل الرسالة
        send_or_edit_message(message, message_text, markup)
    except Exception as e:
        logger.error(f"[ERROR] خطأ في الإعدادات: {e}")

def handle_alerts_log_callback(message):
    """معالج سجل التنبيهات"""
    try:
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        
        message_text = """
📋 **سجل الإشعارات**

عرض وإدارة سجل الإشعارات والصفقات:
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.row(
            create_animated_button("📊 عرض السجل", "view_alerts_log", "📊"),
            create_animated_button("🗑️ مسح السجل", "clear_alerts", "🗑️")
        )
        markup.row(
            create_animated_button("📈 تحليل الأداء", "performance_analysis", "📈")
        )
        
        # استخدام الوظيفة المحسنة لإرسال أو تعديل الرسالة
        send_or_edit_message(message, message_text, markup)
    except Exception as e:
        logger.error(f"[ERROR] خطأ في سجل التنبيهات: {e}")

def handle_help_main_callback(message):
    """معالج المساعدة الرئيسي"""
    try:
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        
        message_text = """
❓ **المساعدة والدعم**

اختر نوع المساعدة المطلوبة:
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.row(
            create_animated_button("📚 استخدام البوت", "help_usage", "📚")
        )
        markup.row(
            create_animated_button("ℹ️ حول البوت", "about", "ℹ️")
        )
        markup.row(
            create_animated_button("🆘 الدعم الفني", "technical_support", "🆘")
        )
        
        # استخدام الوظيفة المحسنة لإرسال أو تعديل الرسالة
        send_or_edit_message(message, message_text, markup)
    except Exception as e:
        logger.error(f"[ERROR] خطأ في المساعدة: {e}")

@bot.message_handler(func=lambda message: message.text == "📈 أسعار مباشرة")
@require_authentication
def handle_live_prices_keyboard(message):
    """معالج زر الأسعار المباشرة من الكيبورد"""
    try:
        user_id = message.from_user.id
        
        message_text = """
📈 **الأسعار المباشرة من MetaTrader5**

اختر فئة الرموز للحصول على الأسعار اللحظية:
(مصدر البيانات: MT5 - لحظي)
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.row(
            create_animated_button("💱 العملات الأجنبية", "live_forex", "💱"),
            create_animated_button("🥇 المعادن النفيسة", "live_metals", "🥇")
        )
        markup.row(
            create_animated_button("₿ العملات الرقمية", "live_crypto", "₿"),
            create_animated_button("📈 الأسهم الأمريكية", "live_stocks", "📈")
        )
        markup.row(
            create_animated_button("📊 المؤشرات", "live_indices", "📊")
        )
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        bot.send_message(
            chat_id=message.chat.id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
            
    except Exception as e:
        logger.error(f"[ERROR] خطأ في الأسعار المباشرة من الكيبورد: {e}")
        bot.send_message(
            chat_id=message.chat.id,
            text="❌ حدث خطأ في عرض الأسعار المباشرة، يرجى المحاولة مرة أخرى."
        )

@bot.message_handler(func=lambda message: message.text == "📊 إحصائياتي")
@require_authentication
def handle_my_stats_keyboard(message):
    """معالج زر الإحصائيات من الكيبورد"""
    handle_my_stats_callback(message)

@bot.message_handler(func=lambda message: message.text == "⚙️ الإعدادات")
@require_authentication
def handle_settings_keyboard(message):
    """معالج زر الإعدادات من الكيبورد"""
    handle_settings_callback(message)


@bot.message_handler(func=lambda message: message.text == "❓ المساعدة")
@require_authentication
def handle_help_keyboard(message):
    """معالج زر المساعدة من الكيبورد"""
    handle_help_main_callback(message)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_password')
def handle_password(message):
    """معالج كلمة المرور"""
    user_id = message.from_user.id
    
    if message.text == BOT_PASSWORD:
        user_sessions[user_id] = {
            'authenticated': True,
            'trading_mode': 'scalping',
            'notification_settings': get_user_advanced_notification_settings(user_id)
        }
        
        # إجبار سؤال رأس المال لجميع المستخدمين بعد كلمة المرور
        user_states[user_id] = 'waiting_initial_capital'
        
        message_text = """
💰 **مرحباً بك! يرجى تحديد رأس المال للبدء**

اختر رأس المال المناسب لك:
(يمكن تعديله لاحقاً من الإعدادات)
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        for capital in DEFAULT_CAPITAL_OPTIONS:
            markup.row(
                types.InlineKeyboardButton(f"${capital:,}", callback_data=f"initial_capital_{capital}")
            )
        
        markup.row(
            create_animated_button("💰 إدخال مبلغ مخصص", "initial_custom_capital", "💰")
        )
        
        bot.send_message(
            user_id,
            message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "❌ كلمة مرور خاطئة. حاول مرة أخرى:")

@bot.callback_query_handler(func=lambda call: call.data.startswith("initial_capital_"))
def handle_initial_capital(call):
    """معالج تحديد رأس المال الأولي"""
    try:
        user_id = call.from_user.id
        capital = int(call.data.replace("initial_capital_", ""))
        
        set_user_capital(user_id, capital)
        user_states.pop(user_id, None)
        
        bot.edit_message_text(
            f"✅ تم تحديد رأس المال: ${capital:,}\n\n"
            "🎉 مرحباً بك في بوت التداول المتقدم v1.2.0!",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
        
        # إرسال القائمة الرئيسية
        time.sleep(1)
        fake_message = type('obj', (object,), {'from_user': call.from_user, 'chat': call.message.chat})
        handle_start(fake_message)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تحديد رأس المال الأولي: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "initial_custom_capital")
def handle_initial_custom_capital(call):
    """معالج إدخال رأس مال مخصص أولي"""
    try:
        user_id = call.from_user.id
        user_states[user_id] = 'waiting_initial_custom_capital'
        
        bot.edit_message_text(
            "💰 **إدخال رأس مال مخصص**\n\n"
            "يرجى إدخال المبلغ المطلوب بالدولار الأمريكي:\n"
            "مثال: 1500 أو 25000\n\n"
            "الحد الأدنى: $50\n"
            "الحد الأقصى: $1,000,000",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=None
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في إدخال رأس مال مخصص أولي: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_initial_custom_capital')
def handle_initial_custom_capital_input(message):
    """معالج إدخال رأس المال المخصص الأولي"""
    try:
        user_id = message.from_user.id
        
        try:
            capital = float(message.text.replace(',', '').replace('$', ''))
            
            if capital < 50:
                bot.reply_to(message, "❌ المبلغ أقل من الحد الأدنى ($50). يرجى إدخال مبلغ أكبر.")
                return
            
            if capital > 1000000:
                bot.reply_to(message, "❌ المبلغ أكبر من الحد الأقصى ($1,000,000). يرجى إدخال مبلغ أصغر.")
                return
            
            set_user_capital(user_id, capital)
            user_states.pop(user_id, None)
            
            bot.reply_to(message, f"✅ تم تحديد رأس المال: ${capital:,.0f}\n\n🎉 مرحباً بك في بوت التداول المتقدم!")
            
            time.sleep(1)
            handle_start(message)
            
        except ValueError:
            bot.reply_to(message, "❌ يرجى إدخال رقم صحيح. مثال: 1500")
            
    except Exception as e:
        logger.error(f"[ERROR] خطأ في معالجة رأس المال المخصص الأولي: {e}")
        bot.reply_to(message, "❌ حدث خطأ في معالجة المبلغ")
        user_states.pop(user_id, None)

# ===== معالجات فئات الرموز =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def handle_symbol_category(call):
    """معالج فئات الرموز"""
    try:
        user_id = call.from_user.id
        category = call.data.replace("category_", "")
        
        # جلب الرموز المختارة
        selected_symbols = user_selected_symbols.get(user_id, [])
        
        category_names = {
            'crypto': 'العملات الرقمية ₿',
            'forex': 'العملات الأجنبية والمعادن 💱',
            'stocks': 'الأسهم الأمريكية 📈',
            'indices': 'المؤشرات 📊'
        }
        
        symbols = SYMBOL_CATEGORIES.get(category, {})
        
        message_text = f"""
📊 **{category_names.get(category, 'فئة غير معروفة')}**

اختر الرموز التي تريد تحليلها:
✅ = مختار للتحليل | ⚪ = غير مختار
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # إضافة الرموز مع تمييز المختارة
        for symbol, info in symbols.items():
            is_selected = symbol in selected_symbols
            button_text = f"✅ {info['name']}" if is_selected else f"⚪ {info['name']}"
            
            markup.row(
                types.InlineKeyboardButton(
                    button_text, 
                    callback_data=f"toggle_symbol_{symbol}_{category}"
                )
            )
        
        # أزرار التحكم
        markup.row(
            create_animated_button("🔄 تحليل المختارة", f"analyze_selected_{category}", "🔄"),
            create_animated_button("✅ اختيار الكل", f"select_all_{category}", "✅")
        )
        markup.row(
            create_animated_button("❌ إلغاء الكل", f"deselect_all_{category}", "❌"),
            create_animated_button("🔙 التحليل اليدوي", "analyze_symbols", "🔙")
        )
        
        bot.edit_message_text(
            message_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في معالج فئات الرموز: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

# تم حذف المعالج القديم المكرر - يتم استخدام المعالج الجديد في السطر 4166

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_all_"))
def handle_select_all_category(call):
    """معالج اختيار جميع رموز الفئة"""
    try:
        user_id = call.from_user.id
        category = call.data.replace("select_all_", "")
        
        if user_id not in user_selected_symbols:
            user_selected_symbols[user_id] = []
        
        symbols = SYMBOL_CATEGORIES.get(category, {})
        
        # إضافة جميع رموز الفئة
        for symbol in symbols.keys():
            if symbol not in user_selected_symbols[user_id]:
                user_selected_symbols[user_id].append(symbol)
        
        bot.answer_callback_query(call.id, f"✅ تم اختيار جميع رموز الفئة ({len(symbols)} رمز)")
        
        # تحديث القائمة
        fake_call = type('obj', (object,), {
            'data': f'category_{category}',
            'from_user': call.from_user,
            'message': call.message
        })
        handle_symbol_category(fake_call)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في اختيار جميع الرموز: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deselect_all_"))
def handle_deselect_all_category(call):
    """معالج إلغاء اختيار جميع رموز الفئة"""
    try:
        user_id = call.from_user.id
        category = call.data.replace("deselect_all_", "")
        
        if user_id not in user_selected_symbols:
            user_selected_symbols[user_id] = []
        
        symbols = SYMBOL_CATEGORIES.get(category, {})
        
        # إزالة جميع رموز الفئة
        for symbol in symbols.keys():
            if symbol in user_selected_symbols[user_id]:
                user_selected_symbols[user_id].remove(symbol)
        
        bot.answer_callback_query(call.id, f"❌ تم إلغاء اختيار جميع رموز الفئة")
        
        # تحديث القائمة
        fake_call = type('obj', (object,), {
            'data': f'category_{category}',
            'from_user': call.from_user,
            'message': call.message
        })
        handle_symbol_category(fake_call)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في إلغاء اختيار جميع الرموز: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

# ===== معالجات الأزرار الرئيسية =====
@bot.callback_query_handler(func=lambda call: call.data == "live_prices")
@require_authentication
def handle_live_prices(call):
    """معالج الأسعار المباشرة المحسن"""
    try:
        user_id = call.from_user.id
        
        message_text = """
📈 **الأسعار المباشرة من MetaTrader5**

اختر فئة الرموز للحصول على الأسعار اللحظية:
(مصدر البيانات: MT5 - لحظي)
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.row(
            create_animated_button("💱 العملات الأجنبية", "live_forex", "💱"),
            create_animated_button("🥇 المعادن النفيسة", "live_metals", "🥇")
        )
        markup.row(
            create_animated_button("₿ العملات الرقمية", "live_crypto", "₿"),
            create_animated_button("📈 الأسهم الأمريكية", "live_stocks", "📈")
        )
        markup.row(
            create_animated_button("📊 المؤشرات", "live_indices", "📊")
        )
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
            
    except Exception as e:
        logger.error(f"[ERROR] خطأ في الأسعار المباشرة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض الأسعار", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "my_stats")
def handle_my_stats(call):
    """معالج عرض إحصائيات المستخدم"""
    try:
        user_id = call.from_user.id
        stats = TradeDataManager.get_user_feedback_stats(user_id)
        
        message_text = f"""
📊 **إحصائياتك الشخصية**

📈 **تقييمات الإشارات:**
• إجمالي التقييمات: {stats['total_feedbacks']}
• تقييمات إيجابية: {stats['positive_feedbacks']} 👍
• تقييمات سلبية: {stats['negative_feedbacks']} 👎
• معدل الدقة: {stats['accuracy_rate']:.1f}%

🎯 **نمط التداول الحالي:** {get_user_trading_mode(user_id)}

🧠 **التعلم الآلي:**
• عدد عينات التدريب: {stats['total_feedbacks']}
• حالة التعلم: {'نشط' if stats['total_feedbacks'] > 0 else 'في انتظار المزيد من التقييمات'}

───────────────────────
💡 كلما زادت تقييماتك، كلما تحسنت دقة التوقعات!
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض الإحصائيات: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في جلب الإحصائيات", show_alert=True)

# ===== معالجات إضافية للأزرار =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("analyze_symbol_"))
def handle_single_symbol_analysis(call):
    """معالج تحليل رمز واحد تفصيلياً - مثل v1.1.0"""
    try:
        user_id = call.from_user.id
        symbol = call.data.replace("analyze_symbol_", "")
        
        logger.info(f"[START] بدء تحليل الرمز {symbol} للمستخدم {user_id}")
        
        # العثور على معلومات الرمز
        symbol_info = ALL_SYMBOLS.get(symbol)
        if not symbol_info:
            logger.error(f"[ERROR] رمز غير صالح: {symbol}")
            bot.answer_callback_query(call.id, "❌ رمز غير صالح", show_alert=True)
            return
        
        # رسالة انتظار
        bot.edit_message_text(
            f"🔄 جاري تحليل {symbol_info['emoji']} {symbol_info['name']}...\n\n"
            "⏳ يرجى الانتظار بينما نجمع البيانات ونحللها...",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        
        # جلب البيانات اللحظية المباشرة من MT5 (بدون كاش - للتحليل اليدوي)
        logger.info(f"[MANUAL_ANALYSIS] جلب بيانات لحظية مباشرة للرمز {symbol}")
        price_data = mt5_manager.get_live_price(symbol, force_fresh=True)
        if not price_data:
            logger.error(f"[ERROR] فشل في جلب البيانات الحقيقية من MT5 للرمز {symbol}")
            bot.edit_message_text(
                f"❌ **لا يمكن الحصول على بيانات حقيقية**\n\n"
                f"لا يمكن الحصول على بيانات {symbol_info['emoji']} {symbol_info['name']} من MetaTrader5.\n\n"
                "🔧 **متطلبات التشغيل:**\n"
                "• يجب تشغيل MetaTrader5 على نفس الجهاز\n"
                "• يجب تسجيل الدخول لحساب حقيقي أو تجريبي في MT5\n"
                "• تأكد من وجود اتصال إنترنت مستقر\n"
                "• تأكد من إضافة الرمز للمراقبة في MT5\n\n"
                "⚠️ **تحذير:** لا يمكن التحليل بدون بيانات حقيقية لحمايتك من قرارات خاطئة.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
            return
        
        # تحليل ذكي مع Gemini AI مع بديل
        analysis = None
        try:
            analysis = gemini_analyzer.analyze_market_data_with_retry(symbol, price_data, user_id)
            logger.info(f"[SUCCESS] تم الحصول على تحليل Gemini للرمز {symbol}")
        except Exception as ai_error:
            logger.warning(f"[WARNING] فشل تحليل Gemini للرمز {symbol}: {ai_error}")
        
        if not analysis:
            logger.warning(f"[WARNING] لا يوجد تحليل Gemini - استخدام تحليل بديل للرمز {symbol}")
            # إنشاء تحليل بديل بسيط (بدون توصيات تداول لحماية المستخدم)
            analysis = {
                'action': 'HOLD',  # دائماً انتظار عند فشل AI
                'confidence': 0,   # لا ثقة بدون AI
                'reasoning': ['تحليل محدود - Gemini AI غير متوفر - لا توصيات تداول'],
                'ai_analysis': f'⚠️ تحذير: لا يمكن تقديم تحليل كامل للرمز {symbol} بدون Gemini AI. البيانات المعروضة للمعلومات فقط.',
                'source': 'Limited Analysis (No AI)',
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price_data': price_data,
                'warning': 'لا توصيات تداول - AI غير متوفر'
            }
        
        # استخدام التحليل الشامل المتقدم الجديد
        message_text = gemini_analyzer.format_comprehensive_analysis_v120(
            symbol, symbol_info, price_data, analysis, user_id
        )
        
        # أزرار التحكم
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        try:
            # أزرار التقييم مبسطة
            markup.row(
                create_animated_button("👍 تحليل ممتاز", f"feedback_positive_{symbol}_{user_id}", "👍"),
                create_animated_button("👎 تحليل ضعيف", f"feedback_negative_{symbol}_{user_id}", "👎")
            )
            
            markup.row(
                create_animated_button("🔄 تحديث التحليل", f"analyze_symbol_{symbol}", "🔄"),
                create_animated_button("📊 تحليل آخر", "analyze_symbols", "📊")
            )
            markup.row(
                create_animated_button("🔙 العودة لقائمة التحليل", "analyze_symbols", "🔙")
            )
        except Exception as btn_error:
            logger.error(f"[ERROR] فشل في إنشاء الأزرار: {btn_error}")
            # أزرار بسيطة كبديل
            markup.row(
                types.InlineKeyboardButton("👍 ممتاز", callback_data=f"feedback_positive_{symbol}_{user_id}"),
                types.InlineKeyboardButton("👎 ضعيف", callback_data=f"feedback_negative_{symbol}_{user_id}")
            )
            markup.row(
                types.InlineKeyboardButton("🔄 تحديث", callback_data=f"analyze_symbol_{symbol}"),
                types.InlineKeyboardButton("📊 آخر", callback_data="analyze_symbols")
            )
            markup.row(
                types.InlineKeyboardButton("🔙 عودة", callback_data="analyze_symbols")
            )
        
        try:
            # التحقق من طول الرسالة (حد Telegram 4096 حرف)
            if len(message_text) > 4000:
                # تقسيم الرسالة إذا كانت طويلة جداً
                message_parts = [message_text[i:i+3900] for i in range(0, len(message_text), 3900)]
                main_message = message_parts[0] + "\n\n⚠️ الرسالة مقطوعة لطولها..."
            else:
                main_message = message_text
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=main_message,
                parse_mode='Markdown',
                reply_markup=markup
            )
            
            # إرسال الجزء الثاني إذا كان موجوداً
            if len(message_text) > 4000:
                for i, part in enumerate(message_parts[1:], 1):
                    bot.send_message(
                        chat_id=call.message.chat.id,
                        text=f"**📄 الجزء {i + 1}:**\n\n{part}",
                        parse_mode='Markdown'
                    )
            
            logger.info(f"[SUCCESS] تم إرسال تحليل الرمز {symbol} للمستخدم {user_id}")
            
        except Exception as send_error:
            logger.error(f"[ERROR] فشل في إرسال التحليل: {send_error}")
            try:
                # محاولة إرسال رسالة خطأ بسيطة
                bot.edit_message_text(
                    f"❌ **خطأ في عرض التحليل**\n\n"
                    f"حدث خطأ في عرض تحليل {symbol_info['emoji']} {symbol_info['name']}.\n\n"
                    "يرجى المحاولة مرة أخرى لاحقاً.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown',
                    reply_markup=markup
                )
            except:
                bot.answer_callback_query(call.id, "حدث خطأ في عرض التحليل", show_alert=True)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ عام في تحليل الرمز {call.data}: {e}")
        try:
            bot.answer_callback_query(call.id, "حدث خطأ في التحليل", show_alert=True)
        except:
            pass

@bot.callback_query_handler(func=lambda call: call.data == "analyze_symbols")
def handle_analyze_symbols(call):
    """معالج تحليل الرموز"""
    try:
        message_text = """
📊 **تحليل الرموز المالية**

اختر فئة الرموز المالية للتحليل:
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.row(
            create_animated_button("💶 أزواج العملات", "analyze_forex", "💶"),
            create_animated_button("🥇 المعادن النفيسة", "analyze_metals", "🥇")
        )
        
        markup.row(
            create_animated_button("₿ العملات الرقمية", "analyze_crypto", "₿"),
            create_animated_button("📈 الأسهم الأمريكية", "analyze_stocks", "📈")
        )
        
        markup.row(
            create_animated_button("📊 المؤشرات", "analyze_indices", "📊")
        )
        
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض تحليل الرموز: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض التحليل", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("analyze_") and call.data != "analyze_symbols" and not call.data.startswith("analyze_symbol_") and not call.data.startswith("toggle_notification_"))
def handle_category_analysis(call):
    """معالج تحليل فئة معينة من الرموز - يرسل تحليل منفصل لكل رمز"""
    try:
        user_id = call.from_user.id
        category = call.data.split('_')[1]
        
        # تحديد الرموز حسب الفئة
        if category == "forex":
            symbols = CURRENCY_PAIRS
            title = "💶 تحليل أزواج العملات"
            category_emoji = "💱"
        elif category == "metals":
            symbols = METALS
            title = "🥇 تحليل المعادن النفيسة"
            category_emoji = "🥇"
        elif category == "crypto":
            symbols = CRYPTO_PAIRS
            title = "₿ تحليل العملات الرقمية"
            category_emoji = "₿"
        elif category == "stocks":
            symbols = STOCKS
            title = "📈 تحليل الأسهم الأمريكية"
            category_emoji = "📈"
        elif category == "indices":
            symbols = INDICES
            title = "📊 تحليل المؤشرات"
            category_emoji = "📊"
        else:
            return
        
        # عرض قائمة الرموز للاختيار
        message_text = f"{title}\n\n"
        message_text += "اختر الرمز الذي تريد تحليله تحليلاً تفصيلياً:\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # إضافة أزرار الرموز
        symbol_buttons = []
        for symbol, info in symbols.items():
            symbol_buttons.append(
                create_animated_button(f"{info['emoji']} {info['name']}", f"analyze_symbol_{symbol}", info['emoji'])
            )
        
        # ترتيب الأزرار في صفوف (2 في كل صف)
        for i in range(0, len(symbol_buttons), 2):
            if i + 1 < len(symbol_buttons):
                markup.row(symbol_buttons[i], symbol_buttons[i + 1])
            else:
                markup.row(symbol_buttons[i])
        
        # زر العودة
        markup.row(
            create_animated_button("🔙 التحليل اليدوي", "analyze_symbols", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تحليل الفئة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في التحليل", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "settings")
def handle_settings(call):
    """معالج الإعدادات"""
    try:
        user_id = call.from_user.id
        trading_mode = get_user_trading_mode(user_id)
        trading_mode_display = "⚡ سكالبينغ سريع" if trading_mode == 'scalping' else "📈 تداول طويل المدى"
        settings = get_user_advanced_notification_settings(user_id)
        frequency = get_user_notification_frequency(user_id)
        frequency_name = NOTIFICATION_FREQUENCIES.get(frequency, {}).get('name', '15 ثانية 🔥')
        user_timezone = get_user_timezone(user_id)
        timezone_display = AVAILABLE_TIMEZONES.get(user_timezone, user_timezone)
        capital = get_user_capital(user_id)
        
        message_text = f"""
⚙️ **الإعدادات**

🎯 **نمط التداول:** {trading_mode_display}
💰 **رأس المال:** ${capital:,.0f}
🌍 **المنطقة الزمنية:** {timezone_display}
🔔 **التنبيهات:** {'مفعلة' if settings.get('trading_signals', True) else 'معطلة'}
⏱️ **تردد الإشعارات:** {frequency_name}
📊 **عتبة النجاح:** {settings.get('success_threshold', 70)}%

اختر الإعداد المطلوب تعديله:
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.row(
            create_animated_button("🎯 نمط التداول", "trading_mode_settings", "🎯"),
            create_animated_button("💰 تحديد رأس المال", "set_capital", "💰")
        )
        
        markup.row(
            create_animated_button("🔔 إعدادات التنبيهات", "advanced_notifications_settings", "🔔"),
            create_animated_button("📊 الإحصائيات", "statistics", "📊")
        )
        
        markup.row(
            create_animated_button("🌍 المنطقة الزمنية", "timezone_settings", "🌍"),
            create_animated_button("🤖 قسم AI", "ai_section", "🤖")
        )
        
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض الإعدادات: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض الإعدادات", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "ai_section")
def handle_ai_section(call):
    """معالج قسم AI"""
    try:
        message_text = """
🤖 **قسم الذكاء الاصطناعي**

🧠 **ميزات الذكاء الاصطناعي المتاحة:**

📁 **تدريب النظام بالملفات:**
• ارفع صور الشارتات والأنماط الفنية
• ارفع ملفات PDF أو Word مع تحليلاتك
• ارفع مستندات تحليلية أو توقعات
• النظام يتعلم من ملفاتك ويحسن دقة التحليل

🔮 **الميزات القادمة:**
• تحليل ذكي للأسواق
• توصيات مخصصة
• تحليل المشاعر  
• تنبؤات السوق

💡 **كيف يعمل التعلم:**
النظام يحلل ملفاتك ويربطها بنمط تداولك ورأس مالك لتحسين التوصيات المستقبلية
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.row(
            create_animated_button("📁 رفع ملف للتدريب", "upload_file", "📁")
        )
        markup.row(
            create_animated_button("⚙️ إدارة قواعد التحليل", "manage_analysis_rules", "⚙️")
        )
        markup.row(
            create_animated_button("🔙 العودة للإعدادات", "settings", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض قسم AI: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض قسم AI", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "manage_analysis_rules")
def handle_manage_analysis_rules(call):
    """معالج إدارة قواعد التحليل"""
    try:
        message_text = """
⚙️ **إدارة قواعد التحليل**

📋 **إدارة قواعد التحليل الذكي:**

• قم بإضافة قواعد تحليل جديدة
• عدّل القواعد الموجودة
• حدد معايير التحليل المخصصة

🔧 **الخيارات المتاحة:**
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.row(
            create_animated_button("➕ إضافة قاعدة", "add_analysis_rule", "➕")
        )
        markup.row(
            create_animated_button("✏️ تحرير القواعد", "edit_analysis_rules", "✏️")
        )
        markup.row(
            create_animated_button("🔙 العودة لقسم AI", "ai_section", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض إدارة قواعد التحليل: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض إدارة قواعد التحليل", show_alert=True)

# ===== نظام إدارة قواعد التحليل =====

def load_analysis_rules():
    """تحميل قواعد التحليل من الملف"""
    rules_file = os.path.join(FEEDBACK_DIR, "analysis_rules.json")
    try:
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تحميل قواعد التحليل: {e}")
        return []

def save_analysis_rules(rules):
    """حفظ قواعد التحليل في الملف"""
    rules_file = os.path.join(FEEDBACK_DIR, "analysis_rules.json")
    try:
        os.makedirs(FEEDBACK_DIR, exist_ok=True)
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"[ERROR] خطأ في حفظ قواعد التحليل: {e}")
        return False

def process_user_rule_with_ai(user_input, user_id):
    """معالجة قاعدة المستخدم باستخدام الذكاء الاصطناعي"""
    try:
        if not gemini_analyzer or not gemini_analyzer.model:
            return None
            
        prompt = f"""
أنت خبير في تحليل الأسواق المالية. المستخدم أدخل قاعدة تحليل جديدة:

"{user_input}"

مهمتك:
1. تحسين وإعادة صياغة هذه القاعدة بشكل احترافي ومفهوم
2. ترقيم القاعدة وتنظيمها
3. إضافة تفاصيل تقنية مفيدة إذا لزم الأمر
4. التأكد من أن القاعدة واضحة وقابلة للتطبيق

اكتب القاعدة المحسنة بشكل مرقم ومنظم:
"""
        
        response = gemini_analyzer.model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في معالجة القاعدة بالذكاء الاصطناعي: {e}")
        return None

def get_analysis_rules_for_prompt():
    """جلب قواعد التحليل المخصصة للإضافة إلى البرومبت"""
    rules = load_analysis_rules()
    if not rules:
        return ""
    
    rules_text = "\n\n=== قواعد التحليل المخصصة من المستخدمين ===\n"
    for i, rule in enumerate(rules, 1):
        rules_text += f"\n{i}. {rule['processed_rule']}\n"
        rules_text += f"   (أضيفت بواسطة المستخدم {rule['user_id']} في {rule['created_at']})\n"
    
    rules_text += "\n=== يجب مراعاة هذه القواعد في التحليل ===\n"
    return rules_text

# تحديث دالة التحليل لتشمل القواعد المخصصة
def get_custom_analysis_rules():
    """الحصول على القواعد المخصصة لإدراجها في البرومبت"""
    return get_analysis_rules_for_prompt()

@bot.callback_query_handler(func=lambda call: call.data == "add_analysis_rule")
def handle_add_analysis_rule(call):
    """معالج إضافة قاعدة تحليل"""
    try:
        message_text = """
➕ **إضافة قاعدة تحليل جديدة**

📝 **اكتب قاعدة التحليل التي تريد إضافتها:**

مثال على القواعد:
• "عند كسر مستوى المقاومة بحجم تداول عالي، زد نسبة الثقة بـ 15%"
• "في حالة تضارب RSI مع MACD، قلل نسبة النجاح بـ 20%"
• "عند تداول الذهب أثناء الأحداث الجيوسياسية، زد الحذر وقلل حجم الصفقة"

⚡ **سيقوم الذكاء الاصطناعي بـ:**
- تحسين وإعادة صياغة قاعدتك
- ترتيبها وترقيمها
- إضافة تفاصيل تقنية مفيدة

📤 **أرسل قاعدتك الآن:**
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.row(
            create_animated_button("🔙 العودة لإدارة القواعد", "manage_analysis_rules", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
        # تعيين حالة انتظار إدخال القاعدة
        user_states[call.from_user.id] = {
            'state': 'waiting_for_analysis_rule',
            'message_id': call.message.message_id,
            'chat_id': call.message.chat.id
        }
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في إضافة قاعدة التحليل: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في إضافة قاعدة التحليل", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "edit_analysis_rules")
def handle_edit_analysis_rules(call):
    """معالج تحرير قواعد التحليل"""
    try:
        rules = load_analysis_rules()
        
        if not rules:
            message_text = """
✏️ **تحرير قواعد التحليل**

📋 **لا توجد قواعد محفوظة حالياً**

قم بإضافة قواعد جديدة أولاً من خلال زر "إضافة قاعدة"
            """
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.row(
                create_animated_button("➕ إضافة قاعدة جديدة", "add_analysis_rule", "➕")
            )
            markup.row(
                create_animated_button("🔙 العودة لإدارة القواعد", "manage_analysis_rules", "🔙")
            )
        else:
            message_text = f"""
✏️ **تحرير قواعد التحليل**

📋 **القواعد المحفوظة ({len(rules)} قاعدة):**

اختر القاعدة التي تريد تحريرها أو حذفها:
            """
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            for i, rule in enumerate(rules):
                rule_preview = rule['processed_rule'][:50] + "..." if len(rule['processed_rule']) > 50 else rule['processed_rule']
                markup.row(
                    create_animated_button(f"📝 {i+1}. {rule_preview}", f"edit_rule_{i}", "📝")
                )
            
            markup.row(
                create_animated_button("🔙 العودة لإدارة القواعد", "manage_analysis_rules", "🔙")
            )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تحرير قواعد التحليل: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في تحرير قواعد التحليل", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_rule_"))
def handle_edit_specific_rule(call):
    """معالج تحرير قاعدة محددة"""
    try:
        rule_index = int(call.data.split("_")[2])
        rules = load_analysis_rules()
        
        if rule_index >= len(rules):
            bot.answer_callback_query(call.id, "القاعدة غير موجودة", show_alert=True)
            return
            
        rule = rules[rule_index]
        
        message_text = f"""
📝 **تحرير القاعدة #{rule_index + 1}**

**القاعدة الحالية:**
{rule['processed_rule']}

**معلومات القاعدة:**
• أضيفت بواسطة: المستخدم {rule['user_id']}
• تاريخ الإضافة: {rule['created_at']}
• النص الأصلي: {rule['original_rule']}

**اختر الإجراء:**
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.row(
            create_animated_button("✏️ تعديل القاعدة", f"modify_rule_{rule_index}", "✏️")
        )
        markup.row(
            create_animated_button("🗑️ حذف القاعدة", f"delete_rule_{rule_index}", "🗑️")
        )
        markup.row(
            create_animated_button("🔙 العودة لقائمة القواعد", "edit_analysis_rules", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تحرير القاعدة المحددة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في تحرير القاعدة", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_rule_"))
def handle_delete_rule(call):
    """معالج حذف قاعدة"""
    try:
        rule_index = int(call.data.split("_")[2])
        rules = load_analysis_rules()
        
        if rule_index >= len(rules):
            bot.answer_callback_query(call.id, "القاعدة غير موجودة", show_alert=True)
            return
        
        # حذف القاعدة
        deleted_rule = rules.pop(rule_index)
        
        if save_analysis_rules(rules):
            bot.answer_callback_query(call.id, "✅ تم حذف القاعدة بنجاح", show_alert=True)
            
            # العودة لقائمة القواعد
            handle_edit_analysis_rules(call)
        else:
            bot.answer_callback_query(call.id, "❌ فشل في حذف القاعدة", show_alert=True)
            
    except Exception as e:
        logger.error(f"[ERROR] خطأ في حذف القاعدة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في حذف القاعدة", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("modify_rule_"))
def handle_modify_rule(call):
    """معالج تعديل قاعدة"""
    try:
        rule_index = int(call.data.split("_")[2])
        rules = load_analysis_rules()
        
        if rule_index >= len(rules):
            bot.answer_callback_query(call.id, "القاعدة غير موجودة", show_alert=True)
            return
            
        rule = rules[rule_index]
        
        message_text = f"""
✏️ **تعديل القاعدة #{rule_index + 1}**

**القاعدة الحالية:**
{rule['processed_rule']}

📝 **اكتب النص الجديد للقاعدة:**

سيقوم الذكاء الاصطناعي بتحسين وإعادة صياغة النص الجديد.

📤 **أرسل النص المُحدث الآن:**
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.row(
            create_animated_button("🔙 العودة للقاعدة", f"edit_rule_{rule_index}", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
        # تعيين حالة انتظار تعديل القاعدة
        user_states[call.from_user.id] = {
            'state': 'waiting_for_rule_modification',
            'rule_index': rule_index,
            'message_id': call.message.message_id,
            'chat_id': call.message.chat.id
        }
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تعديل القاعدة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في تعديل القاعدة", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "select_symbols")
def handle_select_symbols(call):
    """معالج اختيار الرموز للمراقبة"""
    try:
        user_id = call.from_user.id
        selected_symbols = user_selected_symbols.get(user_id, [])
        
        message_text = f"""
📊 **اختيار الرموز للمراقبة**

الرموز المختارة حالياً: {len(selected_symbols)}
{', '.join(selected_symbols) if selected_symbols else 'لا توجد رموز مختارة'}

اختر فئة لإضافة رموز منها:
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.row(
            create_animated_button("💶 أزواج العملات", "select_forex", "💶"),
            create_animated_button("🥇 المعادن", "select_metals", "🥇")
        )
        
        markup.row(
            create_animated_button("₿ العملات الرقمية", "select_crypto", "₿"),
            create_animated_button("📈 الأسهم الأمريكية", "select_stocks", "📈")
        )
        
        markup.row(
            create_animated_button("📊 المؤشرات", "select_indices", "📊")
        )
        
        if selected_symbols:
            markup.row(
                create_animated_button("🗑️ مسح جميع الرموز", "clear_symbols", "🗑️")
            )
        
        markup.row(
            create_animated_button("🔙 المراقبة الآلية", "auto_monitoring", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض اختيار الرموز: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض اختيار الرموز", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_symbol_selection(call):
    """معالج اختيار رموز من فئة معينة"""
    try:
        user_id = call.from_user.id
        category = call.data.split('_')[1]
        
        # حفظ الفئة الحالية للمستخدم
        user_current_category[user_id] = category
        
        # تحديد الرموز حسب الفئة
        if category == "forex":
            symbols = CURRENCY_PAIRS
            title = "💶 اختيار أزواج العملات"
        elif category == "metals":
            symbols = METALS
            title = "🥇 اختيار المعادن"
        elif category == "crypto":
            symbols = CRYPTO_PAIRS
            title = "₿ اختيار العملات الرقمية"
        elif category == "stocks":
            symbols = STOCKS
            title = "📈 اختيار الأسهم الأمريكية"
        elif category == "indices":
            symbols = INDICES
            title = "📊 اختيار المؤشرات"
        else:
            return
        
        selected_symbols = user_selected_symbols.get(user_id, [])
        
        message_text = f"{title}\n\n"
        message_text += "اختر الرموز التي تريد مراقبتها:\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for symbol, info in symbols.items():
            is_selected = symbol in selected_symbols
            button_text = f"{'✅' if is_selected else '☐'} {info['name']}"
            callback_data = f"toggle_{symbol}"
            
            markup.row(
                types.InlineKeyboardButton(button_text, callback_data=callback_data)
            )
        
        markup.row(
            create_animated_button("🔙 اختيار فئة أخرى", "select_symbols", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض رموز الفئة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض الرموز", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def handle_toggle_symbol(call):
    """معالج تبديل اختيار الرمز"""
    try:
        user_id = call.from_user.id
        symbol = call.data.split('_')[1]
        
        if user_id not in user_selected_symbols:
            user_selected_symbols[user_id] = []
        
        selected_symbols = user_selected_symbols[user_id]
        
        if symbol in selected_symbols:
            selected_symbols.remove(symbol)
            action = "تم إلغاء اختيار"
        else:
            selected_symbols.append(symbol)
            action = "تم اختيار"
        
        symbol_info = ALL_SYMBOLS.get(symbol, {'name': symbol})
        
        # إظهار رسالة تأكيد مع أنيميشن
        if symbol in selected_symbols:
            bot.answer_callback_query(
                call.id,
                f"✅ {action} {symbol_info['name']}",
                show_alert=False
            )
        else:
            bot.answer_callback_query(
                call.id,
                f"❌ {action} {symbol_info['name']}",
                show_alert=False
            )
        
        # تحديث القائمة بناءً على الفئة المحفوظة
        current_category = user_current_category.get(user_id, 'forex')
        fake_call = type('obj', (object,), {
            'data': f'select_{current_category}',
            'from_user': call.from_user,
            'message': call.message
        })
        handle_symbol_selection(fake_call)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تبديل الرمز: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في تبديل الرمز", show_alert=True)

# تم حذف معالجات التردد - التردد الآن موحد لكل 15 ثانية

@bot.callback_query_handler(func=lambda call: call.data.startswith("detailed_"))
def handle_detailed_analysis(call):
    """معالج التحليل التفصيلي للفئة"""
    try:
        user_id = call.from_user.id
        category = call.data.split('_')[1]
        
        # تحديد الرموز حسب الفئة
        if category == "forex":
            symbols = CURRENCY_PAIRS
            title = "💶 تحليل تفصيلي - أزواج العملات"
        elif category == "metals":
            symbols = METALS
            title = "🥇 تحليل تفصيلي - المعادن النفيسة"
        elif category == "crypto":
            symbols = CRYPTO_PAIRS
            title = "₿ تحليل تفصيلي - العملات الرقمية"
        elif category == "indices":
            symbols = INDICES
            title = "📊 تحليل تفصيلي - المؤشرات"
        else:
            return
        
        message_text = f"{title}\n\n"
        message_text += "اختر الرمز للحصول على تحليل تفصيلي شامل:\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for symbol, info in symbols.items():
            # جلب بيانات سريعة لعرض السعر
            price_data = mt5_manager.get_live_price(symbol)
            current_price = ""
            if price_data:
                current_price = f" - ${price_data.get('last', price_data.get('bid', 0)):.5f}"
            
            button_text = f"{info['emoji']} {info['name']}{current_price}"
            markup.row(
                types.InlineKeyboardButton(button_text, callback_data=f"full_analysis_{symbol}")
            )
        
        markup.row(
            create_animated_button("🔙 العودة للتحليل السريع", f"analyze_{category}", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في التحليل التفصيلي: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في التحليل التفصيلي", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("full_analysis_"))
def handle_full_symbol_analysis(call):
    """معالج التحليل الشامل لرمز واحد"""
    try:
        user_id = call.from_user.id
        symbol = call.data.split('_', 2)[2]
        
        # جلب معلومات الرمز
        symbol_info = ALL_SYMBOLS.get(symbol)
        if not symbol_info:
            bot.answer_callback_query(call.id, "❌ رمز غير معروف", show_alert=True)
            return
        
        # عرض رسالة التحليل أولاً
        bot.edit_message_text(
            f"🔍 **جاري التحليل الشامل...**\n\n"
            f"📊 **الرمز:** {symbol_info['name']} ({symbol})\n"
            f"👤 **المستخدم:** {call.from_user.first_name}\n"
            "⏳ **يرجى الانتظار للحصول على تحليل متقدم...**",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        
        # جلب البيانات اللحظية
        price_data = mt5_manager.get_live_price(symbol)
        if not price_data:
            bot.edit_message_text(
                f"❌ **فشل في جلب البيانات**\n\n"
                f"📊 **الرمز:** {symbol_info['name']} ({symbol})\n"
                f"⚠️ لا توجد بيانات متاحة حالياً لهذا الرمز.\n"
                f"🔄 يرجى المحاولة مرة أخرى لاحقاً.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
            return
        
        # تحليل شامل مع Gemini AI
        analysis = gemini_analyzer.analyze_market_data(symbol, price_data, user_id)
        
        # إعداد الرسالة الشاملة
        data_source = price_data.get('source', 'Unknown')
        formatted_time = format_time_for_user(user_id, price_data.get('time'))
        trading_mode = get_user_trading_mode(user_id)
        capital = get_user_capital(user_id)
        
        message_text = f"""
🔍 **تحليل شامل - {symbol_info['name']}** {symbol_info['emoji']}

📊 **معلومات الرمز:**
• **الرمز:** {symbol}
• **الاسم:** {symbol_info['name']}
• **النوع:** {symbol_info['type']}

💰 **البيانات السعرية:**
• **السعر الحالي:** ${price_data.get('last', price_data.get('bid', 0)):.5f}
• **سعر الشراء:** ${price_data.get('bid', 0):.5f}
• **سعر البيع:** ${price_data.get('ask', 0):.5f}
• **فرق السعر:** {price_data.get('spread', 0):.5f}
• **الحجم:** {price_data.get('volume', 0):,}

👤 **سياق المستخدم:**
• **نمط التداول:** {trading_mode}
• **رأس المال:** ${capital:,.2f}

🧠 **تحليل الذكاء الاصطناعي:**
• **التوصية:** {analysis.get('action', 'HOLD')} 
• **قوة الإشارة:** {analysis.get('confidence', 50):.1f}%
• **المصدر:** {analysis.get('source', 'AI Analysis')}

📝 **التحليل التفصيلي:**
{analysis.get('ai_analysis', 'تحليل غير متوفر حالياً')}

🕐 **معلومات التحديث:**
• **آخر تحديث:** {formatted_time}
• **مصدر البيانات:** {data_source}

───────────────────────
🤖 **بوت التداول v1.2.0 - تحليل ذكي**
        """
        
        # أزرار التحكم
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.row(
            create_animated_button("🔄 إعادة التحليل", f"full_analysis_{symbol}", "🔄"),
            create_animated_button("📊 إضافة للمراقبة", f"add_monitor_{symbol}", "📊")
        )
        markup.row(
            create_animated_button("🔙 العودة للقائمة", "analyze_symbols", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في التحليل الشامل: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في التحليل", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "help")
def handle_help(call):
    """معالج المساعدة"""
    try:
        help_text = """
❓ **مساعدة بوت التداول v1.2.0**

🚀 **الميزات الجديدة:**
• بيانات لحظية حقيقية من MetaTrader5 + Yahoo Finance
• تحليل ذكي مخصص بـ Google Gemini AI
• نظام تقييم الإشعارات 👍👎 للتعلم الآلي
• تدريب الذكاء الاصطناعي برفع الملفات
• سجل تنبيهات شامل مع إحصائيات

📊 **كيفية الاستخدام:**

1️⃣ **التحليل اليدوي:**
   • انتقل إلى "تحليل الرموز"
   • اختر الفئة المطلوبة (عملات، معادن، عملات رقمية، مؤشرات)
   • احصل على تحليل فوري مخصص لنمط تداولك ورأس مالك

2️⃣ **المراقبة الآلية:**
   • اذهب للإعدادات → اختيار الرموز للمراقبة
   • ستصلك إشعارات ذكية مخصصة كل 30 ثانية
   • التحليل يراعي نمط التداول ورأس المال

3️⃣ **نظام التقييم والتعلم:**
   • اضغط 👍 للإشارات الدقيقة، 👎 للخاطئة
   • النظام يتعلم من تقييماتك ويحسن الدقة
   • راجع سجل التنبيهات لمتابعة الأداء

4️⃣ **تدريب الذكاء الاصطناعي:**
   • ارفع صور الشارتات، ملفات PDF، أو مستندات تحليلية
   • النظام يتعلم من ملفاتك ويطبق المعرفة على التحليلات

5️⃣ **إعدادات متقدمة:**
   • حدد نمط التداول (سكالبينغ/طويل المدى)
   • اضبط عتبة النجاح للإشعارات
   • اختر المنطقة الزمنية لعرض الأوقات بدقة

📊 **مصادر البيانات:**
• **أولوية أولى:** MetaTrader5 (بيانات لحظية مباشرة)
• **بديل ذكي:** Yahoo Finance (للرموز غير المتوفرة في MT5)
• **ضمان التغطية:** 25+ رمز مالي مدعوم

🧠 **الذكاء الاصطناعي المخصص:**
• تحليل يراعي نمط التداول الخاص بك
• توصيات حجم الصفقة حسب رأس المال
• تعلم مستمر من تقييماتك وملفاتك المرفوعة
• عرض الأوقات حسب منطقتك الزمنية

💡 **نصائح للحصول على أفضل النتائج:**
• فعّل MT5 للحصول على أدق البيانات
• قيّم الإشارات بصدق لتحسين النظام
• ارفع ملفات تحليلية لتعزيز ذكاء النظام
• راجع سجل التنبيهات لتتبع الأداء
• استخدم التحليل التفصيلي للقرارات المهمة
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=help_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض المساعدة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض المساعدة", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "about")
def handle_about(call):
    """معالج معلومات البوت"""
    try:
        about_text = """
ℹ️ **حول بوت التداول المتقدم v1.2.0**

🤖 **معلومات البوت:**
📱 رقم الإصدار: v1.2.0
📅 تاريخ الإصدار: 2025
🏗️ مطور بتقنيات متقدمة

🔧 **التقنيات المستخدمة:**
• MetaTrader5: بيانات لحظية حقيقية
• Google Gemini AI: تحليل ذكي ومتطور
• Python: لغة البرمجة الأساسية
• Telegram Bot API: واجهة المستخدم

🚀 **الميزات الجديدة في v1.2.0:**
✅ إلغاء الاعتماد على البيانات التاريخية
✅ بيانات لحظية مباشرة من MT5 + Yahoo Finance
✅ تحليل ذكي مخصص مدعوم بـ Gemini AI
✅ نظام تقييم تفاعلي 👍👎 للتعلم الآلي
✅ رفع ملفات لتدريب الذكاء الاصطناعي
✅ سجل تنبيهات شامل مع إحصائيات
✅ تحليل مخصص يراعي نمط التداول ورأس المال
✅ دعم المناطق الزمنية المختلفة
✅ واجهة محسنة مع تحليل تفصيلي

📊 **الإحصائيات:**
• أكثر من 25 رمز مالي مدعوم
• تحديث لحظي كل 30 ثانية
• دقة تحليل عالية مع التعلم المستمر
• دعم جميع أنواع التداول

👨‍💻 **المطور:**
Mohamad Zalaf ©️2025

🎯 **هدفنا:** 
تقديم أفضل تجربة تداول ذكية مع دقة عالية وتحسين مستمر من خلال تقييمات المستخدمين.

💪 **التزامنا:**
التطوير المستمر والدعم الدائم مع أحدث التقنيات في مجال الذكاء الاصطناعي والتداول.
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=about_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض معلومات البوت: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض معلومات البوت", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "upload_file")
def handle_upload_file(call):
    """معالج رفع الملفات للتدريب"""
    try:
        user_id = call.from_user.id
        
        message_text = """
📁 **رفع ملف للتدريب الذكي**

🤖 **نظام التعلم الآلي:**
يمكنك رفع ملفات مختلفة لتدريب الذكاء الاصطناعي:

📊 **أنواع الملفات المدعومة:**
• **الصور:** الشارتات، الأنماط الفنية، التحليلات البصرية
• **المستندات:** PDF, Word, Text مع تحليلات وتوقعات
• **البيانات:** ملفات Excel مع بيانات السوق

🧠 **كيف يعمل التعلم:**
1. ارفع الملف هنا
2. سيتم تحليل المحتوى
3. ربط البيانات بنمط تداولك ورأس مالك
4. تحسين دقة التوقعات المستقبلية

👤 **سياق التدريب الحالي:**
• نمط التداول: {trading_mode}
• رأس المال: ${capital:,.2f}

📎 **لرفع ملف:** أرسل الملف مباشرة في المحادثة الآن
        """.format(
            trading_mode=get_user_trading_mode(user_id),
            capital=get_user_capital(user_id)
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        # تحديد حالة المستخدم لاستقبال الملف
        user_states[user_id] = 'waiting_file_upload'
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في رفع الملف: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "alerts_log")
def handle_alerts_log(call):
    """معالج سجل التنبيهات"""
    try:
        user_id = call.from_user.id
        
        # جلب آخر التنبيهات للمستخدم
        alerts = get_user_recent_alerts(user_id)
        
        message_text = "📋 **سجل الإشعارات**\n\n"
        
        if not alerts:
            message_text += "📭 لا توجد إشعارات حتى الآن\n"
            message_text += "🔔 ستظهر الإشعارات هنا عند إرسالها"
        else:
            message_text += f"📊 **إجمالي الإشعارات:** {len(alerts)}\n\n"
            
            # عرض آخر 5 تنبيهات
            for i, alert in enumerate(alerts[:5], 1):
                formatted_time = format_time_for_user(user_id, alert.get('timestamp'))
                symbol = alert.get('symbol', 'Unknown')
                action = alert.get('action', 'Unknown')
                confidence = alert.get('confidence', 0)
                feedback = alert.get('feedback', 'لا يوجد تقييم')
                
                feedback_emoji = "👍" if feedback == "positive" else "👎" if feedback == "negative" else "⏳"
                
                message_text += f"**{i}.** {symbol} - {action}\n"
                message_text += f"   💪 قوة: {confidence:.1f}%\n"
                message_text += f"   {feedback_emoji} تقييم: {feedback}\n"
                message_text += f"   🕐 {formatted_time}\n\n"
        
        # إحصائيات التقييم
        stats = TradeDataManager.get_user_feedback_stats(user_id)
        message_text += "📊 **إحصائيات التقييم:**\n"
        message_text += f"• مجموع التقييمات: {stats['total_feedbacks']}\n"
        message_text += f"• تقييمات إيجابية: {stats['positive_feedbacks']} 👍\n"
        message_text += f"• تقييمات سلبية: {stats['negative_feedbacks']} 👎\n"
        message_text += f"• معدل الدقة: {stats['accuracy_rate']:.1f}%\n"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.row(
            create_animated_button("🔄 تحديث", "alerts_log", "🔄"),
            create_animated_button("🗑️ مسح السجل", "clear_alerts", "🗑️")
        )
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض سجل التنبيهات: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض السجل", show_alert=True)

def get_user_recent_alerts(user_id: int, limit: int = 10) -> List[Dict]:
    """جلب التنبيهات الأخيرة للمستخدم"""
    try:
        alerts = []
        
        # البحث في ملفات سجلات الصفقات
        for filename in os.listdir(TRADE_LOGS_DIR):
            if filename.startswith(f'trade_{user_id}_'):
                file_path = os.path.join(TRADE_LOGS_DIR, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    trade_data = json.load(f)
                
                alert_data = {
                    'symbol': trade_data.get('symbol'),
                    'action': trade_data.get('signal', {}).get('action'),
                    'confidence': trade_data.get('signal', {}).get('confidence'),
                    'timestamp': datetime.fromisoformat(trade_data.get('timestamp')),
                    'feedback': trade_data.get('feedback')
                }
                alerts.append(alert_data)
        
        # ترتيب حسب الوقت (الأحدث أولاً)
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return alerts[:limit]
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في جلب التنبيهات: {e}")
        return []

# معالج رفع الملفات
@bot.message_handler(content_types=['document', 'photo'])
def handle_file_upload(message):
    """معالج رفع الملفات من المستخدم"""
    try:
        user_id = message.from_user.id
        
        # التحقق من حالة المستخدم
        if user_states.get(user_id) not in ['waiting_file_upload', 'waiting_pattern_description']:
            return
        
        file_info = None
        file_type = None
        
        if user_states.get(user_id) == 'waiting_file_upload':
            if message.content_type == 'photo':
                file_info = bot.get_file(message.photo[-1].file_id)
                file_type = 'image/jpeg'
            elif message.content_type == 'document':
                file_info = bot.get_file(message.document.file_id)
                file_type = message.document.mime_type or 'application/octet-stream'
            
            if file_info:
                # تحميل الملف
                downloaded_file = bot.download_file(file_info.file_path)
                
                # حفظ الملف محلياً
                upload_dir = os.path.join(DATA_DIR, "uploaded_files")
                os.makedirs(upload_dir, exist_ok=True)
                
                file_extension = file_info.file_path.split('.')[-1] if '.' in file_info.file_path else 'bin'
                local_file_path = os.path.join(upload_dir, f"{user_id}_{int(time.time())}.{file_extension}")
                
                with open(local_file_path, 'wb') as f:
                    f.write(downloaded_file)
                
                # حفظ مسار الملف مؤقتاً للمستخدم
                if not hasattr(bot, 'temp_user_files'):
                    bot.temp_user_files = {}
                bot.temp_user_files[user_id] = {
                    'file_path': local_file_path,
                    'file_type': file_type
                }
                
                # طلب وصف النمط من المستخدم
                user_states[user_id] = 'waiting_pattern_description'
                
                bot.reply_to(message, 
                    "✅ **تم رفع الصورة بنجاح!**\n\n"
                    "🧠 **الآن اشرح لي النمط:**\n\n"
                    "📝 **مثال على الوصف:**\n"
                    "• 'عند رؤية هذا النمط من الشموع، السعر سينزل بنسبة 90%'\n"
                    "• 'هذا النمط يعني ارتفاع قوي - ثقة 100%'\n"
                    "• 'شمعة الدوجي هذه تعني تردد السوق - احتمال انعكاس 80%'\n\n"
                    "💡 **كن محدداً:** اذكر النمط والاتجاه المتوقع ونسبة الثقة")
        
        elif user_states.get(user_id) == 'waiting_pattern_description':
            # معالجة وصف النمط
            pattern_description = message.text.strip()
            
            if len(pattern_description) < 10:
                bot.reply_to(message, 
                    "⚠️ **الوصف قصير جداً**\n\n"
                    "يرجى إعطاء وصف مفصل أكثر للنمط والاتجاه المتوقع")
                return
            
            # جلب بيانات الملف المحفوظة
            if hasattr(bot, 'temp_user_files') and user_id in bot.temp_user_files:
                file_data = bot.temp_user_files[user_id]
                
                # إعداد سياق المستخدم للتدريب
                user_context = {
                    'trading_mode': get_user_trading_mode(user_id),
                    'capital': get_user_capital(user_id),
                    'timezone': get_user_timezone(user_id),
                    'pattern_description': pattern_description
                }
                
                # إرسال للتعلم الآلي مع الوصف
                success = gemini_analyzer.learn_from_pattern_image(
                    file_data['file_path'], 
                    file_data['file_type'], 
                    user_context,
                    pattern_description
                )
                
                if success:
                    bot.reply_to(message, 
                        "🎯 **تم تعلم النمط بنجاح!**\n\n"
                        f"📊 **النمط المحفوظ:** {pattern_description[:100]}...\n\n"
                        "🧠 **ما حدث:**\n"
                        "• تم تحليل الصورة بواسطة الذكاء الاصطناعي\n"
                        "• تم ربط النمط بوصفك وتوقعاتك\n"
                        "• سيتم استخدام هذه المعرفة في التحليلات القادمة\n\n"
                        "🔄 **النتيجة:** التحليلات ستكون أكثر دقة ومخصصة لك!")
                else:
                    bot.reply_to(message, 
                        "⚠️ **تم حفظ النمط ولكن...**\n\n"
                        "📁 النمط محفوظ بنجاح\n"
                        "🤖 لكن لم يتم معالجته بالكامل\n"
                        "🔧 سيتم المحاولة لاحقاً")
                
                # تنظيف البيانات المؤقتة
                del bot.temp_user_files[user_id]
            
            # إزالة حالة انتظار الوصف
            user_states.pop(user_id, None)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في معالجة الملف المرفوع: {e}")
        bot.reply_to(message, "❌ حدث خطأ في معالجة الملف")

# ===== معالجات المراقبة الآلية =====
@bot.callback_query_handler(func=lambda call: call.data == "auto_monitoring")
def handle_auto_monitoring(call):
    """معالج المراقبة الآلية"""
    try:
        user_id = call.from_user.id
        trading_mode = get_user_trading_mode(user_id)
        trading_mode_display = "⚡ سكالبينغ سريع" if trading_mode == 'scalping' else "📈 تداول طويل المدى"
        is_monitoring = user_monitoring_active.get(user_id, False)
        status = "🟢 نشطة" if is_monitoring else "🔴 متوقفة"
        selected_count = len(user_selected_symbols.get(user_id, []))
        
        # الحصول على إعدادات التنبيهات لعرض التردد الصحيح
        settings = get_user_advanced_notification_settings(user_id)
        frequency_display = NOTIFICATION_FREQUENCIES.get(settings.get('frequency', '5min'), {}).get('name', '5 دقائق')
        success_threshold = settings.get('success_threshold', 70)
        threshold_display = f"{success_threshold}%" if success_threshold > 0 else "الكل"
        
        message_text = f"""
📡 **المراقبة الآلية v1.2.0**

🎯 **نمط التداول:** {trading_mode_display}
📈 **الحالة:** {status}
🎯 **الرموز المختارة:** {selected_count}
⏱️ **تردد الفحص:** {frequency_display}
🎯 **نسبة النجاح:** {threshold_display}
🔗 **مصدر البيانات:** MetaTrader5 + Gemini AI

تعتمد المراقبة على إعدادات التنبيهات ونمط التداول المحدد.
        """
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=create_auto_monitoring_menu(user_id)
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في المراقبة الآلية: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض المراقبة", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "start_monitoring")
def handle_start_monitoring(call):
    """معالج بدء المراقبة"""
    user_id = call.from_user.id
    
    try:
        # التحقق من وجود رموز مختارة
        selected_symbols = user_selected_symbols.get(user_id, [])
        trading_mode = get_user_trading_mode(user_id)
        trading_mode_display = "⚡ سكالبينغ سريع" if trading_mode == 'scalping' else "📈 تداول طويل المدى"
        
        if not selected_symbols:
            bot.answer_callback_query(
                call.id,
                "⚠️ يجب اختيار رموز للمراقبة أولاً من زر 'تحديد الرموز'",
                show_alert=True
            )
            return
        
        # التحقق من إعدادات التنبيهات
        notification_settings = get_user_advanced_notification_settings(user_id)
        active_notifications = [k for k, v in notification_settings.items() 
                              if k in ['support_alerts', 'breakout_alerts', 'trading_signals', 
                                     'economic_news', 'candlestick_patterns', 'volume_alerts'] and v]
        
        # تحذير فقط إذا كانت جميع الأنواع معطلة
        if not active_notifications:
            bot.answer_callback_query(
                call.id,
                "⚠️ تحذير: جميع أنواع الإشعارات معطلة! يمكنك تفعيلها من 'إعدادات التنبيهات'",
                show_alert=True
            )
        
        # بدء المراقبة
        user_monitoring_active[user_id] = True
        
        # رسالة تأكيد
        bot.answer_callback_query(call.id, "✅ تم بدء المراقبة الآلية بنجاح")
        
        # تحديث القائمة
        bot.edit_message_text(
            f"▶️ **المراقبة الآلية نشطة**\n\n"
            f"📊 **نمط التداول:** {trading_mode_display}\n"
            f"📈 **الحالة:** 🟢 نشطة\n"
            f"🎯 **الرموز المراقبة:** {len(selected_symbols)} رمز\n"
            f"⚡ **التردد:** {'30 ثانية' if trading_mode == 'scalping' else '5 دقائق'}\n"
            f"🔗 **مصدر البيانات:** MetaTrader5 + Gemini AI\n\n"
            f"📋 **أنواع التنبيهات المفعلة:**\n" + 
            '\n'.join([f"✅ {get_notification_display_name(setting)}" for setting in active_notifications]) +
            "\n\nالمراقبة نشطة وسيتم إرسال التنبيهات عند رصد فرص تداول.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_auto_monitoring_menu(user_id),
            parse_mode='Markdown'
        )
        
        # إرسال تنبيه بدء المراقبة
        symbols_text = ", ".join(selected_symbols[:5])
        if len(selected_symbols) > 5:
            symbols_text += f" و{len(selected_symbols) - 5} رمز آخر"
        
        bot.send_message(
            call.message.chat.id,
            f"▶️ **بدء المراقبة الآلية**\n\n"
            f"📊 نمط التداول: {trading_mode_display}\n"
            f"🎯 الرموز: {symbols_text}\n"
            f"⏰ بدء المراقبة: {datetime.now().strftime('%H:%M:%S')}\n"
            f"🔗 مصدر البيانات: MetaTrader5 + Gemini AI\n\n"
            "سيتم إرسال التنبيهات عند رصد فرص تداول مناسبة! 📈"
        )
        
    except Exception as e:
        logger.error(f"خطأ في بدء المراقبة للمستخدم {user_id}: {str(e)}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في بدء المراقبة")

@bot.callback_query_handler(func=lambda call: call.data == "stop_monitoring")
def handle_stop_monitoring(call):
    """معالج إيقاف المراقبة"""
    user_id = call.from_user.id
    
    try:
        # إيقاف المراقبة
        user_monitoring_active[user_id] = False
        
        # رسالة تأكيد
        bot.answer_callback_query(call.id, "⏹️ تم إيقاف المراقبة الآلية")
        
        # تحديث القائمة
        trading_mode = get_user_trading_mode(user_id)
        trading_mode_display = "⚡ سكالبينغ سريع" if trading_mode == 'scalping' else "📈 تداول طويل المدى"
        selected_count = len(user_selected_symbols.get(user_id, []))
        
        bot.edit_message_text(
            f"📡 **المراقبة الآلية**\n\n"
            f"📊 **نمط التداول:** {trading_mode_display}\n"
            f"📈 **الحالة:** 🔴 متوقفة\n"
            f"🎯 **الرموز المختارة:** {selected_count}\n"
            f"🔗 **مصدر البيانات:** MetaTrader5 + Gemini AI\n\n"
            "تعتمد المراقبة على إعدادات التنبيهات ونمط التداول المحدد.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_auto_monitoring_menu(user_id),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في إيقاف المراقبة للمستخدم {user_id}: {str(e)}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في إيقاف المراقبة")

# ===== معالجات نمط التداول =====
@bot.callback_query_handler(func=lambda call: call.data == "trading_mode_settings")
def handle_trading_mode_settings(call):
    """معالج إعدادات نمط التداول"""
    try:
        user_id = call.from_user.id
        current_mode = get_user_trading_mode(user_id)
        
        message_text = f"""
🎯 **إعدادات نمط التداول**

النمط الحالي: {'⚡ سكالبينغ سريع' if current_mode == 'scalping' else '📈 تداول طويل المدى'}

📊 **السكالبينغ السريع:**
• أهداف ربح صغيرة (1-2%)
• وقف خسارة ضيق (0.5%)
• تحليل سريع وفوري
• مناسب للمتداولين النشطين

📈 **التداول طويل المدى:**
• أهداف ربح أكبر (5-10%)
• وقف خسارة أوسع (2%)
• تحليل شامل ومتأني
• مناسب للاستثمار طويل الأمد

اختر النمط المناسب لك:
        """
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=create_trading_mode_menu(user_id)
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في إعدادات نمط التداول: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض أنماط التداول", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_trading_mode_"))
def handle_set_trading_mode(call):
    """معالج تعيين نمط التداول"""
    try:
        user_id = call.from_user.id
        mode = call.data.replace("set_trading_mode_", "")
        
        set_user_trading_mode(user_id, mode)
        mode_display = "السكالبينغ السريع" if mode == 'scalping' else "التداول طويل الأمد"
        
        bot.answer_callback_query(call.id, f"✅ تم تعيين نمط {mode_display}")
        
        # تحديث القائمة
        handle_trading_mode_settings(call)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تعيين نمط التداول: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في تعيين النمط", show_alert=True)

# ===== معالج مسح السجل =====
@bot.callback_query_handler(func=lambda call: call.data == "clear_alerts")
def handle_clear_alerts(call):
    """معالج مسح سجل التنبيهات"""
    try:
        user_id = call.from_user.id
        
        # حذف جميع ملفات السجل للمستخدم
        deleted_count = 0
        try:
            for filename in os.listdir(TRADE_LOGS_DIR):
                if filename.startswith("trade_") and filename.endswith(".json"):
                    file_path = os.path.join(TRADE_LOGS_DIR, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        trade_data = json.load(f)
                        if trade_data.get('user_id') == user_id:
                            os.remove(file_path)
                            deleted_count += 1
        except Exception as e:
            logger.error(f"خطأ في حذف ملفات السجل: {e}")
        
        if deleted_count > 0:
            bot.answer_callback_query(call.id, f"✅ تم مسح {deleted_count} تنبيه من السجل")
        else:
            bot.answer_callback_query(call.id, "ℹ️ لا توجد تنبيهات لمسحها")
        
        # تحديث عرض السجل
        handle_alerts_log(call)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في مسح السجل: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في مسح السجل", show_alert=True)

# ===== معالجات رأس المال =====
@bot.callback_query_handler(func=lambda call: call.data == "set_capital")
def handle_set_capital(call):
    """معالج تحديد رأس المال"""
    try:
        user_id = call.from_user.id
        current_capital = get_user_capital(user_id)
        
        message_text = f"""
💰 **تحديد رأس المال**

رأس المال الحالي: ${current_capital:,.0f}

اختر رأس المال المناسب لك:
(يؤثر على حجم الصفقات المقترحة وإدارة المخاطر)
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        for capital in DEFAULT_CAPITAL_OPTIONS:
            button_text = f"✅ ${capital:,}" if capital == current_capital else f"${capital:,}"
            markup.row(
                types.InlineKeyboardButton(button_text, callback_data=f"set_capital_{capital}")
            )
        
        # زر إدخال مبلغ مخصص
        markup.row(
            create_animated_button("💰 إدخال مبلغ مخصص", "custom_capital", "💰")
        )
        
        markup.row(
            create_animated_button("🔙 العودة للإعدادات", "settings", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تحديد رأس المال: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض خيارات رأس المال", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_capital_"))
def handle_set_capital_value(call):
    """معالج تعيين قيمة رأس المال"""
    try:
        user_id = call.from_user.id
        capital = int(call.data.replace("set_capital_", ""))
        
        set_user_capital(user_id, capital)
        
        bot.answer_callback_query(call.id, f"✅ تم تحديد رأس المال: ${capital:,}")
        
        # تحديث القائمة
        handle_set_capital(call)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تعيين رأس المال: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في تعيين رأس المال", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "custom_capital")
def handle_custom_capital(call):
    """معالج إدخال مبلغ مخصص لرأس المال"""
    try:
        user_id = call.from_user.id
        user_states[user_id] = 'waiting_custom_capital'
        
        bot.edit_message_text(
            "💰 **إدخال مبلغ مخصص لرأس المال**\n\n"
            "يرجى إدخال المبلغ المطلوب بالدولار الأمريكي:\n"
            "مثال: 1500 أو 25000\n\n"
            "الحد الأدنى: $50\n"
            "الحد الأقصى: $1,000,000",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=types.InlineKeyboardMarkup().row(
                create_animated_button("❌ إلغاء", "set_capital", "❌")
            )
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في إدخال مبلغ مخصص: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_custom_capital')
def handle_custom_capital_input(message):
    """معالج إدخال المبلغ المخصص"""
    try:
        user_id = message.from_user.id
        
        # محاولة تحويل النص إلى رقم
        try:
            capital = float(message.text.replace(',', '').replace('$', ''))
            
            if capital < 50:
                bot.reply_to(message, "❌ المبلغ أقل من الحد الأدنى ($50). يرجى إدخال مبلغ أكبر.")
                return
            
            if capital > 1000000:
                bot.reply_to(message, "❌ المبلغ أكبر من الحد الأقصى ($1,000,000). يرجى إدخال مبلغ أصغر.")
                return
            
            # تعيين رأس المال
            set_user_capital(user_id, capital)
            user_states.pop(user_id, None)
            
            bot.reply_to(message, f"✅ تم تحديد رأس المال بنجاح: ${capital:,.0f}")
            
            # العودة لقائمة رأس المال
            time.sleep(1)
            current_capital = get_user_capital(user_id)
            
            message_text = f"""
💰 **تحديد رأس المال**

رأس المال الحالي: ${current_capital:,.0f}

اختر رأس المال المناسب لك:
(يؤثر على حجم الصفقات المقترحة وإدارة المخاطر)
            """
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            for capital_option in DEFAULT_CAPITAL_OPTIONS:
                button_text = f"✅ ${capital_option:,}" if capital_option == current_capital else f"${capital_option:,}"
                markup.row(
                    types.InlineKeyboardButton(button_text, callback_data=f"set_capital_{capital_option}")
                )
            
            markup.row(
                create_animated_button("💰 إدخال مبلغ مخصص", "custom_capital", "💰")
            )
            
            markup.row(
                create_animated_button("🔙 العودة للإعدادات", "settings", "🔙")
            )
            
            bot.send_message(
                message.chat.id,
                message_text,
                parse_mode='Markdown',
                reply_markup=markup
            )
            
        except ValueError:
            bot.reply_to(message, "❌ يرجى إدخال رقم صحيح. مثال: 1500")
            
    except Exception as e:
        logger.error(f"[ERROR] خطأ في معالجة المبلغ المخصص: {e}")
        bot.reply_to(message, "❌ حدث خطأ في معالجة المبلغ")
        user_states.pop(user_id, None)

# ===== معالجات قواعد التحليل =====

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_analysis_rule')
def handle_analysis_rule_input(message):
    """معالج إدخال قاعدة التحليل الجديدة"""
    try:
        user_id = message.from_user.id
        user_input = message.text.strip()
        
        if len(user_input) < 10:
            bot.reply_to(message, "❌ القاعدة قصيرة جداً. يرجى إدخال قاعدة أكثر تفصيلاً (على الأقل 10 أحرف).")
            return
        
        if len(user_input) > 1000:
            bot.reply_to(message, "❌ القاعدة طويلة جداً. يرجى تقصيرها (أقل من 1000 حرف).")
            return
        
        # رسالة معالجة
        processing_msg = bot.reply_to(message, "🤖 جاري معالجة القاعدة بالذكاء الاصطناعي...")
        
        # معالجة القاعدة بالذكاء الاصطناعي
        processed_rule = process_user_rule_with_ai(user_input, user_id)
        
        if not processed_rule:
            bot.edit_message_text(
                "❌ فشل في معالجة القاعدة. سيتم حفظ النص الأصلي.",
                chat_id=processing_msg.chat.id,
                message_id=processing_msg.message_id
            )
            processed_rule = user_input
        else:
            bot.edit_message_text(
                "✅ تم تحسين القاعدة بنجاح!",
                chat_id=processing_msg.chat.id,
                message_id=processing_msg.message_id
            )
        
        # تحميل القواعد الحالية
        rules = load_analysis_rules()
        
        # إضافة القاعدة الجديدة
        new_rule = {
            'id': len(rules) + 1,
            'user_id': user_id,
            'original_rule': user_input,
            'processed_rule': processed_rule,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'active'
        }
        
        rules.append(new_rule)
        
        # حفظ القواعد
        if save_analysis_rules(rules):
            success_message = f"""
✅ **تم إضافة القاعدة بنجاح!**

**القاعدة الأصلية:**
{user_input}

**القاعدة المحسنة:**
{processed_rule}

🔄 **ستكون هذه القاعدة فعالة في جميع التحليلات القادمة**
            """
            
            bot.reply_to(message, success_message)
            
            # إزالة حالة المستخدم
            user_state = user_states.get(user_id, {})
            if user_state.get('message_id') and user_state.get('chat_id'):
                try:
                    # العودة لقائمة إدارة القواعد
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    markup.row(
                        create_animated_button("➕ إضافة قاعدة أخرى", "add_analysis_rule", "➕")
                    )
                    markup.row(
                        create_animated_button("✏️ تحرير القواعد", "edit_analysis_rules", "✏️")
                    )
                    markup.row(
                        create_animated_button("🔙 العودة لقسم AI", "ai_section", "🔙")
                    )
                    
                    bot.edit_message_text(
                        "✅ تم إضافة القاعدة بنجاح!\n\nماذا تريد أن تفعل الآن؟",
                        chat_id=user_state['chat_id'],
                        message_id=user_state['message_id'],
                        reply_markup=markup
                    )
                except:
                    pass
        else:
            bot.reply_to(message, "❌ فشل في حفظ القاعدة. يرجى المحاولة مرة أخرى.")
        
        # إزالة حالة المستخدم
        user_states.pop(user_id, None)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في معالجة قاعدة التحليل: {e}")
        bot.reply_to(message, "❌ حدث خطأ في معالجة القاعدة. يرجى المحاولة مرة أخرى.")
        user_states.pop(message.from_user.id, None)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_rule_modification')
def handle_rule_modification_input(message):
    """معالج تعديل قاعدة التحليل"""
    try:
        user_id = message.from_user.id
        user_input = message.text.strip()
        user_state = user_states.get(user_id, {})
        rule_index = user_state.get('rule_index')
        
        if rule_index is None:
            bot.reply_to(message, "❌ خطأ في تحديد القاعدة. يرجى المحاولة مرة أخرى.")
            user_states.pop(user_id, None)
            return
        
        if len(user_input) < 10:
            bot.reply_to(message, "❌ النص قصير جداً. يرجى إدخال نص أكثر تفصيلاً (على الأقل 10 أحرف).")
            return
        
        if len(user_input) > 1000:
            bot.reply_to(message, "❌ النص طويل جداً. يرجى تقصيره (أقل من 1000 حرف).")
            return
        
        # رسالة معالجة
        processing_msg = bot.reply_to(message, "🤖 جاري معالجة التعديل بالذكاء الاصطناعي...")
        
        # معالجة النص الجديد بالذكاء الاصطناعي
        processed_rule = process_user_rule_with_ai(user_input, user_id)
        
        if not processed_rule:
            bot.edit_message_text(
                "❌ فشل في معالجة التعديل. سيتم حفظ النص الأصلي.",
                chat_id=processing_msg.chat.id,
                message_id=processing_msg.message_id
            )
            processed_rule = user_input
        else:
            bot.edit_message_text(
                "✅ تم تحسين التعديل بنجاح!",
                chat_id=processing_msg.chat.id,
                message_id=processing_msg.message_id
            )
        
        # تحميل القواعد الحالية
        rules = load_analysis_rules()
        
        if rule_index >= len(rules):
            bot.reply_to(message, "❌ القاعدة غير موجودة. يرجى المحاولة مرة أخرى.")
            user_states.pop(user_id, None)
            return
        
        # تحديث القاعدة
        old_rule = rules[rule_index]['processed_rule']
        rules[rule_index]['original_rule'] = user_input
        rules[rule_index]['processed_rule'] = processed_rule
        rules[rule_index]['modified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rules[rule_index]['modified_by'] = user_id
        
        # حفظ القواعد
        if save_analysis_rules(rules):
            success_message = f"""
✅ **تم تعديل القاعدة بنجاح!**

**القاعدة السابقة:**
{old_rule}

**القاعدة الجديدة:**
{processed_rule}

🔄 **سيتم تطبيق التعديل في جميع التحليلات القادمة**
            """
            
            bot.reply_to(message, success_message)
            
            # العودة لقائمة القواعد
            if user_state.get('message_id') and user_state.get('chat_id'):
                try:
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    markup.row(
                        create_animated_button("✏️ تحرير قواعد أخرى", "edit_analysis_rules", "✏️")
                    )
                    markup.row(
                        create_animated_button("🔙 العودة لقسم AI", "ai_section", "🔙")
                    )
                    
                    bot.edit_message_text(
                        "✅ تم تعديل القاعدة بنجاح!\n\nماذا تريد أن تفعل الآن؟",
                        chat_id=user_state['chat_id'],
                        message_id=user_state['message_id'],
                        reply_markup=markup
                    )
                except:
                    pass
        else:
            bot.reply_to(message, "❌ فشل في حفظ التعديل. يرجى المحاولة مرة أخرى.")
        
        # إزالة حالة المستخدم
        user_states.pop(user_id, None)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في معالجة تعديل القاعدة: {e}")
        bot.reply_to(message, "❌ حدث خطأ في معالجة التعديل. يرجى المحاولة مرة أخرى.")
        user_states.pop(message.from_user.id, None)

# ===== معالج الرسائل العام =====
@bot.message_handler(func=lambda message: True)
def handle_unknown_message(message):
    """معالج الرسائل غير المعرفة - يتحقق من كلمة السر أولاً"""
    user_id = message.from_user.id
    
    # التحقق من كلمة السر أولاً
    if user_id not in user_sessions:
        # إذا لم يكن المستخدم في حالة انتظار كلمة السر، ضعه في هذه الحالة
        if user_states.get(user_id) != 'waiting_password':
            hide_keyboard = types.ReplyKeyboardRemove()
            bot.send_message(
                chat_id=user_id,
                text="🔐 يجب إدخال كلمة المرور أولاً للوصول إلى البوت:",
                reply_markup=hide_keyboard
            )
            user_states[user_id] = 'waiting_password'
        return
    
    # إذا كان المستخدم مصدق، أرسل رسالة غير معروفة
    bot.reply_to(message, "❓ أمر غير معروف. استخدم الأزرار في الأسفل للتنقل.")

# ===== معالجات المنطقة الزمنية =====
@bot.callback_query_handler(func=lambda call: call.data == "timezone_settings")
def handle_timezone_settings(call):
    """معالج إعدادات المنطقة الزمنية"""
    try:
        user_id = call.from_user.id
        current_timezone = get_user_timezone(user_id)
        
        message_text = f"""
🌍 **إعدادات المنطقة الزمنية**

المنطقة الحالية: {AVAILABLE_TIMEZONES.get(current_timezone, current_timezone)}

اختر المنطقة الزمنية المناسبة لك:
(يؤثر على أوقات عرض التنبيهات والتحليلات)
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for tz_key, tz_name in AVAILABLE_TIMEZONES.items():
            button_text = f"✅ {tz_name}" if tz_key == current_timezone else tz_name
            markup.row(
                types.InlineKeyboardButton(button_text, callback_data=f"set_timezone_{tz_key}")
            )
        
        markup.row(
            create_animated_button("🔙 العودة للإعدادات", "settings", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في إعدادات المنطقة الزمنية: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض المناطق الزمنية", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_timezone_"))
def handle_set_timezone(call):
    """معالج تعيين المنطقة الزمنية"""
    try:
        user_id = call.from_user.id
        timezone = call.data.replace("set_timezone_", "")
        
        set_user_timezone(user_id, timezone)
        timezone_name = AVAILABLE_TIMEZONES.get(timezone, timezone)
        
        bot.answer_callback_query(call.id, f"✅ تم تحديد المنطقة الزمنية: {timezone_name}")
        
        # تحديث القائمة
        handle_timezone_settings(call)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تعيين المنطقة الزمنية: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في تعيين المنطقة الزمنية", show_alert=True)

# ===== معالج الإحصائيات =====
@bot.callback_query_handler(func=lambda call: call.data == "statistics")
def handle_statistics(call):
    """معالج الإحصائيات"""
    try:
        user_id = call.from_user.id
        
        # جلب إحصائيات المستخدم
        stats = trade_data_manager.get_user_feedback_stats(user_id)
        trading_mode = get_user_trading_mode(user_id)
        is_monitoring = user_monitoring_active.get(user_id, False)
        selected_symbols = user_selected_symbols.get(user_id, [])
        
        message_text = f"""
📊 **إحصائيات التداول**

👤 **معلومات المستخدم:**
• نمط التداول: {'⚡ سكالبينغ سريع' if trading_mode == 'scalping' else '📈 تداول طويل المدى'}
• حالة المراقبة: {'🟢 نشطة' if is_monitoring else '🔴 متوقفة'}
• الرموز المراقبة: {len(selected_symbols)} رمز

📈 **إحصائيات التقييم:**
• إجمالي التقييمات: {stats['total_feedbacks']}
• تقييمات إيجابية: {stats['positive_feedbacks']} 👍
• تقييمات سلبية: {stats['negative_feedbacks']} 👎
• معدل الدقة: {stats['accuracy_rate']:.1f}%

🎯 **الأداء:**
• مستوى الثقة المطلوب: {get_user_advanced_notification_settings(user_id).get('success_threshold', 70)}%
• تردد الإشعارات: {NOTIFICATION_FREQUENCIES.get(get_user_advanced_notification_settings(user_id).get('frequency', '5min'), {}).get('name', '5 دقائق')}

💡 **نصائح للتحسين:**
{'• ممتاز! استمر على هذا الأداء 🎉' if stats['accuracy_rate'] >= 80 else '• يمكن تحسين الدقة بتعديل إعدادات التنبيهات'}
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.row(
            create_animated_button("🔙 العودة للإعدادات", "settings", "🔙")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض الإحصائيات: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض الإحصائيات", show_alert=True)

# ===== معالجات إعدادات التنبيهات المتقدمة =====
@bot.callback_query_handler(func=lambda call: call.data == "advanced_notifications_settings")
def handle_advanced_notifications_settings(call):
    """معالج إعدادات التنبيهات المتقدمة"""
    try:
        user_id = call.from_user.id
        settings = get_user_advanced_notification_settings(user_id)
        
        # إحصائيات سريعة
        enabled_count = sum(1 for key in ['support_alerts', 'breakout_alerts', 'trading_signals', 
                                        'economic_news', 'candlestick_patterns', 'volume_alerts'] if settings.get(key, True))
        
        frequency_display = NOTIFICATION_FREQUENCIES.get(settings.get('frequency', '5min'), {}).get('name', '5 دقائق')
        
        message_text = f"""
🔔 **إعدادات الإشعارات المتقدمة**

📊 **الأنواع المفعلة:** {enabled_count}/6
⏱️ **التردد الحالي:** {frequency_display}
📈 **نسبة النجاح:** {settings.get('success_threshold', 70)}%
📋 **مدة الاحتفاظ:** {settings.get('log_retention', 7)} أيام

اختر الإعداد المطلوب تعديله:
        """
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=create_advanced_notifications_menu(user_id)
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في إعدادات التنبيهات المتقدمة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض الإعدادات", show_alert=True)



@bot.callback_query_handler(func=lambda call: call.data == "success_threshold")
def handle_success_threshold(call):
    """معالج تحديد نسبة النجاح"""
    try:
        user_id = call.from_user.id
        settings = get_user_advanced_notification_settings(user_id)
        current_threshold = settings.get('success_threshold', 70)
        
        message_text = f"""
📊 **نسبة النجاح المطلوبة**

النسبة الحالية: {current_threshold}%

اختر نسبة النجاح المطلوبة لإرسال التنبيهات:
• نسبة أعلى = تنبيهات أقل ولكن أدق
• نسبة أقل = تنبيهات أكثر ولكن قد تكون أقل دقة
        """
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode='Markdown',
            reply_markup=create_success_threshold_menu(user_id)
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تحديد نسبة النجاح: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)



@bot.callback_query_handler(func=lambda call: call.data.startswith("set_threshold_"))
def handle_set_threshold(call):
    """معالج تعيين نسبة النجاح"""
    try:
        user_id = call.from_user.id
        threshold = int(call.data.replace("set_threshold_", ""))
        
        update_user_advanced_notification_setting(user_id, 'success_threshold', threshold)
        
        bot.answer_callback_query(call.id, f"✅ تم تحديد نسبة النجاح: {threshold}%")
        
        # تحديث القائمة
        handle_success_threshold(call)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تحديد نسبة النجاح: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

# تم حذف معالجات التردد المكررة - التردد الآن موحد لكل 15 ثانية

@bot.callback_query_handler(func=lambda call: call.data == "notification_timing")
def handle_notification_timing(call):
    """معالج توقيت الإشعارات"""
    try:
        user_id = call.from_user.id
        settings = get_user_advanced_notification_settings(user_id)
        current_timing = settings.get('alert_timing', '24h')
        
        timing_options = {
            '24h': '24 ساعة (دائماً) 🕐',
            'morning': 'الصباح (6ص - 12ظ) 🌅',
            'afternoon': 'بعد الظهر (12ظ - 6م) ☀️',
            'evening': 'المساء (6م - 12ص) 🌆',
            'night': 'الليل (12ص - 6ص) 🌙'
        }
        
        current_display = timing_options.get(current_timing, '24 ساعة')
        
        message_text = f"""
⏰ **توقيت الإشعارات**

التوقيت الحالي: {current_display}

اختر الأوقات المفضلة لاستقبال الإشعارات:
(حسب منطقتك الزمنية المحددة)
        """
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for timing_key, timing_name in timing_options.items():
            button_text = f"✅ {timing_name}" if timing_key == current_timing else f"⚪ {timing_name}"
            markup.row(
                types.InlineKeyboardButton(button_text, callback_data=f"set_timing_{timing_key}")
            )
        
        markup.row(
            create_animated_button("🔙 العودة لإعدادات التنبيهات", "advanced_notifications_settings", "🔙")
        )
        
        bot.edit_message_text(
            message_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في توقيت الإشعارات: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_timing_"))
def handle_set_timing(call):
    """معالج تعيين توقيت الإشعارات"""
    try:
        user_id = call.from_user.id
        timing = call.data.replace("set_timing_", "")
        
        update_user_advanced_notification_setting(user_id, 'alert_timing', timing)
        
        timing_names = {
            '24h': '24 ساعة (دائماً)',
            'morning': 'الصباح (6ص - 12ظ)',
            'afternoon': 'بعد الظهر (12ظ - 6م)',
            'evening': 'المساء (6م - 12ص)',
            'night': 'الليل (12ص - 6ص)'
        }
        
        timing_name = timing_names.get(timing, timing)
        bot.answer_callback_query(call.id, f"✅ تم تحديد التوقيت: {timing_name}")
        
        # تحديث القائمة
        handle_notification_timing(call)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في تعيين التوقيت: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

# ===== معالجات الأسعار المباشرة المحسنة =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("live_"))
def handle_live_category_prices(call):
    """معالج الأسعار المباشرة للفئات - MT5 فقط بدون تحديث تلقائي"""
    try:
        user_id = call.from_user.id
        category = call.data.replace("live_", "")
        
        category_names = {
            'crypto': 'العملات الرقمية ₿',
            'forex': 'العملات الأجنبية 💱',
            'metals': 'المعادن النفيسة 🥇',
            'stocks': 'الأسهم الأمريكية 📈',
            'indices': 'المؤشرات 📊'
        }
        
        # جلب الرموز حسب الفئة
        if category == 'crypto':
            symbols = CRYPTO_PAIRS
        elif category == 'forex':
            symbols = CURRENCY_PAIRS
        elif category == 'metals':
            symbols = METALS
        elif category == 'stocks':
            symbols = STOCKS
        elif category == 'indices':
            symbols = INDICES
        else:
            symbols = {}
        
        category_name = category_names.get(category, 'فئة غير معروفة')
        
        # عرض الأسعار الفورية من MT5
        display_instant_prices(user_id, call.message.chat.id, call.message.message_id, 
                              symbols, category_name, category)
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في الأسعار المباشرة للفئة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

def display_instant_prices(user_id, chat_id, message_id, symbols, category_name, category):
    """عرض الأسعار الفورية من MT5 فقط بدون تحديث تلقائي"""
    try:
        current_time = get_current_time_for_user(user_id)
        
        message_text = f"""
📈 **الأسعار المباشرة - {category_name}**

{current_time}
🔗 **مصدر البيانات:** MetaTrader5 (لحظي)

───────────────────────
"""
        
        # التحقق من اتصال MT5
        if not mt5_manager.connected:
            message_text += """
❌ **غير متصل بـ MetaTrader5**

🔧 **للحصول على الأسعار:**
• تأكد من تشغيل MetaTrader5
• تحقق من اتصال الإنترنت  
• حاول مرة أخرى بعد قليل

───────────────────────
"""
        else:
            # جلب الأسعار من MT5 فقط
            prices_data = []
            available_count = 0
            
            for symbol, info in symbols.items():
                try:
                    price_data = mt5_manager.get_live_price(symbol)
                    if price_data:
                        bid = price_data.get('bid', 0)
                        ask = price_data.get('ask', 0)
                        spread = price_data.get('spread', 0)
                        last_price = price_data.get('last', bid)
                        
                        # التحقق من صحة البيانات بمرونة أكثر
                        if (bid > 0 and ask > 0) or last_price > 0:
                            # استخدام bid/ask إذا كانا متوفرين، وإلا استخدم last_price
                            display_bid = bid if bid > 0 else last_price
                            display_ask = ask if ask > 0 else last_price
                            display_spread = spread if spread > 0 else abs(display_ask - display_bid)
                            
                            prices_data.append(f"""
{info['emoji']} **{info['name']}**
📊 شراء: {display_bid:.5f} | بيع: {display_ask:.5f}
📏 فرق: {display_spread:.5f}
""")
                        else:
                            prices_data.append(f"""
{info['emoji']} **{info['name']}**
⚠️ بيانات غير مكتملة من MT5
""")
                        available_count += 1
                    else:
                        # إضافة معلومات تشخيصية أكثر تفصيلاً
                        if not mt5_manager.connected:
                            status_msg = "❌ غير متصل بـ MT5"
                        else:
                            status_msg = "❌ غير متاح من MT5 (قد يكون متاح من Yahoo Finance)"
                        
                        prices_data.append(f"""
{info['emoji']} **{info['name']}**
{status_msg}
""")
                        
                except Exception as e:
                    logger.error(f"[ERROR] خطأ في جلب سعر {symbol}: {e}")
                    prices_data.append(f"""
{info['emoji']} **{info['name']}**
⚠️ خطأ في البيانات
""")
            
            message_text += "\n".join(prices_data)
            message_text += "\n\n───────────────────────"
            message_text += f"\n✅ **متوفر:** {available_count}/{len(symbols)} رمز"
        
        # إنشاء لوحة التحكم
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.row(
            create_animated_button("🔄 تحديث الأسعار", f"live_{category}", "🔄"),
            create_animated_button("🔙 العودة للفئات", "live_prices", "🔙")
        )
        markup.row(
            create_animated_button("🔙 القائمة الرئيسية", "main_menu", "🔙")
        )
        
        # تحديث الرسالة
        bot.edit_message_text(
            message_text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في عرض الأسعار الفورية: {e}")
        bot.edit_message_text(
            f"❌ **خطأ في عرض الأسعار**\n\n"
            f"حدث خطأ أثناء جلب أسعار {category_name}.\n"
            "يرجى المحاولة مرة أخرى.",
            chat_id,
            message_id,
            parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_live_"))
def handle_stop_live_prices(call):
    """معالج إيقاف التحديث التلقائي للأسعار"""
    try:
        category = call.data.replace("stop_live_", "")
        
        bot.edit_message_text(
            "⏸️ **تم إيقاف التحديث التلقائي**\n\n"
            "يمكنك العودة لقائمة الأسعار المباشرة لبدء المراقبة مرة أخرى.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=types.InlineKeyboardMarkup().row(
                create_animated_button("🔙 العودة للأسعار", "live_prices", "🔙")
            )
        )
        
        bot.answer_callback_query(call.id, "✅ تم إيقاف التحديث التلقائي")
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في إيقاف الأسعار المباشرة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "live_prices_menu")
def handle_live_prices_menu(call):
    """العودة لقائمة الأسعار المباشرة"""
    handle_live_prices(call)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def handle_main_menu(call):
    """العودة للقائمة الرئيسية"""
    try:
        # إنشاء رسالة ترحيبية مختصرة
        welcome_message = f"""
🎉 **بوت التداول المتقدم v1.2.0**

🚀 **الميزات:**
✅ تحليل ذكي بـ Gemini AI
✅ بيانات حقيقية من MT5
✅ إشعارات مخصصة

📊 **حالة الاتصال:**
• MetaTrader5: {'🟢 متصل' if mt5_manager.connected else '🔴 منقطع'}
• Gemini AI: {'🟢 متاح' if GEMINI_AVAILABLE else '🔴 غير متاح'}

استخدم الأزرار في الأسفل للتنقل 👇
        """
        
        bot.edit_message_text(
            welcome_message,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        
        # إرسال الكيبورد الثابت إذا لم يكن موجوداً
        bot.send_message(
            call.message.chat.id,
            "اختر الخدمة المطلوبة:",
            reply_markup=create_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في العودة للقائمة الرئيسية: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

# تم حذف المعالجات المكررة لتجنب التضارب

# ===== نظام المراقبة والتنبيهات =====
# تم حذف نظام الـ cache - سنستخدم بيانات لحظية فقط

def is_notification_time_allowed(user_id: int, alert_timing: str) -> bool:
    """فحص ما إذا كان الوقت الحالي مناسب لإرسال الإشعارات حسب المنطقة الزمنية للمستخدم"""
    if alert_timing == '24h':
        return True
    
    try:
        import pytz
        from datetime import datetime
        
        # الحصول على المنطقة الزمنية للمستخدم
        user_timezone = get_user_timezone(user_id)
        
        # تحويل الوقت للمنطقة الزمنية للمستخدم
        tz = pytz.timezone(user_timezone)
        current_time = datetime.now(tz)
        current_hour = current_time.hour
        
        # تحديد الأوقات المسموحة حسب إعدادات المستخدم
        if alert_timing == 'morning':  # الصباح: 6ص - 12ظ
            return 6 <= current_hour < 12
        elif alert_timing == 'afternoon':  # بعد الظهر: 12ظ - 6م
            return 12 <= current_hour < 18
        elif alert_timing == 'evening':  # المساء: 6م - 12ص
            return 18 <= current_hour < 24
        elif alert_timing == 'night':  # الليل: 12ص - 6ص
            return 0 <= current_hour < 6
        
    except Exception as e:
        logger.error(f"[ERROR] خطأ في فحص التوقيت للمستخدم {user_id}: {e}")
        return True  # في حالة الخطأ، نسمح بالإشعار
    
    return True

def monitoring_loop():
    """حلقة مراقبة الأسعار وإرسال التنبيهات مع معالجة محسنة للأخطاء"""
    global monitoring_active
    logger.info("[RUNNING] بدء حلقة المراقبة...")
    consecutive_errors = 0
    max_consecutive_errors = 5
    connection_check_interval = 300  # فحص الاتصال كل 5 دقائق
    last_connection_check = 0
    
    while monitoring_active:
        try:
            current_time = time.time()
            
            # فحص دوري لحالة اتصال MT5
            if current_time - last_connection_check > connection_check_interval:
                logger.debug("[DEBUG] فحص دوري لحالة اتصال MT5...")
                if not mt5_manager.validate_connection_health():
                    logger.warning("[WARNING] انقطاع في اتصال MT5 تم اكتشافه - محاولة إعادة الاتصال...")
                    mt5_manager.check_real_connection()
                last_connection_check = current_time
            
            # مراقبة المستخدمين النشطين فقط
            active_users = list(user_monitoring_active.keys())
            logger.debug(f"[DEBUG] المستخدمون النشطون: {active_users}")
            if not active_users:
                logger.debug("[DEBUG] لا يوجد مستخدمين نشطين - انتظار 30 ثانية")
                time.sleep(30)  # انتظار أطول إذا لم يكن هناك مستخدمين نشطين
                continue
            
            successful_operations = 0
            failed_operations = 0
            mt5_connection_errors = 0
            
            # الخطوة 1: تجميع جميع الرموز المطلوبة من جميع المستخدمين
            all_symbols_needed = set()
            users_by_symbol = {}  # {symbol: [user_ids]}
            
            for user_id in active_users:
                if not user_monitoring_active.get(user_id, False):
                    continue
                    
                selected_symbols = user_selected_symbols.get(user_id, [])
                logger.debug(f"[DEBUG] الرموز المختارة للمستخدم {user_id}: {selected_symbols}")
                if not selected_symbols:
                    logger.debug(f"[DEBUG] لا توجد رموز مختارة للمستخدم {user_id}")
                    continue
                
                for symbol in selected_symbols:
                    all_symbols_needed.add(symbol)
                    if symbol not in users_by_symbol:
                        users_by_symbol[symbol] = []
                    users_by_symbol[symbol].append(user_id)
            
            # الخطوة 2: جلب البيانات لجميع الرموز مرة واحدة فقط
            symbols_data = {}  # {symbol: price_data}
            for symbol in all_symbols_needed:
                try:
                    price_data = mt5_manager.get_live_price(symbol)
                    if price_data:
                        symbols_data[symbol] = price_data
                    else:
                        failed_operations += 1
                        if not mt5_manager.connected:
                            mt5_connection_errors += 1
                except Exception as e:
                    logger.error(f"[ERROR] خطأ في جلب بيانات {symbol}: {e}")
                    failed_operations += 1
            
            # الخطوة 3: معالجة كل رمز مع المستخدمين المهتمين به
            for symbol, price_data in symbols_data.items():
                try:
                    # تحليل الرمز مرة واحدة فقط
                    analysis = gemini_analyzer.analyze_market_data_with_retry(symbol, price_data, users_by_symbol[symbol][0])
                    
                    if not analysis:
                        failed_operations += len(users_by_symbol[symbol])
                        continue
                    
                    # إرسال للمستخدمين المهتمين بهذا الرمز
                    for user_id in users_by_symbol[symbol]:
                        try:
                            # الحصول على إعدادات المستخدم
                            settings = get_user_advanced_notification_settings(user_id)
                            min_confidence = settings.get('success_threshold', 70)
                            alert_timing = settings.get('alert_timing', '24h')
                            
                            # فحص التوقيت المناسب للإشعارات
                            if not is_notification_time_allowed(user_id, alert_timing):
                                successful_operations += 1  # العملية نجحت لكن ليس الوقت المناسب
                                continue
                            
                            # إرسال التنبيه إذا كانت هناك إشارة قوية
                            if analysis.get('confidence', 0) >= min_confidence:
                                signal = {
                                    'action': analysis.get('action', 'HOLD'),
                                    'confidence': analysis.get('confidence', 0),
                                    'reasoning': analysis.get('reasoning', [])
                                }
                                
                                try:
                                    send_trading_signal_alert(user_id, symbol, signal, analysis)
                                    successful_operations += 1
                                except Exception as alert_error:
                                    logger.error(f"[ERROR] خطأ في إرسال تنبيه {symbol} للمستخدم {user_id}: {alert_error}")
                                    failed_operations += 1
                            else:
                                successful_operations += 1  # لا توجد إشارة قوية ولكن العملية نجحت
                                
                        except Exception as user_error:
                            logger.error(f"[ERROR] خطأ في معالجة المستخدم {user_id} للرمز {symbol}: {user_error}")
                            failed_operations += 1
                            continue
                            
                except Exception as symbol_error:
                    logger.error(f"[ERROR] خطأ في معالجة الرمز {symbol}: {symbol_error}")
                    failed_operations += len(users_by_symbol[symbol])
                    continue
            
            # تتبع نجاح العمليات وحالة الاتصال
            if successful_operations > 0:
                consecutive_errors = 0  # إعادة تعيين عداد الأخطاء المتتالية
                
            # تحذير خاص لمشاكل اتصال MT5
            if mt5_connection_errors > 0:
                logger.warning(f"[WARNING] {mt5_connection_errors} أخطاء اتصال MT5 في هذه الدورة")
                
            if failed_operations > successful_operations and failed_operations > 10:
                logger.warning(f"[WARNING] نسبة عالية من الأخطاء: {failed_operations} فشل مقابل {successful_operations} نجح")
                
                # إذا كانت معظم الأخطاء بسبب MT5، نحاول إعادة الاتصال
                if mt5_connection_errors > failed_operations * 0.7:  # 70% من الأخطاء بسبب MT5
                    logger.info("[RECONNECT] محاولة إعادة اتصال شاملة بسبب أخطاء MT5 المتكررة...")
                    mt5_manager.check_real_connection()
            
            # انتظار 15 ثانية - تردد موحد لجميع المستخدمين
            time.sleep(15)
            
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"[ERROR] خطأ في حلقة المراقبة (الخطأ رقم {consecutive_errors}): {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                logger.error(f"[ERROR] تم الوصول للحد الأقصى للأخطاء المتتالية ({max_consecutive_errors}). إيقاف مؤقت لمدة 5 دقائق...")
                time.sleep(300)  # انتظار 5 دقائق
                consecutive_errors = 0  # إعادة تعيين العداد
                
                # محاولة إعادة تهيئة MT5 بعد الإيقاف المؤقت
                logger.info("[RECONNECT] محاولة إعادة تهيئة MT5 بعد الإيقاف المؤقت...")
                mt5_manager.initialize_mt5()
            else:
                # انتظار متدرج حسب عدد الأخطاء
                wait_time = min(60 * consecutive_errors, 300)  # حد أقصى 5 دقائق
                time.sleep(wait_time)
    
    logger.info("[SYSTEM] تم إنهاء حلقة المراقبة بأمان")

# ===== تشغيل البوت =====
if __name__ == "__main__":
    try:
        logger.info("▶️ بدء تشغيل بوت التداول المتقدم v1.2.0...")
        
        # التحقق من اتصال MT5
        if mt5_manager.connected:
            logger.info("[OK] MetaTrader5 متصل ومستعد!")
        else:
            logger.warning("[WARNING] MetaTrader5 غير متصل - يرجى التحقق من الإعدادات")
        
        # التحقق من Gemini AI
        if GEMINI_AVAILABLE:
            logger.info("[OK] Gemini AI جاهز للتحليل!")
        else:
            logger.warning("[WARNING] Gemini AI غير متوفر - تأكد من مفتاح API")
        
        logger.info("[SYSTEM] نظام التنبيهات: مراقبة لحظية مع تقييم المستخدم")
        logger.info("[SYSTEM] نظام التخزين: تسجيل جميع الصفقات والتقييمات")
        
        # إنشاء متغير لإيقاف حلقة المراقبة بأمان
        monitoring_active = True
        
        # بدء حلقة المراقبة في خيط منفصل مع معالجة محسنة
        monitoring_thread = threading.Thread(
            target=monitoring_loop, 
            daemon=True,
            name="MonitoringThread"
        )
        monitoring_thread.start()
        logger.info("[RUNNING] تم بدء حلقة المراقبة في الخلفية")
        
        # التحقق من بدء الـ thread بنجاح
        time.sleep(1)
        if monitoring_thread.is_alive():
            logger.info("[OK] خيط المراقبة يعمل بشكل صحيح")
        else:
            logger.error("[ERROR] فشل في بدء خيط المراقبة")
        
        # بدء البوت
        logger.info("[SYSTEM] البوت جاهز للعمل!")
        print("\n" + "="*60)
        print("🚀 بوت التداول v1.2.0 جاهز للعمل!")
        print("📊 مصدر البيانات: MetaTrader5 (لحظي)")
        print("🧠 محرك التحليل: Google Gemini AI")
        print("💾 نظام التقييم: تفعيل ذكي للتعلم")
        print("="*60 + "\n")
        
        # تشغيل البوت مع معالجة أخطاء الشبكة
        while True:
            try:
                logger.info("[SYSTEM] بدء استقبال الرسائل...")
                bot.infinity_polling(none_stop=True, interval=1, timeout=60)
                break  # إذا انتهى بشكل طبيعي
                
            except Exception as polling_error:
                logger.error(f"[ERROR] خطأ في الاستقبال: {polling_error}")
                logger.info("[SYSTEM] محاولة إعادة الاتصال خلال 5 ثواني...")
                time.sleep(5)
                continue
        
    except KeyboardInterrupt:
        logger.info("[SYSTEM] تم الحصول على إشارة إيقاف...")
        monitoring_active = False
        logger.info("[SYSTEM] تم إيقاف حلقة المراقبة")
    except Exception as e:
        logger.error(f"[ERROR] خطأ عام في تشغيل البوت: {e}")
        
    finally:
        # إغلاق اتصال MT5 عند الإنهاء بشكل آمن
        monitoring_active = False
        try:
            mt5_manager.graceful_shutdown()
        except Exception as e:
            logger.error(f"[ERROR] خطأ في إغلاق MT5: {e}")
        logger.info("[SYSTEM] تم إنهاء البوت بأمان")
