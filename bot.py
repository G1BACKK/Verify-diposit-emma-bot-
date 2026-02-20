import os
import re
import json
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import pytesseract
from PIL import Image
import io

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Data store
data = {}

def load():
    global data
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except:
        data = {}

def save():
    with open('data.json', 'w') as f:
        json.dump(data, f)

load()

def photo(update, context):
    try:
        chat = str(update.effective_chat.id)
        
        # Download
        photo = update.message.photo[-1]
        file = context.bot.get_file(photo.file_id)
        img_bytes = file.download_as_bytearray()
        
        # OCR
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img)
        
        # Find 12-digit
        nums = re.findall(r'\d+', text)
        for num in nums:
            if len(num) == 12:
                if chat not in data:
                    data[chat] = []
                data[chat].append(num)
                save()
                update.message.reply_text(f"✅ {num}")
                return
    except Exception as e:
        logger.error(e)

def stats(update, context):
    chat = str(update.effective_chat.id)
    c = len(data.get(chat, []))
    update.message.reply_text(f"📊 {c}")

def start(update, context):
    update.message.reply_text("Send screenshot")

# Main
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(MessageHandler(Filters.photo, photo))
dp.add_handler(CommandHandler("stats", stats))
dp.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    logger.info("Running...")
    updater.start_polling()
    updater.idle()
