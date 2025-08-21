#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 Trading Bot UI Controller v1.2.0 - EMBEDDED VERSION
====================================================
English GUI Interface for Advanced Trading Bot Control with Embedded Bot

Features:
- Start/Stop Bot Control
- Real-time Status Monitoring
- Event Logging with Timestamps
- Password Protection
- Process Management
- User-friendly Interface
- Users Count Window (Maroon background, Red text)
- Embedded Bot Code (No external .py files needed)
- Uses Original JSON System (No SQLite Database)

Developer: Mohamad Zalaf ©️2025
Compatible with: Embedded tbot_v1.2.0.py
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import subprocess
import os
import sys
import threading
import time
import json
from typing import Dict, List, Optional, Any
import glob

# ===============================================
# EMBEDDED BOT CODE START
# ===============================================

# Import all required libraries for the embedded bot
import telebot
from telebot import apihelper
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import google.generativeai as genai
from telebot import types
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from datetime import datetime, timedelta
import ta
from PIL import Image, ImageDraw, ImageFont
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Bot configuration (embedded)
BOT_TOKEN = '7703327028:AAHLqgR1HtVPsq6LfUKEWzNEgLZjJPLa6YU'
BOT_PASSWORD = 'tra12345678'
GEMINI_API_KEY = 'AIzaSyDAOp1ARgrkUvPcmGmXddFx8cqkzhy-3O8'
GEMINI_API_KEYS = [GEMINI_API_KEY]

# Bot settings
MONITORING_INTERVAL = 30
MIN_CONFIDENCE_THRESHOLD = 70
MAX_DAILY_ALERTS = 50
GEMINI_MODEL = 'gemini-2.0-flash'

# Data directories (same as original bot)
DATA_DIR = "trading_data"
USERS_DIR = os.path.join(DATA_DIR, "users")
FEEDBACK_DIR = os.path.join(DATA_DIR, "user_feedback")
TRADE_LOGS_DIR = os.path.join(DATA_DIR, "trade_logs")
CHAT_LOGS_DIR = os.path.join(DATA_DIR, "chat_logs")

