from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="ℹ️ Cтатус"),
        KeyboardButton(text="❤️ Подключится")
    )
    
    builder.row(
        KeyboardButton(text="💳 Купить"),
        KeyboardButton(text="🆘 Помощь")
    )

    return builder.as_markup(resize_keyboard = True)