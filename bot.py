import os
import re
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import io

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

group_data = {}

def load_data():
    global group_data
    try:
        with open('data.json', 'r') as f:
            group_data = json.load(f)
    except:
        group_data = {}

def save_data():
    with open('data.json', 'w') as f:
        json.dump(group_data, f)

load_data()

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    
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

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    count = len(group_data.get(group_id, []))
    await update.message.reply_text(f"📊 Total UTRs: {count}")

# App setup
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(MessageHandler(filters.Regex('^/stats$'), stats_handler))

if __name__ == "__main__":
    app.run_polling()
