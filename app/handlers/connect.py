from aiogram import Router, F
from aiogram.types import Message
from ..keyboards.connect_menu import connect_menu_keyboard
from app.services.marzban_api import marzban_client

router = Router()

@router.message(F.text == "❤️ Подключится")
async def handle_help(message: Message):
    await message.delete()

    url_android = "https://telegra.ph/Podklyuchenie-hiddify-na-Android-11-01"
    url_ios = "https://telegra.ph/Podklyuchenie-hiddify-na-IOS-11-01"
    url_win = "https://telegra.ph/Podklyuchenie-hiddify-na-Windows-11-01"

    telegram_user_id = message.from_user.id
    marzban_username = f"tg{telegram_user_id}"
    
    user_info = await marzban_client.get_user_info(marzban_username)
    
    subscription_link = None
    if user_info:
        subscription_link = user_info.get("subscription_url") or user_info.get("link")

    if subscription_link:
        link_display = f"<code>{subscription_link}</code>"
        link_instructions = "Ссылка для ручного подключения\nТапните чтобы скопировать в буфер обмена ↓\n\n"
    else:
        link_display = "У вас нет активной подписки или она еще не сгенерирована."
        link_instructions = "❗️ Пожалуйста, сначала приобретите подписку в меню 💳 Купить.\n"
        
    
    text = (
        "Доступ к VPN в 2 шага:\n\n" 
        "1️⃣ Скачать - для скачивания приложения\n"
        "2️⃣ Подключить - для добавления подписки\n\n"
        "Настроить VPN вручную:\n"
        f"- <a href='{url_android}'>Инструкция для Android 🤖</a>\n"
        f"- <a href='{url_ios}'>Инструкция для iOS/MacOS 🍏</a>\n"
        f"- <a href='{url_win}'>Инструкция для Windows 🖥</a>\n\n"
        f"{link_instructions}"
        f"{link_display}"
    )
    
    await message.answer(
        text,
        reply_markup=connect_menu_keyboard(),
        parse_mode="HTML"
    )