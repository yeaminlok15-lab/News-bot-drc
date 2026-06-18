import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from src.config import BOT_TOKEN, CHANNEL_ID, ADMIN_ID, POSTING_INTERVAL
from src.database import init_db, add_source
from src.fetcher import fetch_new_articles

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Formatter ---
def format_message(article: dict) -> str:
    return (
        f"📰 *{article['title']}*\n\n"
        f"📄 {article['summary']}\n\n"
        f"🔗 [Read More]({article['url']})\n\n"
        f"🌐 Source: {article['source_name']}\n"
        f"⏰ Published: {article['published']}\n\n"
        f"{article['hashtags']} #BreakingNews"
    )

# --- Scheduler Job ---
async def fetch_and_post_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Running scheduled news fetch...")
    articles = await fetch_new_articles()
    
    for article in articles:
        msg_text = format_message(article)
        try:
            if article['image']:
                await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=article['image'],
                    caption=msg_text,
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=msg_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=False
                )
        except Exception as e:
            logger.error(f"Failed to post article: {e}")

# --- Admin Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 News Aggregator Bot is running.")

async def add_source_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("Unauthorized.")
    
    try:
        # Usage: /addsource "Name" "URL" "Category" "Language"
        args = context.args
        if len(args) < 4:
            return await update.message.reply_text("Usage: /addsource Name URL Category Language")
        
        success = await add_source(args[0], args[1], args[2], args[3])
        if success:
            await update.message.reply_text(f"✅ Added source: {args[0]}")
        else:
            await update.message.reply_text("❌ Source URL already exists.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def manual_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🔄 Manual fetch initiated...")
    await fetch_and_post_job(context)
    await update.message.reply_text("✅ Manual fetch completed.")

# --- Main App ---
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addsource", add_source_cmd))
    app.add_handler(CommandHandler("fetch", manual_fetch))

    # Init DB locally before starting (sync wrapper)
    import asyncio
    asyncio.get_event_loop().run_until_complete(init_db())

    # Start the job queue
    job_queue = app.job_queue
    job_queue.run_repeating(fetch_and_post_job, interval=POSTING_INTERVAL * 60, first=10)

    logger.info("Bot is polling...")
    app.run_polling()

if __name__ == '__main__':
    main()
