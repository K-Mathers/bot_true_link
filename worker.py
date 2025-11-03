import asyncio
import logging
from aiogram import Bot
from config import BOT_TOKEN 
from app.handlers.buy import check_crypto_payments
from app.db.database import init_db
from app.services.marzban_api import marzban_client

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - WORKER - %(levelname)s - %(message)s')

async def worker_main():
    logging.info("⏳ Запуск Marzban Worker...")
    
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не установлен в Worker. Завершение.")
        return

    try:
        await marzban_client.initialize()
        await init_db()
    except Exception as e:
        logging.error(f"❌ Критическая ошибка инициализации Worker (Marzban/DB): {e}")
        return

    bot = Bot(token=BOT_TOKEN)
    
    try:
        logging.info("✅ Worker: Запуск бесконечного цикла проверки платежей.")
        await check_crypto_payments(bot)
    except asyncio.CancelledError:
        logging.info("🛑 Worker: Задача проверки платежей отменена (SIGTERM).")
    except Exception as e:
        logging.error(f"❌ Worker: Непредвиденная ошибка в основном цикле: {e}")
    finally:
        logging.info("🛑 Worker: Закрытие ресурсов...")
        try:
            await marzban_client.close() 
            await bot.session.close()
        except Exception as e:
            logging.error(f"Worker: Ошибка при закрытии сессий: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(worker_main())
    except KeyboardInterrupt:
        logging.info("Worker stopped by KeyboardInterrupt (Local).")
    except Exception as e:
        logging.error(f"Критическая ошибка при выполнении worker_main: {e}")
