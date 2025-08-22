#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 Quick Test Runner for Trading Bot UI v1.2.0
==============================================
Simple script to test the GUI application before building executable

Usage: python run_gui.py
"""

import sys
import os

def main():
    """Run the GUI application for testing"""
    try:
        print("🤖 تشغيل واجهة بوت التداول للاختبار...")
        print("=" * 40)
        
        # Check if bot_ui.py exists
        if not os.path.exists('bot_ui.py'):
            print("❌ ملف bot_ui.py غير موجود!")
            return False
        
        # Import and run the GUI
        from bot_ui import TradingBotUI
        
        print("✅ تم تحميل الواجهة بنجاح")
        print("🔐 كلمة مرور الواجهة: 041768454")
        print("🤖 كلمة مرور البوت: tra12345678")
        print("=" * 40)
        
        # Create and run the application
        app = TradingBotUI()
        app.run()
        
        return True
        
    except ImportError as e:
        print(f"❌ خطأ في استيراد المكتبات: {e}")
        print("💡 تأكد من تثبيت المكتبات المطلوبة:")
        print("   pip install telebot pandas numpy MetaTrader5 google-generativeai Pillow")
        return False
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل الواجهة: {e}")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 تم إنهاء التطبيق بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        sys.exit(1)