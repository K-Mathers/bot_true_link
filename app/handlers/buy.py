from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, SuccessfulPayment, ContentType
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.database import get_db_session 
from app.db.models import User, Subscription 
from app.keyboards.pay_menu import get_tarfs_keyboard, get_payment_keyboard, TARIFS
from app.services.marzban_api import marzban_client
from config import PROVIDER_TOKEN, CRYPTO_TOKEN
from datetime import datetime, timedelta
from aiocryptopay import AioCryptoPay, Networks
import asyncio
from aiocryptopay.exceptions import CryptoPayAPIError

router = Router()
crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET)

@router.message(F.text == "💳 Купить")
async def handle_buy_menu(message: Message):
    await message.delete()

    await message.answer("👋 Для полного доступа выберите удобный для вас тариф:\n\n"
             "200₽ / 3$ / 1 мес\n" "600₽ / 8$ / 3 мес\n" "1200₽ / 16$ /  6 мес\n\n"
             "💳 Можно оплатить через:\n"
             "Звёзды Telegram и криптовалюту.",
             reply_markup=get_tarfs_keyboard(),
             parse_mode="Markdown",
    )
    
@router.callback_query(F.data.startswith("buy_"))
async def handle_tarrife(callback: CallbackQuery):
    tariff = callback.data.split("_")[1]
    user_id = callback.from_user.id

    async with await get_db_session() as session: 
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalars().first()

        if not user:
            user = User(
                id=user_id,
                username=callback.from_user.username or "",
                registration_date=datetime.utcnow() 
            )
            session.add(user)
            await session.commit()
        pass

    title = TARIFS[tariff]["title"]
    response = f"👌 **Вы выбрали тариф:** {title}\n\nВыберите удобный способ оплаты:"

    await callback.message.edit_text(
        text=response,
        reply_markup=get_payment_keyboard(tariff),
        parse_mode="Markdown",
    )

    await callback.answer()


@router.callback_query(F.data.startswith("pay_stars_"))
async def process_payment(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    try:
        tariff_code = callback.data.split("_")[2] 
    except IndexError:
        await callback.answer("Ошибка: Неверный формат данных тарифа.")
        return

    if tariff_code not in TARIFS:
        await callback.answer("Ошибка: Тариф не выбран или не найден.")
        return
    
    tariff_data = TARIFS[tariff_code]
    
    prices = [
        LabeledPrice(label=tariff_data['title'], amount=tariff_data['stars']) 
    ]

    payload = f"stars_{tariff_code}_{user_id}"
    
    try:
        await bot.send_invoice (
            chat_id = user_id,
            title = tariff_data["title"],
            description=tariff_data['description'],
            payload=payload, 
            provider_token=PROVIDER_TOKEN,
            currency="XTR", 
            prices=prices,
            reply_markup=None,
        )
    except TelegramBadRequest as e:
        print(f"Ошибка при отправке инвойса: {e}")
        await callback.message.answer("Произошла ошибка при создании счета.")
    
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    try:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except TelegramAPIError as e:
        print(f"Ошибка PreCheckout: {e}")

@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: Message):
    
    payment_info = message.successful_payment
    user_id = message.from_user.id

    try:
        _, tariff_code, _ = payment_info.invoice_payload.split('_') 
    except ValueError:
        await message.answer("Ошибка: Неверный формат данных оплаты.")
        return
    
    tariff_data = TARIFS.get(tariff_code)
    if not tariff_data:
        await message.answer("Ошибка: Тариф оплаты не найден в системе.")
        return
        
    title = tariff_data.get("title", "Ваш новый тариф")
    
    subscription_link = await marzban_client.create_user(
        telegram_user_id=user_id, 
        tariff_code=tariff_code, 
        user_data=tariff_data
    )
    
    if subscription_link:
        response_text = (
            "🎉 **Оплата прошла успешно!** 🎉\n"
            f"Вы приобрели: **{title}**.\n\n"
            "🔑 **Ваша персональная ссылка для подписки:**\n"
            f"```\n{subscription_link}\n```\n\n"
            "🔗 Нажмите на ссылку, чтобы добавить ключ в ваш VPN-клиент (V2RayNG, Hiddify и т.д.).\n"
            "💡 Нажмите **❤️ Подключится** для дальнейших инструкций и просмотра ссылки."
        )
    else:
        response_text = (
            "⚠️ **Оплата прошла успешно**, но произошла ошибка при генерации ключа.\n"
            "Администратор уже уведомлен. Пожалуйста, свяжитесь с поддержкой."
        )
        
    await message.answer(
        text=response_text,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("pay_crypto_"))
