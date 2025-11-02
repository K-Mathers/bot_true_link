import time
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from app.services.marzban_api import marzban_client

router = Router()

def format_bytes(bytes_value: int, suffix: str = "B") -> str:
    """Конвертирует байты в более читаемый формат (KB, MB, GB, TB)."""
    if bytes_value == 0:
        return "0 Bytes"
    for unit in ['', 'K', 'M', 'G', 'T']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}{suffix}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} P{suffix}"


@router.message(F.text == "ℹ️ Cтатус")
async def handle_status(message: Message):
    await message.delete()
    
    telegram_user_id = message.from_user.id
    marzban_username = f"tg{telegram_user_id}"
    user_info = await marzban_client.get_user_info(marzban_username)

    if not user_info:
        await message.answer(
            "ℹ️ **Ваш статус:**\n\n"
            "❌ Подписка не найдена. Похоже, вы еще не приобретали VPN-ключ.\n\n"
            "Нажмите кнопку 'Купить', чтобы выбрать тариф.",
            parse_mode="Markdown"
        )
        return
    
    subscription_link = user_info.get("subscription_url") or user_info.get("link")

    expire_timestamp = user_info.get('expire', 0)
    current_time_s = int(time.time())
    
    if expire_timestamp > current_time_s:
        expire_date = datetime.fromtimestamp(expire_timestamp)
        time_left: timedelta = expire_date - datetime.now()
        
        days_left = time_left.days
        hours_left = time_left.seconds // 3600
        minutes_left = (time_left.seconds % 3600) // 60
        
        status_line = "✅ АКТИВНА"
        time_left_str = f"{days_left} дн., {hours_left} ч., {minutes_left} мин."
        expire_date_str = expire_date.strftime("%d.%m.%Y %H:%M")
        
    else:
        status_line = "❌ **ИСТЕКЛА**"
        time_left_str = "0 дн."
        expire_date_str = "—"
        
    data_usage = user_info.get('data_usage', 0)
    data_limit = user_info.get('data_limit', 0)
    
    used_traffic = format_bytes(data_usage)
    total_limit = format_bytes(data_limit)
    
    if data_limit > 0:
        percent_used = (data_usage / data_limit) * 100
        traffic_line = f"├ Трафик: {used_traffic} из {total_limit} ({percent_used:.1f}%)"
    else:
        traffic_line = f"├ Трафик: Неограничен"

    message_text = (
        f"ℹ️ Ваш статус подписки\n\n"
        f"Доступ: {status_line}\n"
        f"├ Осталось дней: {time_left_str}\n"
        f"├ Активна до: {expire_date_str}\n"
        f"{traffic_line}\n"
        f"└ Статус сервера: `{user_info.get('status', 'Неизвестен')}`\n\n"
    )

    if subscription_link:
        message_text += (
            f"🔑 Ваша ссылка для подключения:\n\n"
            f"<code>{subscription_link}</code>\n\n"
            "Нажмите, чтобы добавить ключ в клиент (Hiddify, V2RayNG, v2Box и т.д.)"
        )
    else:
        message_text += "🔗 Ссылка для подписки пока не найдена. Попробуйте позже."

    await message.answer(message_text, parse_mode="HTML")
