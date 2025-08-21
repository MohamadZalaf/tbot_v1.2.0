#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📋 ملف الإعدادات - بوت التداول v1.2.0
==================================================

ملف الإعدادات الرئيسي للبوت مع المفاتيح المحدثة
"""

# ===== إعدادات البوت الأساسية =====

# رمز بوت Telegram
BOT_TOKEN = '7703327028:AAHLqgR1HtVPsq6LfUKEWzNEgLZjJPLa6YU'

# كلمة مرور البوت
BOT_PASSWORD = 'tra12345678'

# مفتاح Google Gemini AI
GEMINI_API_KEY = 'AIzaSyDAOp1ARgrkUvPcmGmXddFx8cqkzhy-3O8'
# قائمة مفاتيح بديلة للتبديل التلقائي عند حدود RPD/Quota (ضع مفاتيح إضافية هنا إن وجدت)
GEMINI_API_KEYS = [GEMINI_API_KEY]

# ===== إعدادات MetaTrader5 =====

# معلومات الحساب (اختيارية - للاتصال التلقائي)
MT5_LOGIN = None  # رقم الحساب
MT5_PASSWORD = None  # كلمة مرور الحساب  
MT5_SERVER = None  # اسم الخادم

# ===== إعدادات المراقبة =====

# تردد فحص الأسعار (بالثواني)
MONITORING_INTERVAL = 30

# الحد الأدنى لمستوى الثقة لإرسال الإشعارات (0-100)
MIN_CONFIDENCE_THRESHOLD = 70

# أقصى عدد إشعارات يومية لكل مستخدم
MAX_DAILY_ALERTS = 50

# ===== إعدادات Gemini AI =====

# نموذج Gemini المستخدم
GEMINI_MODEL = 'gemini-2.0-flash'

# إعدادات توليد المحتوى
GEMINI_GENERATION_CONFIG = {
    'temperature': 0.7,
    'top_p': 0.8,
    'top_k': 40,
    'max_output_tokens': 1024,
}

# إعدادات الأمان
GEMINI_SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH", 
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]

# حدود جلسة المحادثة والسياق
# الحد الأقصى التقريبي لسياق الجلسة لكل رمز قبل فتح جلسة جديدة (تقديري لحماية من الاستهلاك)
GEMINI_CONTEXT_TOKEN_LIMIT = 120000
# بدء جلسة جديدة عند بلوغ هذه النسبة من الحد
GEMINI_CONTEXT_NEAR_LIMIT_RATIO = 0.85
# تفعيل التبديل التلقائي للمفاتيح عند ظهور أخطاء معدل/كوتا
GEMINI_ROTATE_ON_RATE_LIMIT = True

# حفظ سجلات المحادثة لكل رمز
SAVE_CHAT_LOGS = True
CHAT_LOG_RETENTION_DAYS = 7

# ===== إعدادات إدارة المخاطر =====

# نسب الهدف ووقف الخسارة الافتراضية
DEFAULT_TAKE_PROFIT_PERCENTAGE = 3.0  # 3%
DEFAULT_STOP_LOSS_PERCENTAGE = 1.0    # 1%

# إعدادات خاصة بنمط التداول
TRADING_MODE_SETTINGS = {
    'scalping': {
        'min_confidence': 80,
        'take_profit_pct': 1.5,
        'stop_loss_pct': 0.5,
        'max_daily_alerts': 30
    },
    'longterm': {
        'min_confidence': 60,
        'take_profit_pct': 5.0,
        'stop_loss_pct': 2.0,
        'max_daily_alerts': 10
    }
}

# ===== إعدادات التنبيهات الافتراضية =====
DEFAULT_NOTIFICATION_SETTINGS = {
    'support_alerts': True,         # تنبيهات مستوى الدعم
    'breakout_alerts': True,        # تنبيهات اختراق المستويات
    'trading_signals': True,        # إشارات التداول
    'economic_news': False,         # الأخبار الاقتصادية
    'candlestick_patterns': True,   # أنماط الشموع
    'volume_alerts': True,          # تنبيهات حجم التداول
    'success_threshold': 70,        # نسبة النجاح الدنيا
    'frequency': '5min',            # تردد الإشعارات
    'alert_timing': '24h',          # توقيت الإشعارات
    'log_retention': 7              # مدة الاحتفاظ بالسجل (أيام)
}

# ===== إعدادات المنطقة الزمنية =====

# المنطقة الزمنية الافتراضية
DEFAULT_TIMEZONE = 'Asia/Baghdad'

# خيارات المنطقة الزمنية المتاحة
AVAILABLE_TIMEZONES = {
    "Asia/Baghdad": "🇮🇶 بغداد (UTC+3)",
    "Asia/Riyadh": "🇸🇦 الرياض (UTC+3)", 
    "Asia/Kuwait": "🇰🇼 الكويت (UTC+3)",
    "Asia/Qatar": "🇶🇦 الدوحة (UTC+3)",
    "Asia/Dubai": "🇦🇪 دبي (UTC+4)",
    "Europe/Cairo": "🇪🇬 القاهرة (UTC+2)",
    "Europe/Istanbul": "🇹🇷 إستطنبول (UTC+3)",
    "Europe/London": "🇬🇧 لندن (UTC+0)",
    "Europe/Berlin": "🇩🇪 برلين (UTC+1)",
    "America/New_York": "🇺🇸 نيويورك (UTC-5)",
}

# ===== رؤوس الأموال الافتراضية =====
DEFAULT_CAPITAL_OPTIONS = [
    100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000
]