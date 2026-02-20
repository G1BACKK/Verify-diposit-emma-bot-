import os
import re
import json
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import io

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

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
    try:
        group_id = str(update.effective_chat.id)
        user = update.effective_user
        
        logger.info(f"📸 Photo from {user.first_name}")
        
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
                    'user_id': user.id,
                    'time': str(update.message.date)
                })
                save_data()
                
                # Reply
                await update.message.reply_text(f"✅ UTR: {num}")
                logger.info(f"✅ UTR found: {num}")
                return
                
    except Exception as e:
        logger.error(f"Error: {e}")

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    count = len(group_data.get(group_id, []))
    await update.message.reply_text(f"📊 Total UTRs: {count}")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 UTR Bot Active!\n\n"
        "Send screenshot with 12-digit UTR\n"
        "/stats - Check total UTRs"
    )

def main():
    """Main function"""
    logger.info("🤖 Bot starting...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.Regex('^/stats$'), stats_handler))
    app.add_handler(MessageHandler(filters.Regex('^/start$'), start_handler))
    
    # Start bot
    logger.info("✅ Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
