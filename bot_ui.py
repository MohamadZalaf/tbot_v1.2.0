#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 Trading Bot UI Controller v1.2.0 - ENHANCED EMBEDDED VERSION
==============================================================
Arabic GUI Interface for Advanced Trading Bot Control with Full Embedding

Features:
- Complete bot code embedding (no external .py files needed)
- Password-protected user management with ban/unban functionality
- Settings window with tabbed interface
- Gemini API key management with status checking
- MT5 login configuration
- Real-time user count display
- Enhanced security and control

Developer: Mohamad Zalaf ©️2025
Compatible with: Embedded tbot_v1.2.0.py + config.py
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, simpledialog
import subprocess
import os
import sys
import threading
import time
import json
import base64
from typing import Dict, List, Optional, Any
import glob
import io

# ===============================================
# EMBEDDED RESOURCES (BASE64 ENCODED)
# ===============================================

# Embedded config data
EMBEDDED_CONFIG = {
    'BOT_TOKEN': '7703327028:AAHLqgR1HtVPsq6LfUKEWzNEgLZjJPLa6YU',
    'BOT_PASSWORD': 'tra12345678',
    'GEMINI_API_KEYS': ['AIzaSyDAOp1ARgrkUvPcmGmXddFx8cqkzhy-3O8'],
    'MT5_LOGIN': None,
    'MT5_PASSWORD': None,
    'MT5_SERVER': None,
    'MONITORING_INTERVAL': 30,
    'MIN_CONFIDENCE_THRESHOLD': 70,
    'MAX_DAILY_ALERTS': 50,
    'GEMINI_MODEL': 'gemini-2.0-flash',
    'GEMINI_GENERATION_CONFIG': {
        'temperature': 0.7,
        'top_p': 0.8,
        'top_k': 40,
        'max_output_tokens': 1024,
    },
    'GEMINI_SAFETY_SETTINGS': [],
    'DEFAULT_CAPITAL_OPTIONS': [100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
}

# Simple embedded icon (bot icon as base64)
EMBEDDED_ICON = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlz
AAALEwAACxMBAJqcGAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAOzSURB
VFiFtZc9aBRBFMd/s7ubTWI0RhsLwcJCG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sL
G1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sL
G1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sL
G1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sL
G1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sL
G1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sLG1sL
"""

# ===============================================
# EMBEDDED BOT CLASS
# ===============================================

import telebot
from telebot import apihelper
import pandas as pd
import numpy as np

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from telebot import types
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Data directories
DATA_DIR = "trading_data"
USERS_DIR = os.path.join(DATA_DIR, "users")
BANNED_USERS_FILE = os.path.join(DATA_DIR, "banned_users.json")

# Create directories if they don't exist
for directory in [DATA_DIR, USERS_DIR]:
    os.makedirs(directory, exist_ok=True)

class EmbeddedTradingBot:
    """Enhanced Embedded Trading Bot with Full Functionality"""
    
    def __init__(self, config_data=None):
        self.config = config_data or EMBEDDED_CONFIG
        self.bot = None
        self.is_running = False
        self.user_sessions = {}
        self.authenticated_users = set()
        self.banned_users = self.load_banned_users()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler('bot.log', maxBytes=10*1024*1024, backupCount=5),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_banned_users(self):
        """Load banned users list"""
        try:
            if os.path.exists(BANNED_USERS_FILE):
                with open(BANNED_USERS_FILE, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            print(f"Error loading banned users: {e}")
            return set()
    
    def save_banned_users(self):
        """Save banned users list"""
        try:
            with open(BANNED_USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self.banned_users), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving banned users: {e}")
    
    def ban_user(self, user_id):
        """Ban a user"""
        try:
            user_id_str = str(user_id)
            self.banned_users.add(user_id_str)
            self.save_banned_users()
            
            # Remove from authenticated users if present
            if user_id in self.authenticated_users:
                self.authenticated_users.remove(user_id)
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
                
            self.logger.info(f"User {user_id} has been banned")
            return True
        except Exception as e:
            self.logger.error(f"Error banning user {user_id}: {e}")
            return False
    
    def unban_user(self, user_id):
        """Unban a user"""
        try:
            user_id_str = str(user_id)
            if user_id_str in self.banned_users:
                self.banned_users.remove(user_id_str)
                self.save_banned_users()
                self.logger.info(f"User {user_id} has been unbanned")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error unbanning user {user_id}: {e}")
            return False
    
    def is_user_banned(self, user_id):
        """Check if user is banned"""
        return str(user_id) in self.banned_users
        
    def get_users_count(self):
        """Get total number of users from JSON files"""
        try:
            user_files = glob.glob(os.path.join(USERS_DIR, "user_*.json"))
            return len(user_files)
        except Exception as e:
            self.logger.error(f"Error getting users count: {e}")
            return 0
    
    def get_users_details(self):
        """Get detailed information about all users"""
        try:
            users_details = []
            user_files = glob.glob(os.path.join(USERS_DIR, "user_*.json"))
            
            for user_file in user_files:
                try:
                    with open(user_file, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                        
                    user_id = os.path.basename(user_file).replace('user_', '').replace('.json', '')
                    
                    users_details.append({
                        'user_id': user_id,
                        'username': user_data.get('username', 'غير محدد'),
                        'first_name': user_data.get('first_name', 'غير محدد'),
                        'last_name': user_data.get('last_name', ''),
                        'registration_date': user_data.get('registration_date', user_data.get('join_date', 'غير محدد')),
                        'last_activity': user_data.get('last_activity', user_data.get('last_active', 'غير محدد')),
                        'trading_mode': user_data.get('trading_mode', 'غير محدد'),
                        'is_banned': self.is_user_banned(user_id)
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error reading user file {user_file}: {e}")
                    continue
            
            users_details.sort(key=lambda x: int(x['user_id']) if x['user_id'].isdigit() else 0)
            return users_details
            
        except Exception as e:
            self.logger.error(f"Error getting users details: {e}")
            return []
    
    def load_user_data(self, user_id):
        """Load user data from JSON file"""
        try:
            user_file = os.path.join(USERS_DIR, f"user_{user_id}.json")
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            self.logger.error(f"Error loading user data for {user_id}: {e}")
            return None
    
    def save_user_data(self, user_id, username=None, first_name=None):
        """Save user data to JSON file"""
        try:
            user_data = {
                'user_id': str(user_id),
                'username': username,
                'first_name': first_name,
                'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_activity': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            existing_data = self.load_user_data(user_id)
            if existing_data:
                user_data['registration_date'] = existing_data.get('registration_date', existing_data.get('join_date', user_data['registration_date']))
                user_data['username'] = username or existing_data.get('username')
                user_data['first_name'] = first_name or existing_data.get('first_name')
            
            user_file = os.path.join(USERS_DIR, f"user_{user_id}.json")
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"User data saved for {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving user data for {user_id}: {e}")
    
    def authenticate_user(self, user_id):
        """Mark user as authenticated"""
        try:
            if self.is_user_banned(user_id):
                return False
                
            self.authenticated_users.add(user_id)
            self.user_sessions[user_id] = {
                'authenticated': True,
                'login_time': datetime.now()
            }
            self.logger.info(f"User {user_id} authenticated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error authenticating user {user_id}: {e}")
            return False
    
    def is_authenticated(self, user_id):
        """Check if user is authenticated"""
        return self.user_sessions.get(user_id, {}).get('authenticated', False)
    
    def start_bot(self):
        """Start the trading bot"""
        if self.is_running:
            return False, "البوت يعمل بالفعل"
            
        try:
            apihelper.CONNECT_TIMEOUT = 60
            apihelper.READ_TIMEOUT = 60
            apihelper.RETRY_TIMEOUT = 5
            
            self.bot = telebot.TeleBot(self.config['BOT_TOKEN'])
            self.setup_handlers()
            
            self.bot_thread = threading.Thread(target=self._run_bot, daemon=True)
            self.is_running = True
            self.bot_thread.start()
            
            self.logger.info("Trading bot started successfully")
            return True, "تم تشغيل البوت بنجاح"
            
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            return False, f"خطأ في تشغيل البوت: {e}"
    
    def stop_bot(self):
        """Stop the trading bot"""
        if not self.is_running:
            return False, "البوت متوقف بالفعل"
            
        try:
            self.is_running = False
            if self.bot:
                self.bot.stop_polling()
            
            self.logger.info("Trading bot stopped")
            return True, "تم إيقاف البوت بنجاح"
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
            return False, f"خطأ في إيقاف البوت: {e}"
    
    def _run_bot(self):
        """Run bot polling"""
        try:
            self.bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            self.logger.error(f"Bot polling error: {e}")
            self.is_running = False
    
    def setup_handlers(self):
        """Setup bot message handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            user_id = message.from_user.id
            username = message.from_user.username
            first_name = message.from_user.first_name
            
            # Check if user is banned
            if self.is_user_banned(user_id):
                self.bot.reply_to(message, "❌ تم حظرك من استخدام البوت")
                return
            
            self.save_user_data(user_id, username, first_name)
            
            welcome_text = """
🤖 أهلاً بك في بوت التداول المتقدم v1.2.0

للوصول إلى الميزات المتقدمة، يرجى إدخال كلمة المرور:
            """
            
            self.bot.reply_to(message, welcome_text)
        
        @self.bot.message_handler(func=lambda message: not self.is_authenticated(message.from_user.id))
        def handle_password(message):
            user_id = message.from_user.id
            
            # Check if user is banned
            if self.is_user_banned(user_id):
                self.bot.reply_to(message, "❌ تم حظرك من استخدام البوت")
                return
            
            if message.text == self.config['BOT_PASSWORD']:
                if self.authenticate_user(user_id):
                    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
                    keyboard.add(
                        types.KeyboardButton("📊 تحليل الأسواق"),
                        types.KeyboardButton("💰 الأسعار المباشرة"),
                        types.KeyboardButton("📈 توصيات التداول"),
                        types.KeyboardButton("⚙️ الإعدادات")
                    )
                    
                    self.bot.reply_to(
                        message, 
                        "✅ تم تسجيل الدخول بنجاح!\n\nاختر من القائمة أدناه:",
                        reply_markup=keyboard
                    )
                else:
                    self.bot.reply_to(message, "❌ تم حظرك من استخدام البوت")
            else:
                self.bot.reply_to(message, "❌ كلمة مرور خاطئة. حاول مرة أخرى.")
        
        @self.bot.message_handler(func=lambda message: self.is_authenticated(message.from_user.id))
        def handle_authenticated_messages(message):
            user_id = message.from_user.id
            text = message.text
            
            # Check if user got banned during session
            if self.is_user_banned(user_id):
                self.bot.reply_to(message, "❌ تم حظرك من استخدام البوت")
                return
            
            self.save_user_data(user_id, message.from_user.username, message.from_user.first_name)
            
            if text == "📊 تحليل الأسواق":
                self.bot.reply_to(message, "🔄 جاري تحليل الأسواق... يرجى الانتظار")
                
            elif text == "💰 الأسعار المباشرة":
                self.bot.reply_to(message, "📈 جاري جلب الأسعار المباشرة...")
                
            elif text == "📈 توصيات التداول":
                self.bot.reply_to(message, "🤖 جاري تحليل التوصيات...")
                
            elif text == "⚙️ الإعدادات":
                settings_keyboard = types.InlineKeyboardMarkup()
                settings_keyboard.add(
                    types.InlineKeyboardButton("🔔 الإشعارات", callback_data="settings_notifications"),
                    types.InlineKeyboardButton("📊 التفضيلات", callback_data="settings_preferences")
                )
                
                self.bot.reply_to(
                    message,
                    "⚙️ إعدادات البوت:",
                    reply_markup=settings_keyboard
                )
            
            else:
                self.bot.reply_to(message, "استخدم القائمة للتنقل في البوت")

# ===============================================
# MAIN GUI CLASS
# ===============================================

class TradingBotUI:
    def __init__(self):
        self.embedded_bot = EmbeddedTradingBot(EMBEDDED_CONFIG)
        self.PASSWORD = "041768454"
        self.is_logged_in = False
        self.monitoring_thread = None
        self.is_monitoring = False
        self.users_count_window = None
        self.settings_window = None
        
        # Initialize main window
        self.setup_main_window()
        self.create_login_interface()
        self.create_control_interface()
        
        # Start with login screen
        self.show_login()
        
        # Start monitoring thread
        self.start_monitoring()
    
    def setup_main_window(self):
        """Setup main application window"""
        self.root = tk.Tk()
        self.root.title("🤖 بوت التداول المتقدم v1.2.0 - واجهة التحكم")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        # Set embedded icon
        try:
            icon_data = base64.b64decode(EMBEDDED_ICON)
            icon_image = tk.PhotoImage(data=icon_data)
            self.root.iconphoto(False, icon_image)
        except:
            pass
        
        # Configure main style
        self.root.configure(bg='#2b2b2b')
        
        # Create main frame
        self.main_frame = tk.Frame(self.root, bg='#2b2b2b')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_login_interface(self):
        """Create login interface"""
        self.login_frame = tk.Frame(self.main_frame, bg='#2b2b2b')
        
        # Title
        title_label = tk.Label(
            self.login_frame,
            text="🤖 بوت التداول المتقدم",
            font=("Arial", 24, "bold"),
            fg='#00ff00',
            bg='#2b2b2b'
        )
        title_label.pack(pady=30)
        
        # Subtitle
        subtitle_label = tk.Label(
            self.login_frame,
            text="واجهة التحكم المتقدمة v1.2.0 - نظام مدمج كامل",
            font=("Arial", 12),
            fg='#cccccc',
            bg='#2b2b2b'
        )
        subtitle_label.pack(pady=10)
        
        # Password frame
        password_frame = tk.Frame(self.login_frame, bg='#2b2b2b')
        password_frame.pack(pady=40)
        
        # Password label
        password_label = tk.Label(
            password_frame,
            text="🔐 أدخل كلمة المرور:",
            font=("Arial", 14),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        password_label.pack(pady=10)
        
        # Password entry
        self.password_entry = tk.Entry(
            password_frame,
            font=("Arial", 14),
            show="*",
            width=20,
            justify='center'
        )
        self.password_entry.pack(pady=10)
        self.password_entry.bind('<Return>', lambda event: self.check_password())
        
        # Login button
        self.login_button = tk.Button(
            password_frame,
            text="🚀 دخول",
            font=("Arial", 12, "bold"),
            bg='#00aa00',
            fg='white',
            width=15,
            height=2,
            command=self.check_password
        )
        self.login_button.pack(pady=20)
        
        # Status label
        self.login_status_label = tk.Label(
            self.login_frame,
            text="",
            font=("Arial", 10),
            fg='#ff6666',
            bg='#2b2b2b'
        )
        self.login_status_label.pack(pady=10)
    
    def create_control_interface(self):
        """Create main control interface"""
        self.control_frame = tk.Frame(self.main_frame, bg='#2b2b2b')
        
        # Header frame
        header_frame = tk.Frame(self.control_frame, bg='#2b2b2b')
        header_frame.pack(fill=tk.X, pady=10)
        
        # Settings button (top left)
        settings_button = tk.Button(
            header_frame,
            text="⚙️",
            font=("Arial", 16, "bold"),
            bg='#4a4a4a',
            fg='#ffffff',
            width=3,
            height=1,
            command=self.show_settings_window
        )
        settings_button.pack(side=tk.LEFT, padx=5)
        
        # Title
        header_label = tk.Label(
            header_frame,
            text="🤖 لوحة التحكم في بوت التداول - نظام مدمج كامل",
            font=("Arial", 18, "bold"),
            fg='#00ff00',
            bg='#2b2b2b'
        )
        header_label.pack(side=tk.LEFT, padx=20)
        
        # About button (top right)
        about_button = tk.Button(
            header_frame,
            text="ℹ️",
            font=("Arial", 14, "bold"),
            bg='#2196F3',
            fg='white',
            width=3,
            height=1,
            command=self.show_about_dialog
        )
        about_button.pack(side=tk.RIGHT, padx=5)
        
        # Users count button (with click functionality)
        self.users_count_button = tk.Button(
            header_frame,
            text="👥 عدد المستخدمين: 0",
            font=("Arial", 10, "bold"),
            bg='#800020',
            fg='#ff0000',
            command=self.show_users_management_window
        )
        self.users_count_button.pack(side=tk.RIGHT, padx=5)
        
        # Logout button
        logout_button = tk.Button(
            header_frame,
            text="🚪 خروج",
            font=("Arial", 10),
            bg='#666666',
            fg='white',
            command=self.logout
        )
        logout_button.pack(side=tk.RIGHT, padx=5)
        
        # Control buttons frame
        control_buttons_frame = tk.Frame(self.control_frame, bg='#2b2b2b')
        control_buttons_frame.pack(pady=20)
        
        # Start Bot button
        self.start_button = tk.Button(
            control_buttons_frame,
            text="🚀 تشغيل البوت",
            font=("Arial", 14, "bold"),
            bg='#00aa00',
            fg='white',
            width=15,
            height=2,
            command=self.start_bot
        )
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        # Stop Bot button
        self.stop_button = tk.Button(
            control_buttons_frame,
            text="🛑 إيقاف البوت",
            font=("Arial", 14, "bold"),
            bg='#aa0000',
            fg='white',
            width=15,
            height=2,
            command=self.stop_bot,
            state='disabled'
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # Status frame
        status_frame = tk.Frame(self.control_frame, bg='#2b2b2b')
        status_frame.pack(fill=tk.X, pady=20)
        
        # Status label
        status_label = tk.Label(
            status_frame,
            text="📊 حالة البوت:",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        status_label.pack(anchor=tk.W)
        
        # Status indicator
        self.status_indicator = tk.Label(
            status_frame,
            text="⚫ متوقف",
            font=("Arial", 12),
            fg='#ff6666',
            bg='#2b2b2b'
        )
        self.status_indicator.pack(anchor=tk.W, padx=20)
        
        # Log frame
        log_frame = tk.Frame(self.control_frame, bg='#2b2b2b')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Log label
        log_label = tk.Label(
            log_frame,
            text="📝 سجل الأحداث:",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        log_label.pack(anchor=tk.W)
        
        # Log text area with save button
        log_controls_frame = tk.Frame(log_frame, bg='#2b2b2b')
        log_controls_frame.pack(fill=tk.X, pady=5)
        
        save_logs_button = tk.Button(
            log_controls_frame,
            text="💾 حفظ السجل كملف TXT",
            font=("Arial", 10, "bold"),
            bg='#FF9800',
            fg='white',
            command=self.save_logs_to_file
        )
        save_logs_button.pack(side=tk.RIGHT, padx=5)
        
        clear_logs_button = tk.Button(
            log_controls_frame,
            text="🧹 مسح السجل",
            font=("Arial", 10, "bold"),
            bg='#f44336',
            fg='white',
            command=self.clear_logs
        )
        clear_logs_button.pack(side=tk.RIGHT, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=80,
            bg='#1a1a1a',
            fg='#00ff00',
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Bottom frame for uptime counter
        bottom_frame = tk.Frame(self.control_frame, bg='#2b2b2b')
        bottom_frame.pack(fill=tk.X, pady=5)
        
        # Uptime counters (bottom left)
        self.uptime_label = tk.Label(
            bottom_frame,
            text="⏱️ وقت تشغيل الواجهة: 00:00:00",
            font=("Arial", 10),
            fg='#cccccc',
            bg='#2b2b2b'
        )
        self.uptime_label.pack(side=tk.LEFT, padx=5)
        
        self.bot_uptime_label = tk.Label(
            bottom_frame,
            text="🤖 وقت تشغيل البوت: متوقف",
            font=("Arial", 10),
            fg='#cccccc',
            bg='#2b2b2b'
        )
        self.bot_uptime_label.pack(side=tk.LEFT, padx=15)
        
        # Initialize uptime tracking
        self.start_time = datetime.now()
        self.bot_start_time = None  # Will be set when bot starts
        self.update_uptime()
        self.update_bot_uptime()
        
        # Add initial log messages
        self.add_log("🔧 تم تهيئة واجهة التحكم في البوت - إصدار مدمج كامل")
        self.add_log("ℹ️  يستخدم نظام ملفات JSON الأصلي")
        self.add_log("📁 المستخدمون محفوظون في: trading_data/users/")
        self.add_log("🔐 يرجى تسجيل الدخول للوصول إلى عناصر التحكم")
    
    def show_users_management_window(self):
        """Show users management window with password protection"""
        # Ask for password
        password = simpledialog.askstring(
            "كلمة المرور",
            "أدخل كلمة المرور لعرض إدارة المستخدمين:",
            show='*'
        )
        
        if password != self.PASSWORD:
            messagebox.showerror("خطأ", "كلمة مرور خاطئة!")
            return
        
        # Create users management window
        users_window = tk.Toplevel(self.root)
        users_window.title("👥 إدارة المستخدمين")
        users_window.geometry("1000x600")
        users_window.configure(bg='#2b2b2b')
        users_window.transient(self.root)
        users_window.grab_set()
        
        # Main frame
        main_frame = tk.Frame(users_window, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="👥 إدارة المستخدمين",
            font=("Arial", 16, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        title_label.pack(pady=10)
        
        # Create Treeview for users
        columns = ('ID', 'Username', 'Full Name', 'Status', 'Registration', 'Actions')
        tree_frame = tk.Frame(main_frame, bg='#2b2b2b')
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        users_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        
        tree_scroll_y.config(command=users_tree.yview)
        tree_scroll_x.config(command=users_tree.xview)
        
        # Configure columns
        users_tree.heading('ID', text='معرف المستخدم')
        users_tree.heading('Username', text='اسم المستخدم')
        users_tree.heading('Full Name', text='الاسم الكامل')
        users_tree.heading('Status', text='الحالة')
        users_tree.heading('Registration', text='تاريخ التسجيل')
        users_tree.heading('Actions', text='الإجراءات')
        
        users_tree.column('ID', width=100)
        users_tree.column('Username', width=150)
        users_tree.column('Full Name', width=200)
        users_tree.column('Status', width=100)
        users_tree.column('Registration', width=150)
        users_tree.column('Actions', width=200)
        
        users_tree.pack(fill=tk.BOTH, expand=True)
        
        # Populate users data
        self.refresh_users_management(users_tree)
        
        # Action buttons frame
        action_frame = tk.Frame(main_frame, bg='#2b2b2b')
        action_frame.pack(fill=tk.X, pady=10)
        
        # Ban button
        ban_button = tk.Button(
            action_frame,
            text="🚫 حظر المستخدم المحدد",
            font=("Arial", 10, "bold"),
            bg='#ff4444',
            fg='white',
            command=lambda: self.ban_selected_user(users_tree)
        )
        ban_button.pack(side=tk.LEFT, padx=5)
        
        # Unban button
        unban_button = tk.Button(
            action_frame,
            text="✅ إلغاء حظر المستخدم المحدد",
            font=("Arial", 10, "bold"),
            bg='#44ff44',
            fg='white',
            command=lambda: self.unban_selected_user(users_tree)
        )
        unban_button.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        refresh_button = tk.Button(
            action_frame,
            text="🔄 تحديث",
            font=("Arial", 10, "bold"),
            bg='#4CAF50',
            fg='white',
            command=lambda: self.refresh_users_management(users_tree)
        )
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_button = tk.Button(
            action_frame,
            text="❌ إغلاق",
            font=("Arial", 10, "bold"),
            bg='#666666',
            fg='white',
            command=users_window.destroy
        )
        close_button.pack(side=tk.RIGHT, padx=5)
    
    def refresh_users_management(self, tree):
        """Refresh users management tree"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
            
            # Get users details
            users_details = self.embedded_bot.get_users_details()
            
            # Populate tree
            for user in users_details:
                status = "محظور" if user['is_banned'] else "نشط"
                
                item = tree.insert('', tk.END, values=(
                    user['user_id'],
                    f"@{user['username']}" if user['username'] != 'غير محدد' else "لا يوجد",
                    user['first_name'],
                    status,
                    user['registration_date'][:10] if len(user['registration_date']) > 10 else user['registration_date'],
                    "حظر/إلغاء حظر"
                ))
                
                # Color banned users differently
                if user['is_banned']:
                    tree.set(item, 'Status', '🚫 محظور')
                else:
                    tree.set(item, 'Status', '✅ نشط')
                    
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحديث البيانات: {str(e)}")
    
    def ban_selected_user(self, tree):
        """Ban selected user"""
        try:
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("تحذير", "يرجى تحديد مستخدم أولاً")
                return
            
            item = selection[0]
            user_id = tree.item(item)['values'][0]
            username = tree.item(item)['values'][1]
            
            # Confirm action
            result = messagebox.askyesno(
                "تأكيد الحظر",
                f"هل أنت متأكد من حظر المستخدم:\n{username} (ID: {user_id})؟"
            )
            
            if result:
                if self.embedded_bot.ban_user(user_id):
                    messagebox.showinfo("نجح", f"تم حظر المستخدم {username} بنجاح")
                    self.refresh_users_management(tree)
                    self.add_log(f"🚫 تم حظر المستخدم {username} (ID: {user_id})")
                else:
                    messagebox.showerror("خطأ", "فشل في حظر المستخدم")
                    
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حظر المستخدم: {str(e)}")
    
    def unban_selected_user(self, tree):
        """Unban selected user"""
        try:
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("تحذير", "يرجى تحديد مستخدم أولاً")
                return
            
            item = selection[0]
            user_id = tree.item(item)['values'][0]
            username = tree.item(item)['values'][1]
            
            # Check if user is actually banned
            if not self.embedded_bot.is_user_banned(user_id):
                messagebox.showinfo("معلومات", "هذا المستخدم غير محظور")
                return
            
            # Confirm action
            result = messagebox.askyesno(
                "تأكيد إلغاء الحظر",
                f"هل أنت متأكد من إلغاء حظر المستخدم:\n{username} (ID: {user_id})؟"
            )
            
            if result:
                if self.embedded_bot.unban_user(user_id):
                    messagebox.showinfo("نجح", f"تم إلغاء حظر المستخدم {username} بنجاح")
                    self.refresh_users_management(tree)
                    self.add_log(f"✅ تم إلغاء حظر المستخدم {username} (ID: {user_id})")
                else:
                    messagebox.showerror("خطأ", "فشل في إلغاء حظر المستخدم")
                    
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في إلغاء حظر المستخدم: {str(e)}")
    
    def show_settings_window(self):
        """Show settings window with password protection"""
        # Ask for password
        password = simpledialog.askstring(
            "كلمة المرور",
            "أدخل كلمة المرور للوصول إلى الإعدادات:",
            show='*'
        )
        
        if password != self.PASSWORD:
            messagebox.showerror("خطأ", "كلمة مرور خاطئة!")
            return
        
        # Create settings window
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
            
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("⚙️ إعدادات البوت")
        self.settings_window.geometry("800x600")
        self.settings_window.configure(bg='#2b2b2b')
        self.settings_window.transient(self.root)
        self.settings_window.grab_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configurations tab
        self.create_configurations_tab(notebook)
        
        # Users tab
        self.create_users_tab(notebook)
        
        # Security tab (with additional password protection)
        self.create_security_tab(notebook)
    
    def create_configurations_tab(self, notebook):
        """Create configurations tab"""
        config_frame = tk.Frame(notebook, bg='#2b2b2b')
        notebook.add(config_frame, text="⚙️ Configurations")
        
        # Main scrollable frame
        canvas = tk.Canvas(config_frame, bg='#2b2b2b')
        scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Telegram API Section
        telegram_frame = tk.LabelFrame(
            scrollable_frame,
            text="📱 إدارة رمز Telegram Bot API",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        telegram_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Current token display
        token_label = tk.Label(
            telegram_frame,
            text="رمز البوت الحالي:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        token_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.telegram_token_entry = tk.Entry(
            telegram_frame,
            font=("Arial", 10),
            width=50,
            bg='#1a1a1a',
            fg='#ffffff'
        )
        self.telegram_token_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Bot password
        bot_password_label = tk.Label(
            telegram_frame,
            text="كلمة مرور البوت:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        bot_password_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.bot_password_entry = tk.Entry(
            telegram_frame,
            font=("Arial", 10),
            width=50,
            bg='#1a1a1a',
            fg='#ffffff'
        )
        self.bot_password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Load current telegram settings
        self.load_telegram_settings()
        
        # Telegram save button
        telegram_save_frame = tk.Frame(telegram_frame, bg='#2b2b2b')
        telegram_save_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        save_telegram_button = tk.Button(
            telegram_save_frame,
            text="💾 حفظ إعدادات Telegram",
            font=("Arial", 10, "bold"),
            bg='#4CAF50',
            fg='white',
            command=self.save_telegram_settings
        )
        save_telegram_button.pack(side=tk.LEFT, padx=5)
        
        test_telegram_button = tk.Button(
            telegram_save_frame,
            text="🔗 اختبار الرمز",
            font=("Arial", 10, "bold"),
            bg='#2196F3',
            fg='white',
            command=self.test_telegram_token
        )
        test_telegram_button.pack(side=tk.LEFT, padx=5)
        
        # Gemini API Section
        gemini_frame = tk.LabelFrame(
            scrollable_frame,
            text="🤖 إدارة مفاتيح Gemini API",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        gemini_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # API Keys listbox
        keys_label = tk.Label(
            gemini_frame,
            text="مفاتيح API الحالية:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        keys_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Frame for listbox and scrollbar
        listbox_frame = tk.Frame(gemini_frame, bg='#2b2b2b')
        listbox_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Listbox with scrollbar
        listbox_scroll = ttk.Scrollbar(listbox_frame)
        listbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.api_keys_listbox = tk.Listbox(
            listbox_frame,
            height=5,
            yscrollcommand=listbox_scroll.set,
            bg='#1a1a1a',
            fg='#ffffff',
            font=("Consolas", 9)
        )
        self.api_keys_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        listbox_scroll.config(command=self.api_keys_listbox.yview)
        
        # Populate API keys
        self.refresh_api_keys()
        
        # API Keys buttons
        keys_buttons_frame = tk.Frame(gemini_frame, bg='#2b2b2b')
        keys_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        add_key_button = tk.Button(
            keys_buttons_frame,
            text="➕ إضافة مفتاح",
            font=("Arial", 9),
            bg='#4CAF50',
            fg='white',
            command=self.add_api_key
        )
        add_key_button.pack(side=tk.LEFT, padx=2)
        
        edit_key_button = tk.Button(
            keys_buttons_frame,
            text="✏️ تحرير",
            font=("Arial", 9),
            bg='#2196F3',
            fg='white',
            command=self.edit_api_key
        )
        edit_key_button.pack(side=tk.LEFT, padx=2)
        
        delete_key_button = tk.Button(
            keys_buttons_frame,
            text="🗑️ حذف",
            font=("Arial", 9),
            bg='#f44336',
            fg='white',
            command=self.delete_api_key
        )
        delete_key_button.pack(side=tk.LEFT, padx=2)
        
        check_keys_button = tk.Button(
            keys_buttons_frame,
            text="🔍 فحص المفاتيح",
            font=("Arial", 9),
            bg='#FF9800',
            fg='white',
            command=self.check_api_keys_status
        )
        check_keys_button.pack(side=tk.LEFT, padx=2)
        
        # Gemini save button
        gemini_save_frame = tk.Frame(gemini_frame, bg='#2b2b2b')
        gemini_save_frame.pack(fill=tk.X, padx=5, pady=5)
        
        save_gemini_button = tk.Button(
            gemini_save_frame,
            text="💾 حفظ إعدادات Gemini",
            font=("Arial", 10, "bold"),
            bg='#4CAF50',
            fg='white',
            command=self.save_gemini_settings
        )
        save_gemini_button.pack(side=tk.LEFT, padx=5)
        
        # MT5 Login Section
        mt5_frame = tk.LabelFrame(
            scrollable_frame,
            text="🏦 إعدادات تسجيل الدخول MT5",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        mt5_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # MT5 Account field
        account_label = tk.Label(
            mt5_frame,
            text="رقم الحساب:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        account_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.mt5_account_entry = tk.Entry(
            mt5_frame,
            font=("Arial", 10),
            width=30,
            bg='#1a1a1a',
            fg='#ffffff'
        )
        self.mt5_account_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # MT5 Password field
        password_label = tk.Label(
            mt5_frame,
            text="كلمة المرور:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        password_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.mt5_password_entry = tk.Entry(
            mt5_frame,
            font=("Arial", 10),
            width=30,
            show="*",
            bg='#1a1a1a',
            fg='#ffffff'
        )
        self.mt5_password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # MT5 Server field
        server_label = tk.Label(
            mt5_frame,
            text="نوع الحساب:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        server_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.mt5_server_entry = tk.Entry(
            mt5_frame,
            font=("Arial", 10),
            width=30,
            bg='#1a1a1a',
            fg='#ffffff'
        )
        self.mt5_server_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Load current MT5 settings
        self.load_mt5_settings()
        
        # MT5 buttons
        mt5_buttons_frame = tk.Frame(mt5_frame, bg='#2b2b2b')
        mt5_buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        save_mt5_button = tk.Button(
            mt5_buttons_frame,
            text="💾 حفظ إعدادات MT5",
            font=("Arial", 9),
            bg='#4CAF50',
            fg='white',
            command=self.save_mt5_settings
        )
        save_mt5_button.pack(side=tk.LEFT, padx=5)
        
        test_mt5_button = tk.Button(
            mt5_buttons_frame,
            text="🔗 اختبار الاتصال",
            font=("Arial", 9),
            bg='#2196F3',
            fg='white',
            command=self.test_mt5_connection
        )
        test_mt5_button.pack(side=tk.LEFT, padx=5)
    
    def create_users_tab(self, notebook):
        """Create users management tab"""
        users_frame = tk.Frame(notebook, bg='#2b2b2b')
        notebook.add(users_frame, text="👥 Users")
        
        # Title
        title_label = tk.Label(
            users_frame,
            text="👥 إدارة المستخدمين",
            font=("Arial", 16, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        title_label.pack(pady=10)
        
        # Create Treeview for users
        columns = ('ID', 'Username', 'Full Name', 'Status', 'Registration')
        tree_frame = tk.Frame(users_frame, bg='#2b2b2b')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        users_tree_tab = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            yscrollcommand=tree_scroll_y.set
        )
        
        tree_scroll_y.config(command=users_tree_tab.yview)
        
        # Configure columns
        users_tree_tab.heading('ID', text='معرف المستخدم')
        users_tree_tab.heading('Username', text='اسم المستخدم')
        users_tree_tab.heading('Full Name', text='الاسم الكامل')
        users_tree_tab.heading('Status', text='الحالة')
        users_tree_tab.heading('Registration', text='تاريخ التسجيل')
        
        users_tree_tab.column('ID', width=100)
        users_tree_tab.column('Username', width=150)
        users_tree_tab.column('Full Name', width=200)
        users_tree_tab.column('Status', width=100)
        users_tree_tab.column('Registration', width=150)
        
        users_tree_tab.pack(fill=tk.BOTH, expand=True)
        
        # Populate users data
        self.refresh_users_tab(users_tree_tab)
        
        # Action buttons
        tab_action_frame = tk.Frame(users_frame, bg='#2b2b2b')
        tab_action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ban_tab_button = tk.Button(
            tab_action_frame,
            text="🚫 حظر",
            font=("Arial", 10, "bold"),
            bg='#ff4444',
            fg='white',
            command=lambda: self.ban_selected_user(users_tree_tab)
        )
        ban_tab_button.pack(side=tk.LEFT, padx=5)
        
        unban_tab_button = tk.Button(
            tab_action_frame,
            text="✅ إلغاء حظر",
            font=("Arial", 10, "bold"),
            bg='#44ff44',
            fg='white',
            command=lambda: self.unban_selected_user(users_tree_tab)
        )
        unban_tab_button.pack(side=tk.LEFT, padx=5)
        
        refresh_tab_button = tk.Button(
            tab_action_frame,
            text="🔄 تحديث",
            font=("Arial", 10, "bold"),
            bg='#4CAF50',
            fg='white',
            command=lambda: self.refresh_users_tab(users_tree_tab)
        )
        refresh_tab_button.pack(side=tk.LEFT, padx=5)
    
    def refresh_users_tab(self, tree):
        """Refresh users tab tree"""
        self.refresh_users_management(tree)
    
    def create_security_tab(self, notebook):
        """Create security and protection tab with additional password protection"""
        # Create a frame that will show password prompt first
        security_outer_frame = tk.Frame(notebook, bg='#2b2b2b')
        notebook.add(security_outer_frame, text="🔐 Security")
        
        # Initially show password prompt
        self.security_password_frame = tk.Frame(security_outer_frame, bg='#2b2b2b')
        self.security_password_frame.pack(fill=tk.BOTH, expand=True)
        
        # Password prompt for security tab
        security_title = tk.Label(
            self.security_password_frame,
            text="🔐 تبويب الحماية والأمان",
            font=("Arial", 18, "bold"),
            fg='#ff6666',
            bg='#2b2b2b'
        )
        security_title.pack(pady=50)
        
        security_warning = tk.Label(
            self.security_password_frame,
            text="⚠️ هذا التبويب يحتوي على إعدادات حساسة\nيرجى إدخال كلمة المرور للمتابعة",
            font=("Arial", 12),
            fg='#ffaa00',
            bg='#2b2b2b',
            justify=tk.CENTER
        )
        security_warning.pack(pady=20)
        
        # Password entry for security tab
        security_password_entry = tk.Entry(
            self.security_password_frame,
            font=("Arial", 14),
            show="*",
            width=20,
            justify='center',
            bg='#1a1a1a',
            fg='#ffffff'
        )
        security_password_entry.pack(pady=20)
        
        # Access button
        def access_security_tab():
            entered_password = security_password_entry.get()
            if entered_password == self.PASSWORD:
                # Hide password prompt and show security content
                self.security_password_frame.pack_forget()
                self.create_security_content(security_outer_frame)
                self.add_log("🔐 تم الوصول إلى تبويب الحماية والأمان")
            else:
                messagebox.showerror("خطأ", "كلمة مرور خاطئة!")
                security_password_entry.delete(0, tk.END)
        
        access_button = tk.Button(
            self.security_password_frame,
            text="🔓 دخول",
            font=("Arial", 12, "bold"),
            bg='#ff6666',
            fg='white',
            width=15,
            height=2,
            command=access_security_tab
        )
        access_button.pack(pady=20)
        
        # Bind Enter key to access button
        security_password_entry.bind('<Return>', lambda event: access_security_tab())
        
        # Focus on password entry when tab is selected
        def on_tab_selected(event):
            if notebook.index(notebook.select()) == 2:  # Security tab index
                security_password_entry.focus()
        
        notebook.bind("<<NotebookTabChanged>>", on_tab_selected)
    
    def create_security_content(self, parent_frame):
        """Create the actual security tab content"""
        # Main security frame
        security_frame = tk.Frame(parent_frame, bg='#2b2b2b')
        security_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            security_frame,
            text="🔐 إعدادات الحماية والأمان",
            font=("Arial", 16, "bold"),
            fg='#ff6666',
            bg='#2b2b2b'
        )
        title_label.pack(pady=10)
        
        # Password change section
        password_frame = tk.LabelFrame(
            security_frame,
            text="🔑 تغيير كلمات المرور",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        password_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Current bot password display
        current_password_label = tk.Label(
            password_frame,
            text="كلمة مرور البوت الحالية:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        current_password_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.current_bot_password_display = tk.Label(
            password_frame,
            text=EMBEDDED_CONFIG.get('BOT_PASSWORD', 'tra12345678'),
            font=("Arial", 10, "bold"),
            fg='#ffaa00',
            bg='#2b2b2b'
        )
        self.current_bot_password_display.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # New bot password
        new_password_label = tk.Label(
            password_frame,
            text="كلمة مرور البوت الجديدة:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        new_password_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.new_bot_password_entry = tk.Entry(
            password_frame,
            font=("Arial", 10),
            width=30,
            bg='#1a1a1a',
            fg='#ffffff'
        )
        self.new_bot_password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Confirm new password
        confirm_password_label = tk.Label(
            password_frame,
            text="تأكيد كلمة المرور الجديدة:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        confirm_password_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.confirm_bot_password_entry = tk.Entry(
            password_frame,
            font=("Arial", 10),
            width=30,
            bg='#1a1a1a',
            fg='#ffffff'
        )
        self.confirm_bot_password_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Change password button
        change_password_frame = tk.Frame(password_frame, bg='#2b2b2b')
        change_password_frame.grid(row=3, column=0, columnspan=2, pady=15)
        
        change_password_button = tk.Button(
            change_password_frame,
            text="🔑 تغيير كلمة مرور البوت",
            font=("Arial", 11, "bold"),
            bg='#ff6666',
            fg='white',
            command=self.change_bot_password
        )
        change_password_button.pack(side=tk.LEFT, padx=5)
        
        reset_password_button = tk.Button(
            change_password_frame,
            text="🔄 إعادة تعيين للافتراضي",
            font=("Arial", 11, "bold"),
            bg='#666666',
            fg='white',
            command=self.reset_bot_password
        )
        reset_password_button.pack(side=tk.LEFT, padx=5)
        
        # UI Password change section
        ui_password_frame = tk.LabelFrame(
            security_frame,
            text="🖥️ تغيير كلمة مرور الواجهة",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        ui_password_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Current UI password (masked)
        current_ui_label = tk.Label(
            ui_password_frame,
            text="كلمة مرور الواجهة الحالية:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        current_ui_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        current_ui_display = tk.Label(
            ui_password_frame,
            text="*" * len(self.PASSWORD),
            font=("Arial", 10, "bold"),
            fg='#ffaa00',
            bg='#2b2b2b'
        )
        current_ui_display.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # New UI password
        new_ui_password_label = tk.Label(
            ui_password_frame,
            text="كلمة مرور الواجهة الجديدة:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        new_ui_password_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.new_ui_password_entry = tk.Entry(
            ui_password_frame,
            font=("Arial", 10),
            width=30,
            show="*",
            bg='#1a1a1a',
            fg='#ffffff'
        )
        self.new_ui_password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Confirm new UI password
        confirm_ui_password_label = tk.Label(
            ui_password_frame,
            text="تأكيد كلمة مرور الواجهة:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        confirm_ui_password_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.confirm_ui_password_entry = tk.Entry(
            ui_password_frame,
            font=("Arial", 10),
            width=30,
            show="*",
            bg='#1a1a1a',
            fg='#ffffff'
        )
        self.confirm_ui_password_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Change UI password button
        change_ui_password_button = tk.Button(
            ui_password_frame,
            text="🔐 تغيير كلمة مرور الواجهة",
            font=("Arial", 11, "bold"),
            bg='#ff6666',
            fg='white',
            command=self.change_ui_password
        )
        change_ui_password_button.grid(row=3, column=0, columnspan=2, pady=15)
        
        # Security info section
        info_frame = tk.LabelFrame(
            security_frame,
            text="ℹ️ معلومات الأمان",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        security_info = tk.Text(
            info_frame,
            height=8,
            width=70,
            bg='#1a1a1a',
            fg='#cccccc',
            font=("Arial", 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        security_info.pack(padx=10, pady=10)
        
        # Add security information
        security_text = """🔐 معلومات الحماية والأمان:

• كلمة مرور البوت: تُستخدم للمصادقة داخل Telegram
• كلمة مرور الواجهة: تُستخدم للوصول إلى واجهة التحكم
• تبويب الحماية: يتطلب كلمة مرور إضافية للوصول

⚠️ تحذيرات مهمة:
• احتفظ بنسخة احتياطية من كلمات المرور
• استخدم كلمات مرور قوية ومعقدة
• لا تشارك كلمات المرور مع أشخاص غير مخولين
• تغيير كلمة مرور البوت يتطلب إعادة تشغيل البوت

💡 نصائح الأمان:
• استخدم أرقام وحروف ورموز في كلمات المرور
• تجنب استخدام معلومات شخصية
• غير كلمات المرور بانتظام"""

        security_info.config(state=tk.NORMAL)
        security_info.insert("1.0", security_text)
        security_info.config(state=tk.DISABLED)
    
    def refresh_api_keys(self):
        """Refresh API keys listbox"""
        try:
            self.api_keys_listbox.delete(0, tk.END)
            
            for i, key in enumerate(EMBEDDED_CONFIG['GEMINI_API_KEYS']):
                # Show only first and last 8 characters for security
                masked_key = f"{key[:8]}...{key[-8:]}" if len(key) > 16 else key
                self.api_keys_listbox.insert(tk.END, f"{i+1}. {masked_key}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في تحديث المفاتيح: {str(e)}")
    
    def add_api_key(self):
        """Add new API key"""
        try:
            new_key = simpledialog.askstring(
                "إضافة مفتاح API",
                "أدخل مفتاح Gemini API الجديد:",
                show='*'
            )
            
            if new_key and new_key.strip():
                new_key = new_key.strip()
                if new_key not in EMBEDDED_CONFIG['GEMINI_API_KEYS']:
                    EMBEDDED_CONFIG['GEMINI_API_KEYS'].append(new_key)
                    self.refresh_api_keys()
                    self.save_config()
                    messagebox.showinfo("نجح", "تم إضافة المفتاح بنجاح")
                    self.add_log(f"➕ تم إضافة مفتاح API جديد")
                else:
                    messagebox.showwarning("تحذير", "هذا المفتاح موجود بالفعل")
                    
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في إضافة المفتاح: {str(e)}")
    
    def edit_api_key(self):
        """Edit selected API key"""
        try:
            selection = self.api_keys_listbox.curselection()
            if not selection:
                messagebox.showwarning("تحذير", "يرجى تحديد مفتاح أولاً")
                return
            
            index = selection[0]
            current_key = EMBEDDED_CONFIG['GEMINI_API_KEYS'][index]
            
            new_key = simpledialog.askstring(
                "تحرير مفتاح API",
                "أدخل المفتاح الجديد:",
                initialvalue=current_key,
                show='*'
            )
            
            if new_key and new_key.strip() and new_key != current_key:
                EMBEDDED_CONFIG['GEMINI_API_KEYS'][index] = new_key.strip()
                self.refresh_api_keys()
                self.save_config()
                messagebox.showinfo("نجح", "تم تحديث المفتاح بنجاح")
                self.add_log(f"✏️ تم تحرير مفتاح API")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في تحرير المفتاح: {str(e)}")
    
    def delete_api_key(self):
        """Delete selected API key"""
        try:
            selection = self.api_keys_listbox.curselection()
            if not selection:
                messagebox.showwarning("تحذير", "يرجى تحديد مفتاح أولاً")
                return
            
            if len(EMBEDDED_CONFIG['GEMINI_API_KEYS']) <= 1:
                messagebox.showwarning("تحذير", "لا يمكن حذف المفتاح الوحيد")
                return
            
            index = selection[0]
            
            result = messagebox.askyesno(
                "تأكيد الحذف",
                "هل أنت متأكد من حذف هذا المفتاح؟"
            )
            
            if result:
                del EMBEDDED_CONFIG['GEMINI_API_KEYS'][index]
                self.refresh_api_keys()
                self.save_config()
                messagebox.showinfo("نجح", "تم حذف المفتاح بنجاح")
                self.add_log(f"🗑️ تم حذف مفتاح API")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حذف المفتاح: {str(e)}")
    
    def check_api_keys_status(self):
        """Check API keys status"""
        try:
            # Create status window
            status_window = tk.Toplevel(self.settings_window)
            status_window.title("🔍 حالة مفاتيح API")
            status_window.geometry("600x500")
            status_window.configure(bg='#2b2b2b')
            status_window.transient(self.settings_window)
            status_window.grab_set()
            
            # Status text area
            status_text = scrolledtext.ScrolledText(
                status_window,
                bg='#1a1a1a',
                fg='#ffffff',
                font=("Consolas", 10)
            )
            status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            status_text.insert(tk.END, "🔍 جاري فحص مفاتيح API...\n\n")
            status_window.update()
            
            # Check each key
            for i, key in enumerate(EMBEDDED_CONFIG['GEMINI_API_KEYS']):
                masked_key = f"{key[:8]}...{key[-8:]}"
                status_text.insert(tk.END, f"🔑 المفتاح {i+1}: {masked_key}\n")
                status_window.update()
                
                # Test the actual API key if Gemini is available
                try:
                    if GEMINI_AVAILABLE:
                        genai.configure(api_key=key)
                        model = genai.GenerativeModel('gemini-pro')
                        response = model.generate_content("Test")
                        
                        if response and response.text:
                            status_text.insert(tk.END, "   ✅ يعمل بشكل طبيعي\n")
                            status_text.tag_add("green", f"{status_text.index(tk.END)}-2l", f"{status_text.index(tk.END)}-1l")
                        else:
                            status_text.insert(tk.END, "   ❌ رصيد منتهي أو خطأ\n")
                            status_text.tag_add("red", f"{status_text.index(tk.END)}-2l", f"{status_text.index(tk.END)}-1l")
                    else:
                        status_text.insert(tk.END, "   ⚠️ مكتبة Gemini غير متوفرة\n")
                        status_text.tag_add("yellow", f"{status_text.index(tk.END)}-2l", f"{status_text.index(tk.END)}-1l")
                        
                except Exception as api_error:
                    error_msg = str(api_error).lower()
                    if any(term in error_msg for term in ['quota', 'limit', 'billing', 'exceeded']):
                        status_text.insert(tk.END, "   ❌ رصيد منتهي\n")
                        status_text.tag_add("red", f"{status_text.index(tk.END)}-2l", f"{status_text.index(tk.END)}-1l")
                    else:
                        status_text.insert(tk.END, f"   ❌ خطأ: {str(api_error)[:50]}...\n")
                        status_text.tag_add("red", f"{status_text.index(tk.END)}-2l", f"{status_text.index(tk.END)}-1l")
                
                status_text.see(tk.END)
                time.sleep(0.5)  # Small delay between checks
            
            # Configure text colors
            status_text.tag_config("green", foreground="#00ff00")
            status_text.tag_config("red", foreground="#ff0000")
            status_text.tag_config("yellow", foreground="#ffff00")
            
            status_text.insert(tk.END, "\n✅ تم الانتهاء من فحص جميع المفاتيح")
            
            # Close button
            close_button = tk.Button(
                status_window,
                text="❌ إغلاق",
                font=("Arial", 10),
                bg='#666666',
                fg='white',
                command=status_window.destroy
            )
            close_button.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في فحص المفاتيح: {str(e)}")
    
    def load_mt5_settings(self):
        """Load MT5 settings into fields"""
        try:
            self.mt5_account_entry.delete(0, tk.END)
            self.mt5_password_entry.delete(0, tk.END)
            self.mt5_server_entry.delete(0, tk.END)
            
            if EMBEDDED_CONFIG.get('MT5_LOGIN'):
                self.mt5_account_entry.insert(0, str(EMBEDDED_CONFIG['MT5_LOGIN']))
            if EMBEDDED_CONFIG.get('MT5_PASSWORD'):
                self.mt5_password_entry.insert(0, EMBEDDED_CONFIG['MT5_PASSWORD'])
            if EMBEDDED_CONFIG.get('MT5_SERVER'):
                self.mt5_server_entry.insert(0, EMBEDDED_CONFIG['MT5_SERVER'])
                
        except Exception as e:
            self.add_log(f"خطأ في تحميل إعدادات MT5: {str(e)}")
    
    def save_mt5_settings(self):
        """Save MT5 settings"""
        try:
            EMBEDDED_CONFIG['MT5_LOGIN'] = self.mt5_account_entry.get().strip() or None
            EMBEDDED_CONFIG['MT5_PASSWORD'] = self.mt5_password_entry.get().strip() or None
            EMBEDDED_CONFIG['MT5_SERVER'] = self.mt5_server_entry.get().strip() or None
            
            self.save_config()
            messagebox.showinfo("نجح", "تم حفظ إعدادات MT5 بنجاح")
            self.add_log("💾 تم حفظ إعدادات MT5")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حفظ إعدادات MT5: {str(e)}")
    
    def test_mt5_connection(self):
        """Test MT5 connection"""
        try:
            if not MT5_AVAILABLE:
                messagebox.showerror("خطأ", "مكتبة MetaTrader5 غير متوفرة")
                return
            
            # Show progress
            progress_window = tk.Toplevel(self.settings_window)
            progress_window.title("اختبار الاتصال")
            progress_window.geometry("400x150")
            progress_window.configure(bg='#2b2b2b')
            progress_window.transient(self.settings_window)
            progress_window.grab_set()
            
            progress_label = tk.Label(
                progress_window,
                text="🔗 جاري اختبار الاتصال بـ MT5...",
                font=("Arial", 12),
                fg='#ffffff',
                bg='#2b2b2b'
            )
            progress_label.pack(expand=True)
            
            progress_window.update()
            
            # Test actual connection
            try:
                if mt5.initialize():
                    account_info = mt5.account_info()
                    if account_info:
                        progress_window.destroy()
                        messagebox.showinfo(
                            "نتيجة الاختبار", 
                            f"✅ تم الاتصال بـ MT5 بنجاح\n\n"
                            f"رقم الحساب: {account_info.login}\n"
                            f"الخادم: {account_info.server}\n"
                            f"الشركة: {account_info.company}"
                        )
                        self.add_log("🔗 تم اختبار اتصال MT5 بنجاح")
                    else:
                        progress_window.destroy()
                        messagebox.showerror("فشل الاختبار", "❌ فشل في جلب معلومات الحساب")
                else:
                    progress_window.destroy()
                    error_code = mt5.last_error()
                    messagebox.showerror("فشل الاختبار", f"❌ فشل في الاتصال بـ MT5\nكود الخطأ: {error_code}")
                    
            except Exception as mt5_error:
                progress_window.destroy()
                messagebox.showerror("خطأ", f"❌ خطأ في اختبار MT5: {str(mt5_error)}")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في اختبار الاتصال: {str(e)}")
    
    def load_telegram_settings(self):
        """Load Telegram settings into fields"""
        try:
            self.telegram_token_entry.delete(0, tk.END)
            self.bot_password_entry.delete(0, tk.END)
            
            if EMBEDDED_CONFIG.get('BOT_TOKEN'):
                self.telegram_token_entry.insert(0, EMBEDDED_CONFIG['BOT_TOKEN'])
            if EMBEDDED_CONFIG.get('BOT_PASSWORD'):
                self.bot_password_entry.insert(0, EMBEDDED_CONFIG['BOT_PASSWORD'])
                
        except Exception as e:
            self.add_log(f"خطأ في تحميل إعدادات Telegram: {str(e)}")
    
    def save_telegram_settings(self):
        """Save Telegram settings"""
        try:
            EMBEDDED_CONFIG['BOT_TOKEN'] = self.telegram_token_entry.get().strip()
            EMBEDDED_CONFIG['BOT_PASSWORD'] = self.bot_password_entry.get().strip()
            
            self.save_config()
            messagebox.showinfo("نجح", "تم حفظ إعدادات Telegram بنجاح")
            self.add_log("💾 تم حفظ إعدادات Telegram")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حفظ إعدادات Telegram: {str(e)}")
    
    def test_telegram_token(self):
        """Test Telegram bot token"""
        try:
            token = self.telegram_token_entry.get().strip()
            if not token:
                messagebox.showwarning("تحذير", "يرجى إدخال رمز البوت أولاً")
                return
            
            # Show progress
            progress_window = tk.Toplevel(self.settings_window)
            progress_window.title("اختبار رمز البوت")
            progress_window.geometry("400x150")
            progress_window.configure(bg='#2b2b2b')
            progress_window.transient(self.settings_window)
            progress_window.grab_set()
            
            progress_label = tk.Label(
                progress_window,
                text="🔗 جاري اختبار رمز Telegram Bot...",
                font=("Arial", 12),
                fg='#ffffff',
                bg='#2b2b2b'
            )
            progress_label.pack(expand=True)
            
            progress_window.update()
            
            # Test the token
            try:
                test_bot = telebot.TeleBot(token)
                bot_info = test_bot.get_me()
                
                progress_window.destroy()
                messagebox.showinfo(
                    "نتيجة الاختبار",
                    f"✅ رمز البوت صحيح!\n\n"
                    f"اسم البوت: {bot_info.first_name}\n"
                    f"معرف البوت: @{bot_info.username}\n"
                    f"ID: {bot_info.id}"
                )
                self.add_log("🔗 تم اختبار رمز Telegram بنجاح")
                
            except Exception as token_error:
                progress_window.destroy()
                messagebox.showerror("فشل الاختبار", f"❌ رمز البوت غير صحيح:\n{str(token_error)}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في اختبار الرمز: {str(e)}")
    
    def save_gemini_settings(self):
        """Save Gemini API settings"""
        try:
            self.save_config()
            messagebox.showinfo("نجح", "تم حفظ إعدادات Gemini API بنجاح")
            self.add_log("💾 تم حفظ إعدادات Gemini API")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حفظ إعدادات Gemini: {str(e)}")
    
    def save_logs_to_file(self):
        """Save logs to a text file"""
        try:
            from tkinter import filedialog
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="حفظ سجل الأحداث",
                initialvalue=f"bot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if filename:
                logs_content = self.log_text.get("1.0", tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"🤖 سجل أحداث بوت التداول v1.2.0\n")
                    f.write(f"تاريخ الحفظ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(logs_content)
                
                messagebox.showinfo("نجح", f"تم حفظ السجل في:\n{filename}")
                self.add_log(f"💾 تم حفظ السجل في ملف: {os.path.basename(filename)}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ السجل: {str(e)}")
    
    def clear_logs(self):
        """Clear the logs display"""
        try:
            result = messagebox.askyesno(
                "تأكيد المسح",
                "هل أنت متأكد من مسح جميع السجلات؟\n\n(سيتم الاحتفاظ بالسجلات في ملف bot.log)"
            )
            
            if result:
                self.log_text.delete("1.0", tk.END)
                self.add_log("🧹 تم مسح عرض السجل (الملفات محفوظة)")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في مسح السجل: {str(e)}")
    
    def update_uptime(self):
        """Update uptime counter"""
        try:
            if hasattr(self, 'start_time') and hasattr(self, 'uptime_label'):
                current_time = datetime.now()
                uptime = current_time - self.start_time
                
                # Format uptime as HH:MM:SS
                total_seconds = int(uptime.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.uptime_label.config(text=f"⏱️ وقت تشغيل الواجهة: {uptime_str}")
                
                # Schedule next update
                self.root.after(1000, self.update_uptime)
                
        except Exception as e:
            # Silent error handling for uptime
            pass
    
    def update_bot_uptime(self):
        """Update bot uptime counter"""
        try:
            if hasattr(self, 'bot_start_time') and hasattr(self, 'bot_uptime_label'):
                if self.bot_start_time and self.embedded_bot.is_running:
                    current_time = datetime.now()
                    bot_uptime = current_time - self.bot_start_time
                    
                    # Format uptime as HH:MM:SS
                    total_seconds = int(bot_uptime.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    
                    bot_uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    self.bot_uptime_label.config(
                        text=f"🤖 وقت تشغيل البوت: {bot_uptime_str}",
                        fg='#00ff00'
                    )
                else:
                    self.bot_uptime_label.config(
                        text="🤖 وقت تشغيل البوت: متوقف",
                        fg='#ff6666'
                    )
                
                # Schedule next update
                self.root.after(1000, self.update_bot_uptime)
                
        except Exception as e:
            # Silent error handling for bot uptime
            pass
    
    def change_bot_password(self):
        """Change bot password"""
        try:
            new_password = self.new_bot_password_entry.get().strip()
            confirm_password = self.confirm_bot_password_entry.get().strip()
            
            # Validation
            if not new_password:
                messagebox.showwarning("تحذير", "يرجى إدخال كلمة المرور الجديدة")
                return
            
            if len(new_password) < 6:
                messagebox.showwarning("تحذير", "كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                return
            
            if new_password != confirm_password:
                messagebox.showerror("خطأ", "كلمة المرور وتأكيدها غير متطابقين")
                return
            
            # Confirm change
            result = messagebox.askyesno(
                "تأكيد التغيير",
                f"هل أنت متأكد من تغيير كلمة مرور البوت إلى:\n'{new_password}'?\n\nسيتطلب هذا إعادة تشغيل البوت إذا كان يعمل."
            )
            
            if result:
                # Update config
                EMBEDDED_CONFIG['BOT_PASSWORD'] = new_password
                self.save_config()
                
                # Update display
                self.current_bot_password_display.config(text=new_password)
                
                # Clear entries
                self.new_bot_password_entry.delete(0, tk.END)
                self.confirm_bot_password_entry.delete(0, tk.END)
                
                # Update embedded bot config
                self.embedded_bot.config = EMBEDDED_CONFIG
                
                messagebox.showinfo("نجح", "تم تغيير كلمة مرور البوت بنجاح!\n\nإذا كان البوت يعمل، يرجى إعادة تشغيله لتطبيق التغيير.")
                self.add_log(f"🔑 تم تغيير كلمة مرور البوت إلى: {new_password}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في تغيير كلمة المرور: {str(e)}")
    
    def reset_bot_password(self):
        """Reset bot password to default"""
        try:
            result = messagebox.askyesno(
                "إعادة تعيين كلمة المرور",
                "هل أنت متأكد من إعادة تعيين كلمة مرور البوت إلى القيمة الافتراضية؟\n\n(tra12345678)"
            )
            
            if result:
                default_password = "tra12345678"
                EMBEDDED_CONFIG['BOT_PASSWORD'] = default_password
                self.save_config()
                
                # Update display
                self.current_bot_password_display.config(text=default_password)
                
                # Update embedded bot config
                self.embedded_bot.config = EMBEDDED_CONFIG
                
                messagebox.showinfo("نجح", "تم إعادة تعيين كلمة مرور البوت للقيمة الافتراضية")
                self.add_log("🔄 تم إعادة تعيين كلمة مرور البوت للافتراضي")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في إعادة تعيين كلمة المرور: {str(e)}")
    
    def change_ui_password(self):
        """Change UI password"""
        try:
            new_password = self.new_ui_password_entry.get().strip()
            confirm_password = self.confirm_ui_password_entry.get().strip()
            
            # Validation
            if not new_password:
                messagebox.showwarning("تحذير", "يرجى إدخال كلمة المرور الجديدة")
                return
            
            if len(new_password) < 6:
                messagebox.showwarning("تحذير", "كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                return
            
            if new_password != confirm_password:
                messagebox.showerror("خطأ", "كلمة المرور وتأكيدها غير متطابقين")
                return
            
            # Confirm change
            result = messagebox.askyesno(
                "تأكيد التغيير",
                f"هل أنت متأكد من تغيير كلمة مرور الواجهة؟\n\nستحتاج لاستخدام كلمة المرور الجديدة في المرة القادمة."
            )
            
            if result:
                # Update password
                self.PASSWORD = new_password
                
                # Clear entries
                self.new_ui_password_entry.delete(0, tk.END)
                self.confirm_ui_password_entry.delete(0, tk.END)
                
                messagebox.showinfo("نجح", "تم تغيير كلمة مرور الواجهة بنجاح!\n\nستحتاج لاستخدام كلمة المرور الجديدة في المرة القادمة.")
                self.add_log(f"🔐 تم تغيير كلمة مرور الواجهة")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في تغيير كلمة مرور الواجهة: {str(e)}")
    
    def show_about_dialog(self):
        """Show About dialog with developer information"""
        try:
            # Create about window
            about_window = tk.Toplevel(self.root)
            about_window.title("ℹ️ حول البرنامج")
            about_window.geometry("500x600")
            about_window.configure(bg='#2b2b2b')
            about_window.transient(self.root)
            about_window.grab_set()
            about_window.resizable(False, False)
            
            # Center the window
            about_window.geometry("+%d+%d" % (
                about_window.winfo_screenwidth()//2 - 250,
                about_window.winfo_screenheight()//2 - 300
            ))
            
            # Main frame
            main_frame = tk.Frame(about_window, bg='#2b2b2b')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # App icon/title
            title_label = tk.Label(
                main_frame,
                text="🤖",
                font=("Arial", 48),
                fg='#00ff00',
                bg='#2b2b2b'
            )
            title_label.pack(pady=10)
            
            # App name
            app_name_label = tk.Label(
                main_frame,
                text="بوت التداول المتقدم",
                font=("Arial", 20, "bold"),
                fg='#ffffff',
                bg='#2b2b2b'
            )
            app_name_label.pack(pady=5)
            
            # Version
            version_label = tk.Label(
                main_frame,
                text="الإصدار v1.2.0 Enhanced",
                font=("Arial", 12),
                fg='#cccccc',
                bg='#2b2b2b'
            )
            version_label.pack(pady=5)
            
            # Separator
            separator1 = tk.Frame(main_frame, height=2, bg='#555555')
            separator1.pack(fill=tk.X, pady=15)
            
            # Developer section
            dev_title = tk.Label(
                main_frame,
                text="👨‍💻 معلومات المطور",
                font=("Arial", 14, "bold"),
                fg='#00ff00',
                bg='#2b2b2b'
            )
            dev_title.pack(pady=10)
            
            # Developer name
            dev_name_label = tk.Label(
                main_frame,
                text="المطور: Mohamad Zalaf",
                font=("Arial", 12, "bold"),
                fg='#ffffff',
                bg='#2b2b2b'
            )
            dev_name_label.pack(pady=5)
            
            # Email
            email_label = tk.Label(
                main_frame,
                text="📧 البريد الإلكتروني:",
                font=("Arial", 10),
                fg='#cccccc',
                bg='#2b2b2b'
            )
            email_label.pack(pady=2)
            
            email_value = tk.Label(
                main_frame,
                text="Mohamadzalaf2017@gmail.com",
                font=("Arial", 11, "bold"),
                fg='#2196F3',
                bg='#2b2b2b',
                cursor="hand2"
            )
            email_value.pack(pady=2)
            
            # Make email clickable
            def copy_email(event):
                about_window.clipboard_clear()
                about_window.clipboard_append("Mohamadzalaf2017@gmail.com")
                messagebox.showinfo("تم النسخ", "تم نسخ البريد الإلكتروني إلى الحافظة")
            
            email_value.bind("<Button-1>", copy_email)
            
            # Separator
            separator2 = tk.Frame(main_frame, height=2, bg='#555555')
            separator2.pack(fill=tk.X, pady=15)
            
            # Application info
            app_info_title = tk.Label(
                main_frame,
                text="📋 معلومات التطبيق",
                font=("Arial", 14, "bold"),
                fg='#00ff00',
                bg='#2b2b2b'
            )
            app_info_title.pack(pady=10)
            
            # Features list
            features_text = """✨ الميزات الرئيسية:
• واجهة تحكم شاملة لبوت التداول
• إدارة متقدمة للمستخدمين مع نظام الحظر
• إعدادات Telegram و Gemini API و MT5
• نظام حماية متعدد المستويات
• تضمين كامل للكود المصدري
• حفظ وإدارة السجلات
• عدادات وقت التشغيل المزدوجة

🔒 الأمان والحماية:
• حماية بكلمة مرور للواجهة الرئيسية
• حماية إضافية لإدارة المستخدمين
• حماية خاصة لتبويب الحماية والأمان
• إخفاء المعلومات الحساسة

📅 تاريخ الإصدار: يناير 2025
©️ جميع الحقوق محفوظة"""
            
            features_label = tk.Label(
                main_frame,
                text=features_text,
                font=("Arial", 9),
                fg='#cccccc',
                bg='#2b2b2b',
                justify=tk.LEFT
            )
            features_label.pack(pady=10)
            
            # Close button
            close_button = tk.Button(
                main_frame,
                text="❌ إغلاق",
                font=("Arial", 12, "bold"),
                bg='#666666',
                fg='white',
                width=15,
                command=about_window.destroy
            )
            close_button.pack(pady=20)
            
            self.add_log("ℹ️ تم عرض نافذة معلومات البرنامج")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في عرض نافذة حول: {str(e)}")
     
    def save_config(self):
        """Save configuration to file"""
        try:
            # Save to a config file
            config_file = os.path.join(DATA_DIR, "gui_config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(EMBEDDED_CONFIG, f, ensure_ascii=False, indent=2)
            
            # Update embedded bot config
            self.embedded_bot.config = EMBEDDED_CONFIG
            
        except Exception as e:
            self.add_log(f"خطأ في حفظ الإعدادات: {str(e)}")
    
    def show_login(self):
        """Show login interface"""
        self.control_frame.pack_forget()
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        self.password_entry.focus()
    
    def show_control(self):
        """Show control interface"""
        self.login_frame.pack_forget()
        self.control_frame.pack(fill=tk.BOTH, expand=True)
    
    def check_password(self):
        """Check entered password"""
        entered_password = self.password_entry.get()
        
        if entered_password == self.PASSWORD:
            self.is_logged_in = True
            self.login_status_label.config(text="✅ تم تسجيل الدخول بنجاح!", fg='#00ff00')
            self.add_log("🔐 تم تسجيل دخول المستخدم بنجاح")
            self.root.after(1000, self.show_control)
        else:
            self.login_status_label.config(text="❌ كلمة مرور خاطئة!", fg='#ff6666')
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def logout(self):
        """Logout user"""
        self.is_logged_in = False
        self.password_entry.delete(0, tk.END)
        self.login_status_label.config(text="")
        self.add_log("🚪 تم تسجيل خروج المستخدم")
        self.show_login()
        
        # Close settings window if open
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.destroy()
    
    def start_bot(self):
        """Start the embedded bot"""
        if not self.is_logged_in:
            messagebox.showerror("رفض الوصول", "يرجى تسجيل الدخول أولاً!")
            return
        
        self.add_log("🚀 جاري تشغيل بوت التداول المدمج...")
        success, message = self.embedded_bot.start_bot()
        
        if success:
            self.status_indicator.config(text="🟢 يعمل", fg='#00ff00')
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.add_log(f"✅ {message}")
            
            # Reset start time for uptime counter
            self.bot_start_time = datetime.now()
            self.update_bot_uptime()
        else:
            self.add_log(f"❌ {message}")
            messagebox.showerror("خطأ", message)
    
    def stop_bot(self):
        """Stop the embedded bot"""
        if not self.is_logged_in:
            messagebox.showerror("رفض الوصول", "يرجى تسجيل الدخول أولاً!")
            return
        
        self.add_log("🛑 جاري إيقاف بوت التداول المدمج...")
        success, message = self.embedded_bot.stop_bot()
        
        if success:
            self.status_indicator.config(text="⚫ متوقف", fg='#ff6666')
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.add_log(f"✅ {message}")
            
            # Reset bot start time
            self.bot_start_time = None
        else:
            self.add_log(f"❌ {message}")
            messagebox.showerror("خطأ", message)
    
    def add_log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Keep only last 1000 lines
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 1000:
            self.log_text.delete("1.0", f"{len(lines)-1000}.0")
    
    def start_monitoring(self):
        """Start monitoring thread"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self.monitor_system, daemon=True)
            self.monitoring_thread.start()
    
    def monitor_system(self):
        """Monitor system status"""
        while self.is_monitoring:
            try:
                # Update users count button
                if hasattr(self, 'users_count_button'):
                    users_count = self.embedded_bot.get_users_count()
                    self.root.after(0, lambda: self.users_count_button.config(
                        text=f"👥 عدد المستخدمين: {users_count}"
                    ))
                
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)
    
    def on_closing(self):
        """Handle window closing"""
        if self.embedded_bot.is_running:
            if messagebox.askokcancel("إنهاء", "البوت لا يزال يعمل. إيقاف البوت والخروج؟"):
                self.embedded_bot.stop_bot()
                self.is_monitoring = False
                self.root.destroy()
        else:
            self.is_monitoring = False
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = TradingBotUI()
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 تم إنهاء التطبيق بواسطة المستخدم")
    except Exception as e:
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror(
            "خطأ في التطبيق", 
            f"❌ حدث خطأ في التطبيق:\n\n{str(e)}\n\nيرجى التحقق من تفاصيل الخطأ والمحاولة مرة أخرى."
        )
        temp_root.destroy()