import os
import re
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Download
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        
        # Simple text check
        text = str(img_bytes)
        
        # Find 12-digit
        nums = re.findall(r'\d+', text)
        for num in nums:
            if len(num) == 12:
                await update.message.reply_text(f"✅ {num}")
                return
    except Exception as e:
        logger.error(e)

# App
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, photo))

if __name__ == "__main__":
    logger.info("Started")
    app.run_polling()
