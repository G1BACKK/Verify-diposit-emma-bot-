import os
import re
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import io

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('8527068092:AAFz5nKNegs1RHUHITTzBCUA9RTqaj3zAq8')

# Data store
group_data = {}

# Load data
def load_data():
    global group_data
    try:
        if os.path.exists('group_data.json'):
            with open('group_data.json', 'r') as f:
                group_data = json.load(f)
    except:
        group_data = {}

# Save data
def save_data():
    try:
        with open('group_data.json', 'w') as f:
            json.dump(group_data, f)
    except:
        pass

load_data()

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Group info
        group_id = str(update.effective_chat.id)
        group_name = update.effective_chat.title
        
        # User info
        user = update.effective_user
        user_id = str(user.id)
        user_name = user.first_name or "User"
        
        logger.info(f"📸 Photo in {group_name}")
        
        # Download photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        
        # OCR
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img)
        
        # Find 12-digit UTR
        numbers = re.findall(r'\d+', text)
        for num in numbers:
            if len(num) == 12:
                utr = num
                
                # Initialize group
                if group_id not in group_data:
                    group_data[group_id] = {
                        "name": group_name,
                        "utrs": [],
                        "users": {}
                    }
                
                # Initialize user
                if user_id not in group_data[group_id]["users"]:
                    group_data[group_id]["users"][user_id] = {
                        "name": user_name,
                        "username": user.username,
                        "utrs": []
                    }
                
                # Save UTR
                group_data[group_id]["utrs"].append({
                    "utr": utr,
                    "user": user_id,
                    "time": str(datetime.now())
                })
                group_data[group_id]["users"][user_id]["utrs"].append(utr)
                
                # Save to file
                save_data()
                
                # Reply
                await update.message.reply_text(f"✅ UTR: `{utr}`")
                logger.info(f"✅ UTR: {utr}")
                return
                
    except Exception as e:
        logger.error(f"Error: {e}")

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    if group_id in group_data:
        total = len(group_data[group_id]['utrs'])
        await update.message.reply_text(f"📊 Total UTRs: {total}")
    else:
        await update.message.reply_text("0 UTRs")

# Setup
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(MessageHandler(filters.Regex('^/stats$'), stats_handler))

if __name__ == "__main__":
    logger.info("🤖 Bot started")
    app.run_polling()
