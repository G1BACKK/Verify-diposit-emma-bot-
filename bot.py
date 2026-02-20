import os
import re
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

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

def photo_handler(update: Update, context: CallbackContext):
    try:
        group_id = str(update.effective_chat.id)
        user = update.effective_user
        
        # Download photo
        photo = update.message.photo[-1]
        file = context.bot.get_file(photo.file_id)
        file.download('temp.jpg')
        
        # OCR - using PIL directly
        from PIL import Image
        import pytesseract
        
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        img = Image.open('temp.jpg')
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
                update.message.reply_text(f"✅ UTR: {num}")
                return
                
    except Exception as e:
        print(f"Error: {e}")

def stats_handler(update: Update, context: CallbackContext):
    group_id = str(update.effective_chat.id)
    count = len(group_data.get(group_id, []))
    update.message.reply_text(f"📊 Total UTRs: {count}")

def start_handler(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 UTR Bot Active!\nSend screenshot with 12-digit UTR")

# Main
def main():
    print("🤖 Bot starting...")
    
    # Create updater (old stable version)
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(MessageHandler(Filters.photo, photo_handler))
    dp.add_handler(CommandHandler("stats", stats_handler))
    dp.add_handler(CommandHandler("start", start_handler))
    
    # Start
    updater.start_polling()
    print("✅ Bot running!")
    updater.idle()

if __name__ == "__main__":
    main()
