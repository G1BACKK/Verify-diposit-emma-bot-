import os
import re
import json
import sys
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import io

# Fix for Python 3.14
if not hasattr(pytesseract, 'pytesseract'):
    from pytesseract import pytesseract as pytesseract_core
else:
    pytesseract_core = pytesseract.pytesseract

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Set tesseract path
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

group_data = {}

def load_data():
    global group_data
    try:
        with open('/opt/render/project/src/data.json', 'r') as f:
            group_data = json.load(f)
    except:
        group_data = {}

def save_data():
    with open('/opt/render/project/src/data.json', 'w') as f:
        json.dump(group_data, f)

load_data()

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img)
        
        nums = re.findall(r'\d+', text)
        for num in nums:
            if len(num) == 12:
                if group_id not in group_data:
                    group_data[group_id] = []
                
                group_data[group_id].append({
                    'utr': num,
                    'user': update.effective_user.first_name,
                    'time': str(update.message.date)
                })
                save_data()
                
                await update.message.reply_text(f"✅ UTR: {num}")
                return
    except Exception as e:
        print(f"Error: {e}")

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    count = len(group_data.get(group_id, []))
    await update.message.reply_text(f"📊 Total UTRs: {count}")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 UTR Bot Active!\n\n"
        "Send screenshot with 12-digit UTR\n"
        "Commands:\n"
        "/stats - Total UTRs in group"
    )

# App setup
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(MessageHandler(filters.Regex('^/stats$'), stats_handler))
app.add_handler(MessageHandler(filters.Regex('^/start$'), start_handler))

if __name__ == "__main__":
    print("🤖 Bot starting...")
    app.run_polling()