# Create directories if they don't exist
for directory in [DATA_DIR, USERS_DIR, FEEDBACK_DIR, TRADE_LOGS_DIR, CHAT_LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

class EmbeddedTradingBot:
    """Embedded Trading Bot Class - Uses Original JSON System"""
    
    def __init__(self):
        self.bot = None
        self.is_running = False
        self.user_sessions = {}  # In-memory sessions (like original)
        self.authenticated_users = set()
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
        
    def get_users_count(self):
        """Get total number of users from JSON files (original system)"""
        try:
            # Count JSON files in users directory
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
                        
                    # Extract user ID from filename
                    user_id = os.path.basename(user_file).replace('user_', '').replace('.json', '')
                    
                    # Get user details
                    username = user_data.get('username', 'غير محدد')
                    first_name = user_data.get('first_name', 'غير محدد')
                    last_name = user_data.get('last_name', '')
                    full_name = f"{first_name} {last_name}".strip()
                    
                    # Get additional info
                    registration_date = user_data.get('registration_date', 'غير محدد')
                    last_activity = user_data.get('last_activity', 'غير محدد')
                    trading_mode = user_data.get('trading_mode', 'غير محدد')
                    
                    users_details.append({
                        'user_id': user_id,
                        'username': username,
                        'full_name': full_name,
                        'registration_date': registration_date,
                        'last_activity': last_activity,
                        'trading_mode': trading_mode
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error reading user file {user_file}: {e}")
                    continue
            
            # Sort by user ID
            users_details.sort(key=lambda x: int(x['user_id']) if x['user_id'].isdigit() else 0)
            return users_details
            
        except Exception as e:
            self.logger.error(f"Error getting users details: {e}")
            return []
    
    def load_user_data(self, user_id):
        """Load user data from JSON file (original system)"""
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
        """Save user data to JSON file (original system)"""
        try:
            user_data = {
                'user_id': str(user_id),
                'username': username,
                'first_name': first_name,
                'join_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_active': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Check if user already exists
            existing_data = self.load_user_data(user_id)
            if existing_data:
                # Update only last_active, keep original join_date
                user_data['join_date'] = existing_data.get('join_date', user_data['join_date'])
                user_data['username'] = username or existing_data.get('username')
                user_data['first_name'] = first_name or existing_data.get('first_name')
            
            user_file = os.path.join(USERS_DIR, f"user_{user_id}.json")
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"User data saved for {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving user data for {user_id}: {e}")
    
    def authenticate_user(self, user_id):
        """Mark user as authenticated (in-memory, like original)"""
        try:
            self.authenticated_users.add(user_id)
            self.user_sessions[user_id] = {
                'authenticated': True,
                'login_time': datetime.now()
            }
            self.logger.info(f"User {user_id} authenticated successfully")
            
        except Exception as e:
            self.logger.error(f"Error authenticating user {user_id}: {e}")
    
    def is_authenticated(self, user_id):
        """Check if user is authenticated (original system)"""
        return self.user_sessions.get(user_id, {}).get('authenticated', False)
    
    def start_bot(self):
        """Start the trading bot"""
        if self.is_running:
            return False, "Bot is already running"
            
        try:
            # Initialize bot
            apihelper.CONNECT_TIMEOUT = 60
            apihelper.READ_TIMEOUT = 60
            apihelper.RETRY_TIMEOUT = 5
            
            self.bot = telebot.TeleBot(BOT_TOKEN)
            self.setup_handlers()
            
            # Start polling in a separate thread
            self.bot_thread = threading.Thread(target=self._run_bot, daemon=True)
            self.is_running = True
            self.bot_thread.start()
            
            self.logger.info("Trading bot started successfully")
            return True, "Bot started successfully"
            
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            return False, f"Error starting bot: {e}"
    
    def stop_bot(self):
        """Stop the trading bot"""
        if not self.is_running:
            return False, "Bot is not running"
            
        try:
            self.is_running = False
            if self.bot:
                self.bot.stop_polling()
            
            self.logger.info("Trading bot stopped")
            return True, "Bot stopped successfully"
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
            return False, f"Error stopping bot: {e}"
    
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
            
            # Save user data to JSON (original system)
            self.save_user_data(user_id, username, first_name)
            
            welcome_text = """
🤖 أهلاً بك في بوت التداول المتقدم v1.2.0

للوصول إلى الميزات المتقدمة، يرجى إدخال كلمة المرور:
            """
            
            self.bot.reply_to(message, welcome_text)
        
        @self.bot.message_handler(func=lambda message: not self.is_authenticated(message.from_user.id))
        def handle_password(message):
            user_id = message.from_user.id
            
            if message.text == BOT_PASSWORD:
                self.authenticate_user(user_id)
                
                # Create main keyboard
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
                self.bot.reply_to(message, "❌ كلمة مرور خاطئة. حاول مرة أخرى.")
        
        @self.bot.message_handler(func=lambda message: self.is_authenticated(message.from_user.id))
        def handle_authenticated_messages(message):
            user_id = message.from_user.id
            text = message.text
            
            # Update user activity
            self.save_user_data(user_id, message.from_user.username, message.from_user.first_name)
            
            if text == "📊 تحليل الأسواق":
                self.bot.reply_to(message, "🔄 جاري تحليل الأسواق... يرجى الانتظار")
                # Add market analysis logic here
                
            elif text == "💰 الأسعار المباشرة":
                self.bot.reply_to(message, "📈 جاري جلب الأسعار المباشرة...")
                # Add live prices logic here
                
            elif text == "📈 توصيات التداول":
                self.bot.reply_to(message, "🤖 جاري تحليل التوصيات...")
                # Add trading recommendations logic here
                
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
# EMBEDDED BOT CODE END
# ===============================================

class TradingBotUI:
    def __init__(self):
        self.embedded_bot = EmbeddedTradingBot()
        self.PASSWORD = "041768454"  # Custom UI password
        self.is_logged_in = False
        self.monitoring_thread = None
        self.is_monitoring = False
        self.users_count_window = None
        
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
        self.root.title("🤖 Trading Bot Controller v1.2.0 - EMBEDDED")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Set window icon (optional)
        try:
            self.root.iconbitmap("icon.ico")
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
            text="🤖 Trading Bot Controller",
            font=("Arial", 24, "bold"),
            fg='#00ff00',
            bg='#2b2b2b'
        )
        title_label.pack(pady=30)
        
        # Subtitle
        subtitle_label = tk.Label(
            self.login_frame,
            text="Advanced Trading Bot Control Panel v1.2.0 - JSON System",
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
            text="🔐 Enter Password:",
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
            text="🚀 LOGIN",
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
        
        # Title
        header_label = tk.Label(
            header_frame,
            text="🤖 Trading Bot Control Panel - JSON SYSTEM",
            font=("Arial", 18, "bold"),
            fg='#00ff00',
            bg='#2b2b2b'
        )
        header_label.pack(side=tk.LEFT)
        
        # Users details button
        users_details_button = tk.Button(
            header_frame,
            text="📋 Users Details",
            font=("Arial", 9, "bold"),
            bg='#4a4a4a',  # Dark gray
            fg='#ffffff',  # White text
            command=self.show_users_details_window
        )
        users_details_button.pack(side=tk.RIGHT, padx=5)
        
        # Users count button
        self.users_count_button = tk.Button(
            header_frame,
            text="👥 Users Count",
            font=("Arial", 10, "bold"),
            bg='#800020',  # Maroon color
            fg='#ff0000',  # Red text
            command=self.show_users_count_window
        )
        self.users_count_button.pack(side=tk.RIGHT, padx=5)
        
        # Logout button
        logout_button = tk.Button(
            header_frame,
            text="🚪 Logout",
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
            text="🚀 START BOT",
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
            text="🛑 STOP BOT",
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
            text="📊 Bot Status:",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        status_label.pack(anchor=tk.W)
        
        # Status indicator
        self.status_indicator = tk.Label(
            status_frame,
            text="⚫ Stopped",
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
            text="📝 Event Log:",
            font=("Arial", 12, "bold"),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        log_label.pack(anchor=tk.W)
        
        # Log text area
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
        
        # Add initial log message
        self.add_log("🔧 Bot Controller Initialized - JSON SYSTEM VERSION")
        self.add_log("ℹ️  Using original JSON file system (no database)")
        self.add_log("📁 Users stored in: trading_data/users/")
        self.add_log("📁 AI training files kept external (as designed)")
        self.add_log("🔐 Please login to access controls")
    
    def show_users_count_window(self):
        """Show users count in a separate window"""
        if self.users_count_window and self.users_count_window.winfo_exists():
            self.users_count_window.lift()
            return
        
        # Create users count window
        self.users_count_window = tk.Toplevel(self.root)
        self.users_count_window.title("👥 Users Count")
        self.users_count_window.geometry("350x180")
        self.users_count_window.resizable(False, False)
        self.users_count_window.configure(bg='#800020')  # Maroon background
        
        # Center the window
        self.users_count_window.transient(self.root)
        self.users_count_window.grab_set()
        
        # Main frame
        main_frame = tk.Frame(self.users_count_window, bg='#800020')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title label
        title_label = tk.Label(
            main_frame,
            text="👥 Total Users",
            font=("Arial", 16, "bold"),
            fg='white',
            bg='#800020'
        )
        title_label.pack(pady=10)
        
        # Users count label
        users_count = self.embedded_bot.get_users_count()
        self.users_count_label = tk.Label(
            main_frame,
            text=str(users_count),
            font=("Arial", 32, "bold"),
            fg='#ff0000',  # Red text
            bg='#800020'
        )
        self.users_count_label.pack(pady=10)
        
        # Data source info
        source_label = tk.Label(
            main_frame,
            text="(من ملفات JSON)",
            font=("Arial", 10),
            fg='#ffcccc',
            bg='#800020'
        )
        source_label.pack(pady=2)
        
        # Last updated label
        last_updated = tk.Label(
            main_frame,
            text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')}",
            font=("Arial", 10),
            fg='#ffcccc',
            bg='#800020'
        )
        last_updated.pack(pady=5)
        
        # Auto-refresh the count every 5 seconds
        def refresh_count():
            if self.users_count_window and self.users_count_window.winfo_exists():
                users_count = self.embedded_bot.get_users_count()
                self.users_count_label.config(text=str(users_count))
                last_updated.config(text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
                self.users_count_window.after(5000, refresh_count)
        
        refresh_count()
    
    def show_users_details_window(self):
        """Show detailed users information in a separate window"""
        try:
            # Create users details window
            details_window = tk.Toplevel(self.root)
            details_window.title("📋 Users Details")
            details_window.geometry("900x600")
            details_window.configure(bg='#2b2b2b')
            
            # Center the window
            details_window.transient(self.root)
            details_window.grab_set()
            
            # Main frame with scrollbar
            main_frame = tk.Frame(details_window, bg='#2b2b2b')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Title label
            title_label = tk.Label(
                main_frame,
                text="📋 Users Details",
                font=("Arial", 16, "bold"),
                fg='#ffffff',
                bg='#2b2b2b'
            )
            title_label.pack(pady=10)
            
            # Create Treeview for users data
            columns = ('ID', 'Username', 'Full Name', 'Trading Mode', 'Registration', 'Last Activity')
            tree_frame = tk.Frame(main_frame, bg='#2b2b2b')
            tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Create Treeview with scrollbars
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
            
            # Configure column headings and widths
            users_tree.heading('ID', text='User ID')
            users_tree.heading('Username', text='Username')
            users_tree.heading('Full Name', text='Full Name')
            users_tree.heading('Trading Mode', text='Trading Mode')
            users_tree.heading('Registration', text='Registration Date')
            users_tree.heading('Last Activity', text='Last Activity')
            
            users_tree.column('ID', width=100, minwidth=80)
            users_tree.column('Username', width=120, minwidth=100)
            users_tree.column('Full Name', width=150, minwidth=120)
            users_tree.column('Trading Mode', width=120, minwidth=100)
            users_tree.column('Registration', width=150, minwidth=120)
            users_tree.column('Last Activity', width=150, minwidth=120)
            
            users_tree.pack(fill=tk.BOTH, expand=True)
            
            # Get users details and populate tree
            users_details = self.embedded_bot.get_users_details()
            
            for user in users_details:
                users_tree.insert('', tk.END, values=(
                    user['user_id'],
                    user['username'],
                    user['full_name'],
                    user['trading_mode'],
                    user['registration_date'][:10] if len(user['registration_date']) > 10 else user['registration_date'],
                    user['last_activity'][:10] if len(user['last_activity']) > 10 else user['last_activity']
                ))
            
            # Status label
            status_label = tk.Label(
                main_frame,
                text=f"Total Users: {len(users_details)}",
                font=("Arial", 12, "bold"),
                fg='#00ff00',
                bg='#2b2b2b'
            )
            status_label.pack(pady=5)
            
            # Buttons frame
            buttons_frame = tk.Frame(main_frame, bg='#2b2b2b')
            buttons_frame.pack(pady=10)
            
            # Refresh button
            refresh_button = tk.Button(
                buttons_frame,
                text="🔄 Refresh",
                font=("Arial", 10, "bold"),
                bg='#4CAF50',
                fg='white',
                command=lambda: self.refresh_users_tree(users_tree, status_label)
            )
            refresh_button.pack(side=tk.LEFT, padx=5)
            
            # Export button
            export_button = tk.Button(
                buttons_frame,
                text="📤 Export CSV",
                font=("Arial", 10, "bold"),
                bg='#2196F3',
                fg='white',
                command=lambda: self.export_users_data(users_details)
            )
            export_button.pack(side=tk.LEFT, padx=5)
            
            # Close button
            close_button = tk.Button(
                buttons_frame,
                text="❌ Close",
                font=("Arial", 10, "bold"),
                bg='#f44336',
                fg='white',
                command=details_window.destroy
            )
            close_button.pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show users details: {str(e)}")
    
    def refresh_users_tree(self, tree, status_label):
        """Refresh users tree with latest data"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
            
            # Get fresh data
            users_details = self.embedded_bot.get_users_details()
            
            # Populate tree
            for user in users_details:
                tree.insert('', tk.END, values=(
                    user['user_id'],
                    user['username'],
                    user['full_name'],
                    user['trading_mode'],
                    user['registration_date'][:10] if len(user['registration_date']) > 10 else user['registration_date'],
                    user['last_activity'][:10] if len(user['last_activity']) > 10 else user['last_activity']
                ))
            
            # Update status
            status_label.config(text=f"Total Users: {len(users_details)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")
    
    def export_users_data(self, users_details):
        """Export users data to CSV file"""
        try:
            import csv
            from tkinter import filedialog
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Users Data"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['User ID', 'Username', 'Full Name', 'Trading Mode', 'Registration Date', 'Last Activity']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for user in users_details:
                        writer.writerow({
                            'User ID': user['user_id'],
                            'Username': user['username'],
                            'Full Name': user['full_name'],
                            'Trading Mode': user['trading_mode'],
                            'Registration Date': user['registration_date'],
                            'Last Activity': user['last_activity']
                        })
                
                messagebox.showinfo("Success", f"Users data exported to: {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
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
            self.login_status_label.config(text="✅ Login successful!", fg='#00ff00')
            self.add_log("🔐 User authenticated successfully")
            self.root.after(1000, self.show_control)
        else:
            self.login_status_label.config(text="❌ Invalid password!", fg='#ff6666')
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def logout(self):
        """Logout user"""
        self.is_logged_in = False
        self.password_entry.delete(0, tk.END)
        self.login_status_label.config(text="")
        self.add_log("🚪 User logged out")
        self.show_login()
        
        # Close users count window if open
        if self.users_count_window and self.users_count_window.winfo_exists():
            self.users_count_window.destroy()
    
    def start_bot(self):
        """Start the embedded bot"""
        if not self.is_logged_in:
            messagebox.showerror("Access Denied", "Please login first!")
            return
        
        self.add_log("🚀 Starting embedded trading bot with JSON system...")
        success, message = self.embedded_bot.start_bot()
        
        if success:
            self.status_indicator.config(text="🟢 Running", fg='#00ff00')
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.add_log(f"✅ {message}")
            self.add_log("📁 Users will be saved in trading_data/users/")
        else:
            self.add_log(f"❌ {message}")
            messagebox.showerror("Error", message)
    
    def stop_bot(self):
        """Stop the embedded bot"""
        if not self.is_logged_in:
            messagebox.showerror("Access Denied", "Please login first!")
            return
        
        self.add_log("🛑 Stopping embedded trading bot...")
        success, message = self.embedded_bot.stop_bot()
        
        if success:
            self.status_indicator.config(text="⚫ Stopped", fg='#ff6666')
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.add_log(f"✅ {message}")
        else:
            self.add_log(f"❌ {message}")
            messagebox.showerror("Error", message)
    
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
                        text=f"👥 Users: {users_count}"
                    ))
                
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)
    
    def on_closing(self):
        """Handle window closing"""
        if self.embedded_bot.is_running:
            if messagebox.askokcancel("Quit", "Bot is still running. Stop bot and quit?"):
                self.embedded_bot.stop_bot()
                self.is_monitoring = False
                self.root.destroy()
        else:
            self.is_monitoring = False
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start main loop
        self.root.mainloop()

if __name__ == "__main__":
    # Create and run the UI with embedded bot
    try:
        app = TradingBotUI()
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Application terminated by user")
    except Exception as e:
        # Create a temporary root window for messagebox
        temp_root = tk.Tk()
        temp_root.withdraw()  # Hide the temporary window
        messagebox.showerror(
            "Application Error", 
            f"❌ Application error occurred:\n\n{str(e)}\n\nPlease check the error details and try again."
        )
        temp_root.destroy()