from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "🆘 Помощь")
async def handle_help(message: Message):
    await message.delete()

    await message.answer("Если у вас проблемы с подключением, отправьте статус из бота и скриншот из приложения, которым вы пользуетесь для доступа к VPN в поддержку.\n\n"
                         "Свяжитесь с поддержкой - @truelinkmanager")