import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)

from config import BOT_TOKEN, PRICE_AMOUNT, PRICE_ASSET, ACCESS_HOURS, VLESS_KEY, BANNER_PATH
from cryptobot import create_invoice, get_invoice_status
from storage import save_invoice, mark_paid, is_paid

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"🔑 Купить доступ — {PRICE_AMOUNT}$ / {ACCESS_HOURS}ч",
                callback_data="buy"
            )],
            [InlineKeyboardButton(text="ℹ️ Как подключиться", callback_data="howto")],
        ]
    )


def pay_kb(invoice_id: str, pay_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
            [InlineKeyboardButton(text="✅ Я оплатил, проверить", callback_data=f"check_{invoice_id}")],
        ]
    )


WELCOME_TEXT = (
    "🟣 <b>MartVPN</b>\n\n"
    "Быстрый и стабильный VPN-доступ.\n"
    f"Стоимость: <b>{PRICE_AMOUNT}$</b> за <b>{ACCESS_HOURS} часа</b>.\n"
    "Оплата через CryptoBot — мгновенно и без ограничений по региону.\n\n"
    "Жми на кнопку ниже, чтобы получить ключ 👇"
)

HOWTO_TEXT = (
    "📱 <b>Как подключиться</b>\n\n"
    "1. Скачай приложение Happ (или любой V2Ray/VLESS клиент)\n"
    "2. Скопируй выданную ссылку\n"
    "3. Импортируй её в приложение (обычно кнопка «Добавить подписку по ссылке»)\n"
    "4. Подключайся ✅"
)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    if os.path.exists(BANNER_PATH):
        photo = FSInputFile(BANNER_PATH)
        await message.answer_photo(
            photo=photo,
            caption=WELCOME_TEXT,
            reply_markup=main_menu_kb(),
        )
    else:
        await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@dp.callback_query(F.data == "howto")
async def cb_howto(callback: CallbackQuery):
    await callback.message.answer(HOWTO_TEXT)
    await callback.answer()


@dp.callback_query(F.data == "buy")
async def cb_buy(callback: CallbackQuery):
    await callback.answer("Создаю счет...")
    try:
        invoice_id, pay_url = await create_invoice()
    except Exception as e:
        logging.exception("Ошибка создания инвойса")
        await callback.message.answer(f"⚠️ Не удалось создать счет: {e}")
        return

    save_invoice(invoice_id, callback.from_user.id)

    await callback.message.answer(
        f"Счет на {PRICE_AMOUNT} {PRICE_ASSET} создан.\n"
        "Оплати по кнопке ниже, затем нажми «Я оплатил, проверить».",
        reply_markup=pay_kb(invoice_id, pay_url),
    )


@dp.callback_query(F.data.startswith("check_"))
async def cb_check(callback: CallbackQuery):
    invoice_id = callback.data.split("_", 1)[1]

    if is_paid(invoice_id):
        await deliver_key(callback)
        return

    try:
        status = await get_invoice_status(invoice_id)
    except Exception as e:
        logging.exception("Ошибка проверки инвойса")
        await callback.answer(f"Ошибка проверки: {e}", show_alert=True)
        return

    if status == "paid":
        mark_paid(invoice_id)
        await deliver_key(callback)
    else:
        await callback.answer("Оплата пока не найдена. Попробуй через минуту.", show_alert=True)


async def deliver_key(callback: CallbackQuery):
    text = (
        "✅ <b>Оплата подтверждена!</b>\n\n"
        f"Твой доступ на {ACCESS_HOURS} часа:\n\n"
        f"<code>{VLESS_KEY}</code>\n\n"
        "Скопируй ссылку и импортируй её в приложении (Happ / v2rayNG / Hiddify)."
    )
    await callback.message.answer(text)
    await callback.answer("Готово! Ключ отправлен ✅")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
