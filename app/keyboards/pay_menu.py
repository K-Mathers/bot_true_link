from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
# from config import TRIAL_TARIFF_CODE # Если config.py будет использоваться

# --- ПЛАТНЫЕ ТАРИФЫ (Только для меню покупки) ---
PAID_TARIFS = {
    "1m": {"price_rub": 200, "limit_gb": 100, "price_usd": 3, "stars": 120, "title": "VPN на 1 месяц", "description": "Полный доступ к VPN - 1 месяц"},
    "3m": {"price_rub": 600, "limit_gb": 300, "price_usd": 8, "stars": 300, "title": "VPN на 3 месяца", "description": "Полный доступ к VPN - 3 месяца"},
    "6m": {"price_rub": 1200, "limit_gb": 600, "price_usd": 16, "stars": 700, "title": "VPN на 6 месяцев", "description": "Полный доступ к VPN - 6 месяцев"}
}

# --- ПРОБНЫЙ ТАРИФ (Используется только в логике /start) ---
TRIAL_TARIFF_CODE = 'free'
TRIAL_TARIFF = {
    "limit_gb": 5, 
    "days": 3, # Добавляем этот ключ для удобства расчета в timedelta
    "title": "VPN на 3 дня", 
    "description": "Полный доступ к VPN - 3 дня"
}

# --- ОБЩИЙ СЛОВАРЬ (Для buy.py и check_crypto_payments) ---
# Объединяем их, чтобы код в buy.py и check_crypto_payments мог получить доступ ко всем тарифам
TARIFS = PAID_TARIFS.copy()
TARIFS[TRIAL_TARIFF_CODE] = TRIAL_TARIFF


def get_tarfs_keyboard():
    buttons = [
        # 💡 Изменяем: используем PAID_TARIFS, чтобы исключить 'free'
        [InlineKeyboardButton(text=f"{data['title']}", callback_data=f"buy_{code}")]
        for code, data in PAID_TARIFS.items() 
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_keyboard(tariff_code: str):
    # Ваш код не меняется, так как он использует TARIFS, который теперь включает все.
    buttons = [
        [
            InlineKeyboardButton(text="Криптой 💎", callback_data=f"pay_crypto_{tariff_code}"),
            InlineKeyboardButton(text="Звёздами ⭐️", callback_data=f"pay_stars_{tariff_code}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)