async def crypto_payment(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    try:
        tariff_code = callback.data.split("_")[2]
    except IndexError:
        await callback.answer("Ошибка: неверный формат данных тарифа.")
        return

    if tariff_code not in TARIFS:
        await callback.answer("Ошибка: тариф не найден.")
        return

    tariff_data = TARIFS[tariff_code]

    try:
        invoice = await crypto.create_invoice(
            asset="USDT",  
            amount=tariff_data["price_usd"],  
            description=f"Оплата тарифа {tariff_data['title']} пользователем {user_id}",
            hidden_message="Спасибо за оплату! После оплаты дождитесь подтверждения.",
            payload=f"crypto_{tariff_code}_{user_id}", 
            expires_in=3600, 
        )

        async with await get_db_session() as session:
            invoice_id_str = str(invoice.invoice_id)
            
            subscription = Subscription(
                user_id=user_id,
                marzban_username=None,
                tariff_code=tariff_code,
                expires_at=None,
                data_limit_gb=tariff_data["limit_gb"],
                status="pending",
                invoice_id=invoice_id_str,
                is_paid=False,
            )
            session.add(subscription)
            await session.commit()


        await callback.message.answer(
            text=(
                f"💎 **Оплата криптовалютой ({tariff_data['title']})**\n\n"
                f"💰 Сумма: {tariff_data['price_usd']} USDT\n"
                f"🕐 Срок действия счета: 1 час\n\n"
                f"👉 [Перейти к оплате]({invoice.bot_invoice_url})"
            ),
            parse_mode="Markdown",
        )

    except Exception as e:
        print(f"Ошибка при создании crypto-инвойса: {e}") 
        await callback.message.answer("Произошла ошибка при создании крипто-счета. Пожалуйста, попробуйте снова.")

    await callback.answer()


async def check_crypto_payments(bot: Bot):
    while True:
        unpaid_subs_count = 0 
        try:
            async with await get_db_session() as session:
                result = await session.execute(
                    select(Subscription).where(
                        Subscription.is_paid == False,
                        Subscription.invoice_id.is_not(None),
                    )
                )
                unpaid_subs = result.scalars().all()
                unpaid_subs_count = len(unpaid_subs) 

                for sub in unpaid_subs:
                    try:
                        invoice_id_str = str(sub.invoice_id)
                        
                        invoice_result = await crypto.get_invoices(invoice_ids=[invoice_id_str])
                        
                        invoices = None
                        if invoice_result is None:
                            print(f"❌ Ошибка: CryptoPay вернул None для инвойса {sub.invoice_id}. Проверьте токен/сеть.")
                            continue
                        elif isinstance(invoice_result, list):
                            invoices = invoice_result
                        elif hasattr(invoice_result, 'items'):
                            invoices = invoice_result.items
                        else:
                            print(f"❌ Неизвестный формат ответа CryptoPay: {type(invoice_result)} для инвойса {sub.invoice_id}")
                            continue

                        if not invoices:
                            print(f"⚠️ Инвойс {sub.invoice_id} не найден.")
                            continue

                        inv = invoices[0] 
                        
                        if inv.status == "paid":
                            print(f"✅ Инвойс {sub.invoice_id} оплачен пользователем {sub.user_id}")

                            link = None
                            try:
                                metadata = marzban_client.metadata_presets.get(sub.tariff_code, {})
                                duration_s = metadata.get('expire', 0)
      
                                link = await marzban_client.create_user(
                                    telegram_user_id=sub.user_id,
                                    tariff_code=sub.tariff_code,
                                    user_data=TARIFS[sub.tariff_code]
                                )
                            except CryptoPayAPIError as e:
                                print(f"❌ Ошибка CryptoPay API: {e}")
                                continue
                            except Exception as marzban_e:
                                print(f"❌ Ошибка при создании пользователя {sub.user_id}: {marzban_e}")
                                await bot.send_message(
                                    sub.user_id,
                                    "⚠️ Оплата прошла. Повторим попытку через 30 секунд.",
                                )
                                continue
                            
                            if link:
                                start_date = sub.expires_at if sub.expires_at and sub.expires_at > datetime.utcnow() else datetime.utcnow()
                                duration_timedelta = timedelta(seconds=duration_s)

                                sub.expires_at = start_date + duration_timedelta
                                sub.is_paid = True
                                sub.vpn_link = link
                                sub.status = "active" 
                                
                                await session.commit()

                                await bot.send_message(
                                    sub.user_id,
                                    f"🎉 Оплата прошла успешно!\n\n🔑 Ваша ссылка:\n\n{link}\n",
                                    parse_mode="Markdown"
                                )
                            else:
                                await bot.send_message(
                                    sub.user_id,
                                    "⚠️ Оплата прошла, но не удалось создать ключ VPN. Пожалуйста, свяжитесь с поддержкой.",
                                    parse_mode="Markdown"
                                )
                                
                    except Exception as e:
                        print(f"Ошибка при проверке или обработке инвойса {sub.invoice_id}: {e}")

        except Exception as e:
            print("Ошибка при проверке криптооплаты (DB):", e)

        await asyncio.sleep(30)
        
        if unpaid_subs_count > 0:
            print(f"Проверяю {unpaid_subs_count} неоплаченных инвойсов...")