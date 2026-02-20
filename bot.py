import os
import re
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import io

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Data store
group_data = {}

# Load data
def load_data():
    global group_data
    try:
        with open('data.json', 'r') as f:
            group_data = json.load(f)
    except:
        group_data = {}

# Save data
def save_data():
    with open('data.json', 'w') as f:
        json.dump(group_data, f)

load_data()

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    user = update.effective_user
    
    # Download photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()
    
    # OCR
    img = Image.open(io.BytesIO(img_bytes))
    text = pytesseract.image_to_string(img)
    
    # Find UTR
    numbers = re.findall(r'\d+', text)
    for num in numbers:
        if len(num) == 12:
            # Save
            if group_id not in group_data:
                group_data[group_id] = []
            
            group_data[group_id].append({
                'utr': num,
                'user': user.first_name,
                'time': str(update.message.date)
            })
            save_data()
            
            # Reply
            await update.message.reply_text(f"✅ UTR: {num}")
            return

# Setup
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

if __name__ == "__main__":
    app.run_polling()
