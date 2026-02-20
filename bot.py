import os
import re
import json
import logging
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import pytesseract
from PIL import Image
import io
import mimetypes

# Fix for imghdr missing in Python 3.14
import PIL.Image
import PIL.Imaging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Data store
group_data = {}

def load_data():
    global group_data
    try:
        with open('/tmp/data.json', 'r') as f:
            group_data = json.load(f)
    except:
        group_data = {}

def save_data():
    with open('/tmp/data.json', 'w') as f:
        json.dump(group_data, f)

load_data()

def photo_handler(update, context):
    try:
        group_id = str(update.effective_chat.id)
        user = update.effective_user
        
        logger.info(f"📸 Photo from {user.first_name}")
        
        # Download photo
        photo = update.message.photo[-1]
        file = context.bot.get_file(photo.file_id)
        img_bytes = file.download_as_bytearray()
        
        # OCR using PIL directly
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img)
        
        # Find 12-digit UTR
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
                update.message.reply_text(f"✅ UTR: {num}")
                logger.info(f"UTR found: {num}")
                return
                
    except Exception as e:
        logger.error(f"Error: {e}")

def stats_handler(update, context):
    group_id = str(update.effective_chat.id)
    count = len(group_data.get(group_id, []))
    update.message.reply_text(f"📊 Total UTRs: {count}")

def start_handler(update, context):
    update.message.reply_text(
        "🤖 UTR Bot Active!\n\n"
        "Send screenshot with 12-digit UTR\n"
        "/stats - Check total UTRs"
    )

def main():
    logger.info("🤖 Bot starting...")
    
    # Create updater
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(MessageHandler(Filters.photo, photo_handler))
    dp.add_handler(CommandHandler("stats", stats_handler))
    dp.add_handler(CommandHandler("start", start_handler))
    
    # Start
    updater.start_polling()
    logger.info("✅ Bot is running!")
    updater.idle()

if __name__ == "__main__":
    main()
