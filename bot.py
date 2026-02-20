import os
import re
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import io

BOT_TOKEN = os.environ.get('8527068092:AAFz5nKNegs1RHUHITTzBCUA9RTqaj3zAq8')

# Har group ka alag data store hoga
group_data = {}  # {group_id: {"utrs": [], "users": {}}}

# Session save/load
def save_data():
    with open('group_data.json', 'w') as f:
        json.dump(group_data, f)

def load_data():
    global group_data
    try:
        with open('group_data.json', 'r') as f:
            group_data = json.load(f)
    except:
        group_data = {}

load_data()

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kis group se aaya?
    group_id = str(update.effective_chat.id)
    group_name = update.effective_chat.title
    
    # User kaun hai?
    user = update.effective_user
    user_id = str(user.id)
    user_name = user.first_name
    
    # Photo download
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()
    
    # OCR
    img = Image.open(io.BytesIO(img_bytes))
    text = pytesseract.image_to_string(img)
    
    # UTR find
    numbers = re.findall(r'\d+', text)
    for num in numbers:
        if len(num) == 12:
            utr = num
            
            # Group ka data initialize
            if group_id not in group_data:
                group_data[group_id] = {
                    "name": group_name,
                    "utrs": [],
                    "users": {}
                }
            
            # User ka data initialize
            if user_id not in group_data[group_id]["users"]:
                group_data[group_id]["users"][user_id] = {
                    "name": user_name,
                    "username": user.username,
                    "utrs": []
                }
            
            # UTR save karo
            group_data[group_id]["utrs"].append({
                "utr": utr,
                "user": user_id,
                "time": str(update.message.date)
            })
            
            group_data[group_id]["users"][user_id]["utrs"].append(utr)
            
            # Save to file
            save_data()
            
            # Group me reply
            await update.message.reply_text(
                f"✅ **UTR DETECTED**\n\n"
                f"🔢 `{utr}`\n"
                f"👤 {user_name}\n"
                f"📊 Total in this group: {len(group_data[group_id]['utrs'])}"
            )
            return

# Command handlers
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    
    if group_id in group_data:
        data = group_data[group_id]
        total_utrs = len(data['utrs'])
        total_users = len(data['users'])
        
        await update.message.reply_text(
            f"📊 **Group Stats**\n\n"
            f"👥 Users: {total_users}\n"
            f"🔢 Total UTRs: {total_utrs}"
        )
    else:
        await update.message.reply_text("No UTRs found yet")

async def my_utrs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)
    
    if group_id in group_data and user_id in group_data[group_id]["users"]:
        utrs = group_data[group_id]["users"][user_id]["utrs"]
        count = len(utrs)
        
        msg = f"📋 **Your UTRs**: {count}\n\n"
        for utr in utrs[-5:]:  # Last 5
            msg += f"🔹 `{utr}`\n"
        
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("No UTRs found")

# Bot setup
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(MessageHandler(filters.Regex('^/stats$'), stats_handler))
app.add_handler(MessageHandler(filters.Regex('^/myutrs$'), my_utrs_handler))

print("🤖 Bot running...")
app.run_polling()
