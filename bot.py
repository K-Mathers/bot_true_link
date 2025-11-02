import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from app.main_commands import router as commands_router
from app.services.marzban_api import marzban_client
from app.handlers.buy import check_crypto_payments
from app.db.database import init_db

dp = Dispatcher()
dp.include_router(commands_router)

async def main():
    await marzban_client.initialize()
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    print("🚀 Бот запущен...")

    asyncio.create_task(check_crypto_payments(bot))

    try:
        await dp.start_polling(bot)
    finally:
        await marzban_client.close() 
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        print("Bot stopped.")