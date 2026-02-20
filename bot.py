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

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Group data store
group_data = {}

# Load existing data
def load_data():
    global group_data
    try:
        if os.path.exists('group_data.json'):
            with open('group_data.json', 'r') as f:
                group_data = json.load(f)
            logger.info(f"Loaded data for {len(group_data)} groups")
    except Exception as e:
        logger.error(f"Load error: {e}")

# Save data
def save_data():
    try:
        with open('group_data.json', 'w') as f:
            json.dump(group_data, f)
    except Exception as e:
        logger.error(f"Save error: {e}")

load_data()

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Group info
        group_id = str(update.effective_chat.id)
        group_name = update.effective_chat.title
        
        # User info
        user = update.effective_user
        user_id = str(user.id)
        user_name = user.first_name
        
        logger.info(f"📸 Photo from {user_name} in {group_name}")
        
        # Download photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        
        # OCR
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img)
        
        logger.info(f"OCR text: {text[:100]}...")
        
        # Find 12-digit UTR
        numbers = re.findall(r'\d+', text)
        for num in numbers:
            if len(num) == 12:
                utr = num
                
                # Initialize group data
                if group_id not in group_data:
                    group_data[group_id] = {
                        "name": group_name,
                        "utrs": [],
                        "users": {}
                    }
                
                # Initialize user data
                if user_id not in group_data[group_id]["users"]:
                    group_data[group_id]["users"][user_id] = {
                        "name": user_name,
                        "username": user.username,
                        "utrs": []
                    }
                
                # Save UTR
                utr_data = {
                    "utr": utr,
                    "user": user_id,
                    "time": datetime.now().isoformat()
                }
                
                group_data[group_id]["utrs"].append(utr_data)
                group_data[group_id]["users"][user_id]["utrs"].append(utr)
                
                # Save to file
                save_data()
                
                # Reply in group
                await update.message.reply_text(
                    f"✅ **UTR DETECTED**\n\n"
                    f"🔢 `{utr}`\n"
                    f"👤 {user_name}\n"
                    f"📊 Total: {len(group_data[group_id]['utrs'])}"
                )
                
                logger.info(f"✅ UTR found: {utr}")
                return
                
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error processing image")

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    
    if group_id in group_data:
        data = group_data[group_id]
        total_utrs = len(data['utrs'])
        total_users = len(data['users'])
        
        await update.message.reply_text(
            f"📊 **Group Stats**\n\n"
            f"👥 Users: {total_users}\n"
            f"🔢 UTRs: {total_utrs}"
        )
    else:
        await update.message.reply_text("No UTRs yet")

async def my_utrs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)
    
    if group_id in group_data and user_id in group_data[group_id]["users"]:
        utrs = group_data[group_id]["users"][user_id]["utrs"]
        count = len(utrs)
        
        msg = f"📋 **Your UTRs**: {count}\n\n"
        for utr in utrs[-5:]:
            msg += f"🔹 `{utr}`\n"
        
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("No UTRs found")

# Setup bot
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(MessageHandler(filters.Regex('^/stats$'), stats_handler))
app.add_handler(MessageHandler(filters.Regex('^/myutrs$'), my_utrs_handler))

if __name__ == "__main__":
    logger.info("🤖 Bot started!")
    app.run_polling()
