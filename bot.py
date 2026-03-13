import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive
import asyncio
import nest_asyncio

# ==== إصلاح مشكلة event loop على Railway ====
nest_asyncio.apply()

# ==== إعدادات ====
TOKEN = "8328657209:AAGGdgjcX0-FIN4GtBjw9cW62YCQmtpGw2M"  # توكن البوت
DATA_FILE = "data.json"          # ملف البيانات
DEFAULT_DAILY_LIMIT = 5          # العدد الافتراضي للمنشورات يومياً

# ==== تحميل وحفظ البيانات ====
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ==== /start ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 أهلاً بك في بوت النشر التلقائي!\n\n"
        "📋 الأوامر المتاحة:\n\n"
        "1️⃣ /setchannel @channel — ربط قناتك\n"
        "2️⃣ /setschedule N — تحديد عدد المنشورات يومياً\n"
        "3️⃣ /queue — عرض حالة قائمة الانتظار\n"
        "4️⃣ /clearqueue — مسح قائمة الانتظار\n\n"
        "📌 بعد الإعداد، أرسل لي النصوص أو الصور أو الفيديوهات أو الصوتيات وسأخزنها وأنشرها تلقائياً!"
    )

# ==== /setchannel ====
async def setchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) == 0:
        await update.message.reply_text("اكتب اسم القناة هكذا:\n/setchannel @channel")
        return
    channel = context.args[0]
    if user_id not in data:
        data[user_id] = {"channel": channel, "queue": [], "posts": [], "daily_count": 0, "last_post_date": "", "daily_limit": DEFAULT_DAILY_LIMIT}
    else:
        data[user_id]["channel"] = channel
    save_data(data)
    await update.message.reply_text(f"✅ تم ربط القناة {channel} بنجاح!")

# ==== /setschedule ====
async def setschedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) == 0 or not context.args[0].isdigit():
        await update.message.reply_text("اكتب العدد بشكل صحيح: /setschedule 3")
        return
    daily_limit = int(context.args[0])
    if user_id not in data:
        data[user_id] = {"channel": "", "queue": [], "posts": [], "daily_count": 0, "last_post_date": "", "daily_limit": daily_limit}
    else:
        data[user_id]["daily_limit"] = daily_limit
    save_data(data)
    await update.message.reply_text(f"✅ تم تحديد {daily_limit} منشورات يومياً لك.")

# ==== /queue ====
async def show_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in data or not data[user_id].get("queue"):
        await update.message.reply_text("✅ قائمة الانتظار فارغة.")
        return
    queue = data[user_id]["queue"]
    text = "\n".join([f"{i+1}. {item['type']}" for i, item in enumerate(queue)])
    await update.message.reply_text(f"📋 قائمة الانتظار:\n{text}")

# ==== /clearqueue ====
async def clear_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in data:
        data[user_id]["queue"] = []
        save_data(data)
    await update.message.reply_text("✅ تم مسح قائمة الانتظار.")

# ==== إضافة منشور إلى قائمة الانتظار ====
async def add_to_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in data or "channel" not in data[user_id] or not data[user_id]["channel"]:
        await update.message.reply_text("قم بربط قناتك أولاً: /setchannel @channel")
        return

    post = None
    post_type = None

    if update.message.text:
        post = update.message.text
        post_type = "text"
    elif update.message.photo:
        post = update.message.photo[-1].file_id
        post_type = "photo"
    elif update.message.video:
        post = update.message.video.file_id
        post_type = "video"
    elif update.message.voice:
        post = update.message.voice.file_id
        post_type = "voice"
    else:
        await update.message.reply_text("❌ نوع محتوى غير مدعوم.")
        return

    if any(item["content"] == post for item in data[user_id]["queue"]):
        await update.message.reply_text("❌ هذا المحتوى موجود بالفعل في قائمة الانتظار.")
        return

    data[user_id]["queue"].append({"type": post_type, "content": post})
    save_data(data)
    await update.message.reply_text("✅ تم إضافة المنشور إلى قائمة الانتظار.")

# ==== دالة النشر التلقائي ====
async def scheduled_publisher():
    while True:
        for user_id, info in data.items():
            today = datetime.now().strftime("%Y-%m-%d")
            if info.get("last_post_date") != today:
                info["daily_count"] = 0
                info["last_post_date"] = today

            daily_limit = info.get("daily_limit", DEFAULT_DAILY_LIMIT)

            while info["queue"] and info["daily_count"] < daily_limit:
                post = info["queue"].pop(0)
                channel = info["channel"]
                try:
                    if post["type"] == "text":
                        await bot.send_message(channel, post["content"])
                    elif post["type"] == "photo":
                        await bot.send_photo(channel, post["content"])
                    elif post["type"] == "video":
                        await bot.send_video(channel, post["content"])
                    elif post["type"] == "voice":
                        await bot.send_voice(channel, post["content"])
                    info["posts"].append(post["content"])
                    info["daily_count"] += 1
                    save_data(data)
                except Exception as e:
                    print(f"Error sending post for {user_id}: {e}")
        await asyncio.sleep(60)

# ==== بناء التطبيق ====
app = ApplicationBuilder().token(TOKEN).build()
bot = app.bot

# ==== إضافة المعالجات ====
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setchannel", setchannel))
app.add_handler(CommandHandler("setschedule", setschedule))
app.add_handler(CommandHandler("queue", show_queue))
app.add_handler(CommandHandler("clearqueue", clear_queue))
app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO | filters.VOICE, add_to_queue))

# ==== تشغيل keep_alive ====
keep_alive()

# ==== تشغيل البوت + جدولة النشر ====
async def main():
    asyncio.create_task(scheduled_publisher())
    await app.run_polling()

# التشغيل النهائي بدون مشاكل event loop
asyncio.get_event_loop().run_until_complete(main())
