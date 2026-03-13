from flask import Flask
from threading import Thread

# إنشاء تطبيق Flask صغير
app = Flask('')

# صفحة رئيسية بسيطة
@app.route('/')
def home():
    return "Bot is running ✅"

# دالة لتشغيل السيرفر
def run():
    app.run(host='0.0.0.0', port=8000)

# دالة لتشغيل السيرفر في ثريد منفصل
def keep_alive():
    t = Thread(target=run)
    t.start()
