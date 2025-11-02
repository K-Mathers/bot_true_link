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

async def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не установлен. Завершение.")
        return
    
    await marzban_client.initialize()
    await init_db() 

    bot = Bot(token=BOT_TOKEN)
    logging.info("🚀 Бот запущен...")
    asyncio.create_task(check_crypto_payments(bot)) 
    logging.info("✅ Фоновая задача проверки платежей запущена.")
    polling_task = asyncio.create_task(dp.start_polling(bot))
    await start_web_server()
    await polling_task 

async def shutdown(bot, marzban_client):
    logging.info("🛑 Получен сигнал завершения. Закрытие ресурсов...")
    try:
        await marzban_client.close() 
    except Exception as e:
        logging.error(f"Ошибка при закрытии Marzban клиента: {e}")
        
    try:
        await bot.session.close()
    except Exception as e:
        logging.error(f"Ошибка при закрытии сессии бота: {e}")
    logging.info("Все ресурсы закрыты.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by KeyboardInterrupt (Local).")
    except Exception as e:
        logging.error(f"Непредвиденная ошибка при выполнении main: {e}")
