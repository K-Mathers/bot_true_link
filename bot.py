import asyncio
import logging
import os 
from aiogram import Bot, Dispatcher
from aiohttp import web 
from config import BOT_TOKEN
from app.main_commands import router as commands_router
from app.services.marzban_api import marzban_client
from app.handlers.buy import check_crypto_payments
from app.db.database import init_db 
logging.basicConfig(level=logging.INFO)

dp = Dispatcher()
dp.include_router(commands_router)

async def health_check(request):
    return web.Response(text="Bot is running via Long Polling.", status=200)

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/health', health_check)]) 
    port = int(os.environ.get("PORT", 8080)) 
    host = '0.0.0.0'

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    
    logging.info(f"🌐 Web Server запущен на {host}:{port} для Health Check.")
    await site.start()

    try:
        await asyncio.Event().wait()
    finally:
        logging.info("🌐 Web Server получил сигнал остановки. Закрытие runner.")
        await runner.cleanup() 

async def shutdown(bot: Bot):
    logging.info("🛑 Начинается корректное закрытие ресурсов...")
    try:
        await marzban_client.close() 
        await bot.session.close()
    except Exception as e:
        logging.error(f"Ошибка при закрытии сессий: {e}")
    logging.info("Все ресурсы закрыты.")


async def run_bot_tasks(bot: Bot):
    """Выполняет всю инициализацию и запускает Long Polling."""
    logging.info("⏳ Запуск инициализации сервисов (Marzban, DB)...")
    
    try:
        await marzban_client.initialize()
        await init_db() 
        logging.info("✅ Инициализация Marzban и БД завершена.")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка инициализации: {e}. Проверьте ENV VARIABLES!")
        return
    
    asyncio.create_task(check_crypto_payments(bot)) 
    logging.info("✅ Фоновая задача проверки платежей запущена.")
    logging.info("🚀 Бот запускает Long Polling...")
    await dp.start_polling(bot)


async def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не установлен. Завершение.")
        return

    bot = Bot(token=BOT_TOKEN)
    web_server_task = asyncio.create_task(start_web_server())
    polling_task = asyncio.create_task(run_bot_tasks(bot))
    
    try:
        await asyncio.gather(web_server_task, polling_task)
    except asyncio.CancelledError:
        pass 
    finally:
        await shutdown(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by KeyboardInterrupt (Local).")
    except Exception as e:
        logging.error(f"Непредвиденная ошибка при выполнении main: {e}")
