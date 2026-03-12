import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8328657209:AAGGdgjcX0-FIN4GtBjw9cW62YCQmtpGw2M"  # ضع التوكن هنا

DATA_FILE = "data.json"  # ملف لحفظ البيانات


# تحميل البيانات من ملف JSON
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


# حفظ البيانات إلى ملف JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# تحميل البيانات عند تشغيل البوت
data = load_data()


# استقبال الأمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "اهلا بك في بوت النشر التلقائي\n\n"
        "1- أضف البوت مشرف في قناتك\n"
        "2- اربط القناة:\n"
        "/setchannel @channel\n\n"
        "بعدها ارسل نص أو صورة أو فيديو أو صوت وسيتم نشره في قناتك."
    )


# ربط القناة مع البوت
async def setchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if len(context.args) == 0:
        await update.message.reply_text("اكتب اسم القناة هكذا:\n/setchannel @channel")
        return

    channel = context.args[0]

    if user_id not in data:
        data[user_id] = {"posts": []}

    data[user_id]["channel"] = channel

    save_data(data)

    await update.message.reply_text("تم ربط القناة بنجاح ✅")


# نشر المحتوى في القناة
async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id not in data or "channel" not in data[user_id]:
        await update.message.reply_text("قم بربط قناتك أولا:\n/setchannel @channel")
        return

    channel = data[user_id]["channel"]

    post_id = None

    # نشر النصوص
    if update.message.text:
        post_id = update.message.text

        if post_id in data[user_id]["posts"]:
            await update.message.reply_text("هذا المنشور تم نشره مسبقًا ❌")
            return

        await context.bot.send_message(channel, update.message.text)

    # نشر الصور
    elif update.message.photo:
        post_id = update.message.photo[-1].file_id

        if post_id in data[user_id]["posts"]:
            await update.message.reply_text("تم نشر هذه الصورة سابقًا ❌")
            return

        await context.bot.send_photo(
            channel,
            update.message.photo[-1].file_id,
            caption=update.message.caption
        )

    # نشر الفيديوهات
    elif update.message.video:
        post_id = update.message.video.file_id

        if post_id in data[user_id]["posts"]:
            await update.message.reply_text("تم نشر هذا الفيديو سابقًا ❌")
            return

        await context.bot.send_video(
            channel,
            update.message.video.file_id,
            caption=update.message.caption
        )

    # نشر الصوت
    elif update.message.voice:
        post_id = update.message.voice.file_id

        if post_id in data[user_id]["posts"]:
            await update.message.reply_text("تم نشر هذا الصوت سابقًا ❌")
            return

        await context.bot.send_voice(channel, update.message.voice.file_id)

    if post_id:
        data[user_id]["posts"].append(post_id)
        save_data(data)

        await update.message.reply_text("تم نشر المنشور في قناتك ✅")


# بناء البوت
app = ApplicationBuilder().token(TOKEN).build()

# إضافة المعالجات للأوامر المختلفة
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setchannel", setchannel))

# إضافة معالج لرسائل النصوص والصور والفيديو والصوت
app.add_handler(MessageHandler(
    filters.TEXT | filters.PHOTO | filters.VIDEO | filters.VOICE,
    publish
))

print("Bot started...")

# تشغيل البوت
app.run_polling()
