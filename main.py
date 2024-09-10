import logging
import os
from shutil import copyfile
from datetime import datetime, timezone
from time import strftime, localtime
from subprocess import run
from tzlocal import get_localzone

from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, BusinessConnectionHandler

LOG_PATH = "data/logs"
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CONNECTION_ID = os.getenv("OWNER_CONNECTION_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    filename=f"{LOG_PATH}/log",
    filemode="a"
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def log_business_message(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if not update.business_message and not update.edited_business_message:
        return
    business_object = update.business_message or update.edited_business_message
    if business_object.business_connection_id != OWNER_CONNECTION_ID:
        return
    logger.warning(f"Received message: {update}")


async def log_business_connection(update: Update, _: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"Received business connection: {update.business_connection}")


def log_rotation() -> bool:
    result = False

    try:
        readable_time = get_readable_time(the_format='%Y%m%d')

        copyfile(f"{LOG_PATH}/log", f"{LOG_PATH}/log-{readable_time}")
        with open(f"{LOG_PATH}/log", "w", encoding="utf-8") as f:
            f.write("")

        run(f"find {LOG_PATH}/log-* -mtime +7 -delete", shell=True)  # nosec B602

        result = True
    except Exception as e:
        logger.warning(f"Log rotation error: {e}", exc_info=True)

    return result


def get_readable_time(secs: int = 0, the_format: str = "%Y%m%d%H%M%S") -> str:
    result = ""

    try:
        if secs:
            result = datetime.fromtimestamp(secs, timezone.utc).strftime(the_format)
        else:
            result = strftime(the_format, localtime())
    except Exception as e:
        logger.warning(f"Get readable time error: {e}", exc_info=True)

    return result


if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.UpdateType.BUSINESS_MESSAGES, log_business_message)
    business_connection_handler = BusinessConnectionHandler(log_business_connection)
    
    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(business_connection_handler)

    scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": 300}, timezone=str(get_localzone()))
    scheduler.add_job(log_rotation, "cron", hour=23, minute=59)
    scheduler.start()

    
    application.run_polling()
