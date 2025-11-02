from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery, Message
from app.keyboards.main_menu import main_menu_keyboard
from app.db.models import User, Subscription 
from app.db.database import get_db_session
from app.services.marzban_api import marzban_client
from .handlers.help import router as help_router
from .handlers.buy import router as buy_router
from .handlers.connect import router as connect_router
from .handlers.status import router as status_router
from datetime import datetime, timedelta
from sqlalchemy import select
from .keyboards.pay_menu import TARIFS, TRIAL_TARIFF, TRIAL_TARIFF_CODE

router = Router()
inputs = {}

router.include_router(help_router)
router.include_router(buy_router)
router.include_router(connect_router)
router.include_router(status_router)

@router.message(Command("start"))
async def start_cmd(message: Message):
    user_id = message.from_user.id
    TRIAL_CODE = TRIAL_TARIFF_CODE

    async with await get_db_session() as session:
        user_in_db = await session.get(User, user_id)
        if not user_in_db:
            new_user = User(
                id=user_id, 
                username=message.from_user.username,
                registration_date=datetime.utcnow()
            )
            session.add(new_user)

        trial_check_result = await session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.tariff_code == TRIAL_CODE
            )
        )
        trial_subscription_exists = trial_check_result.scalars().first()

        
        if trial_subscription_exists:
            start_message = ("👋 Приветствую!\n\n"
                             "Вы уже использовали бесплатный тестовый доступ (3 дня / 5 GB).\n"
                             "Для начала работы нажмите Подключиться ↓" 
                            )
            
        else:
            link = await _issue_trial_subscription(user_id, session, TRIAL_TARIFF)
            
            if link:
                start_message = (f"🎉 Добро пожаловать, {message.from_user.full_name}!\n\n"
                                 f"Мы активировали для вас **бесплатный тестовый доступ** на 3 дня и 5 GB.\n\n"
                                 f"🔑 Ваша ссылка:\n`{link}`\n\n"
                                 f"Для начала работы нажмите Подключиться ↓" 
                                )
            else:
                start_message = ("⚠️ Ошибка при создании тестового ключа.\n\n"
                                 "Попробуйте позже или свяжитесь с поддержкой: @truelinkmanager \n\n"
                                 "Для начала работы нажмите Подключиться ↓" 
                                )
                
        await session.commit()
    
    await message.answer(
        text=start_message,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

async def _issue_trial_subscription(user_id: int, session, tariff_data: dict) -> str | None:
    tariff_code = TRIAL_TARIFF_CODE 

    days_duration = tariff_data.get("days") 
    limit_gb = tariff_data.get("limit_gb")

    if days_duration == 0 or limit_gb is None:
        print(f"❌ Ошибка конфигурации тарифа '{tariff_code}': не удалось определить срок или лимит трафика.")
        return None
    
    try:
        link = await marzban_client.create_user(
            telegram_user_id=user_id,
            tariff_code=tariff_code, 
            user_data={}
        )
    except Exception as e:
        print(f"Ошибка Marzban при выдаче пробного ключа: {e}")
        return None
    
    if link:
        new_sub = Subscription(
            tariff_code=tariff_code,
            expires_at=datetime.utcnow() + timedelta(days=days_duration),
            data_limit_gb=limit_gb, 
            status="active",
            created_at=datetime.utcnow(),
            user_id=user_id,
            invoice_id=None, 
            is_paid=True,
            vpn_link=link
        )
        session.add(new_sub)
        return link
    
    return None