#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إنشاء أيقونة بسيطة لبوت التداول
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_trading_bot_icon():
    """إنشاء أيقونة بوت التداول"""
    # إنشاء صورة 256x256 بخلفية زرقاء
    size = 256
    img = Image.new('RGBA', (size, size), (33, 150, 243, 255))  # أزرق
    draw = ImageDraw.Draw(img)
    
    # رسم دائرة خارجية
    margin = 20
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=(25, 118, 210, 255), outline=(13, 71, 161, 255), width=4)
    
    # رسم رمز البوت (🤖) كنص
    try:
        # محاولة استخدام خط كبير
        font_size = 120
        font = ImageFont.load_default()
        
        # رسم رمز البوت
        text = "🤖"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - 20
        
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
    except:
        # إذا فشل الخط، ارسم شكل بسيط
        # رسم مربع للرأس
        head_size = 60
        head_x = (size - head_size) // 2
        head_y = size // 2 - 40
        draw.rectangle([head_x, head_y, head_x + head_size, head_y + head_size], 
                      fill=(255, 255, 255, 255), outline=(200, 200, 200, 255), width=2)
        
        # رسم العيون
        eye_size = 8
        eye1_x = head_x + 15
        eye2_x = head_x + head_size - 15 - eye_size
        eye_y = head_y + 20
        draw.ellipse([eye1_x, eye_y, eye1_x + eye_size, eye_y + eye_size], 
                    fill=(33, 150, 243, 255))
        draw.ellipse([eye2_x, eye_y, eye2_x + eye_size, eye_y + eye_size], 
                    fill=(33, 150, 243, 255))
        
        # رسم الفم
        mouth_y = head_y + 40
        draw.rectangle([head_x + 20, mouth_y, head_x + head_size - 20, mouth_y + 4], 
                      fill=(33, 150, 243, 255))
    
    # حفظ الأيقونة
    img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print("✅ تم إنشاء ملف icon.ico بنجاح")

if __name__ == "__main__":
    create_trading_bot_icon()