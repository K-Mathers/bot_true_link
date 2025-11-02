from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def connect_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🤖 Скачать Android", url="https://play.google.com/store/apps/details?id=app.hiddify.com&hl=en"),
            InlineKeyboardButton(text="🤖 Инструкция Android", url="https://telegra.ph/Podklyuchenie-hiddify-na-Android-11-01"),
        ],
        [
            InlineKeyboardButton(text="🍎 Скачать iOS/macOS", url="https://apps.apple.com/us/app/hiddify-proxy-vpn/id6596777532"),
            InlineKeyboardButton(text="🍎 Инструкция iOS/macOS", url="https://telegra.ph/Podklyuchenie-hiddify-na-IOS-11-01"),
        ],
        [
            InlineKeyboardButton(text="💻 Скачать Windows", url="https://github.com/hiddify/hiddify-next/releases/latest/download/Hiddify-Windows-Setup-x64.exe"),
            InlineKeyboardButton(text="💻 Инструкция Windows", url="https://telegra.ph/Podklyuchenie-hiddify-na-Windows-11-01"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)