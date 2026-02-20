import os
import sys
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check token
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable not set!")
    sys.exit(1)

logger.info("✅ BOT_TOKEN found")

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        await update.message.reply_text("✅ Photo received")
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(MessageHandler(filters.PHOTO, photo))
        
        logger.info("🤖 Bot starting...")
        app.run_polling()
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
