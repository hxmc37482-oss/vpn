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

from config import BOT_TOKEN, PLANS, PRICE_ASSET, VLESS_KEY, BANNER_PATH
from cryptobot import create_invoice, get_invoice_status
from storage import save_invoice, mark_paid, is_paid, get_plan_id

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------- Клавиатуры ----------

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Прайс", callback_data="price")],
            [InlineKeyboardButton(text="ℹ️ Как подключиться", callback_data="howto")],
            [InlineKeyboardButton(text="🛟 Поддержка", url="https://t.me/snilszepo")],
        ]
    )


def price_kb() -> InlineKeyboardMarkup:
    rows = []
    for plan_id, plan in PLANS.items():
        rows.append([
            InlineKeyboardButton(
                text=f"{plan['emoji']} {plan['title']} — {plan['amount']}$",
                callback_data=f"buy_{plan_id}",
            )
        ])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pay_kb(invoice_id: str, pay_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
            [InlineKeyboardButton(text="✅ Я оплатил, проверить", callback_data=f"check_{invoice_id}")],
        ]
    )


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ В меню", callback_data="back_main")]]
    )


# ---------- Тексты ----------

WELCOME_TEXT = (
    "🟣 <b>MartVPN</b>\n"
    "Быстрый и стабильный доступ в интернет без границ\n\n"
    "🚀 Высокая скорость\n"
    "🔒 Надежное шифрование\n"
    "⚡️ Мгновенная выдача ключа после оплаты\n\n"
    "Выбирай тариф в разделе «Прайс» и подключайся 👇"
)

HOWTO_TEXT = (
    "📱 <b>Как подключиться</b>\n\n"
    "1️⃣ Скачай приложение Happ (или любой V2Ray/VLESS клиент)\n"
    "2️⃣ Скопируй выданную ссылку\n"
    "3️⃣ В приложении выбери «Добавить подписку по ссылке»\n"
    "4️⃣ Вставь ссылку и подключайся ✅"
)

PRICE_TEXT = (
    "💎 <b>Тарифы MartVPN</b>\n\n"
    "Выбери подходящий вариант:"
)


# ---------- Хендлеры ----------

@dp.message(CommandStart())
async def cmd_start(message: Message):
    if os.path.exists(BANNER_PATH):
        photo = FSInputFile(BANNER_PATH)
        await message.answer_photo(photo=photo, caption=WELCOME_TEXT, reply_markup=main_menu_kb())
    else:
        await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
    await callback.answer()


@dp.callback_query(F.data == "howto")
async def cb_howto(callback: CallbackQuery):
    await callback.message.answer(HOWTO_TEXT, reply_markup=back_kb())
    await callback.answer()


@dp.callback_query(F.data == "price")
async def cb_price(callback: CallbackQuery):
    await callback.message.answer(PRICE_TEXT, reply_markup=price_kb())
    await callback.answer()


@dp.callback_query(F.data.startswith("buy_"))
async def cb_buy(callback: CallbackQuery):
    plan_id = callback.data.split("_", 1)[1]
    plan = PLANS.get(plan_id)
    if not plan:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    await callback.answer("Создаю счет...")
    try:
        invoice_id, pay_url = await create_invoice(
            amount=plan["amount"],
            description=f"MartVPN — {plan['title']}",
        )
    except Exception as e:
        logging.exception("Ошибка создания инвойса")
        await callback.message.answer(f"⚠️ Не удалось создать счет: {e}")
        return

    save_invoice(invoice_id, callback.from_user.id, plan_id)

    await callback.message.answer(
        f"{plan['emoji']} <b>{plan['title']}</b> — {plan['amount']} {PRICE_ASSET}\n\n"
        "Оплати по кнопке ниже, затем нажми «Я оплатил, проверить».",
        reply_markup=pay_kb(invoice_id, pay_url),
    )


@dp.callback_query(F.data.startswith("check_"))
async def cb_check(callback: CallbackQuery):
    invoice_id = callback.data.split("_", 1)[1]

    if is_paid(invoice_id):
        await deliver_key(callback, invoice_id)
        return

    try:
        status = await get_invoice_status(invoice_id)
    except Exception as e:
        logging.exception("Ошибка проверки инвойса")
        await callback.answer(f"Ошибка проверки: {e}", show_alert=True)
        return

    if status == "paid":
        mark_paid(invoice_id)
        await deliver_key(callback, invoice_id)
    else:
        await callback.answer("Оплата пока не найдена. Попробуй через минуту.", show_alert=True)


async def deliver_key(callback: CallbackQuery, invoice_id: str):
    plan_id = get_plan_id(invoice_id)
    plan = PLANS.get(plan_id, {})
    title = plan.get("title", "")

    text = (
        "✅ <b>Оплата подтверждена!</b>\n\n"
        f"Тариф: <b>{title}</b>\n\n"
        f"Твоя ссылка доступа:\n"
        f"<code>{VLESS_KEY}</code>\n\n"
        "Импортируй её в приложении (Happ / v2rayNG / Hiddify).\n"
        "Если что-то не работает — жми «Поддержка» в главном меню."
    )
    await callback.message.answer(text, reply_markup=back_kb())
    await callback.answer("Готово! Ключ отправлен ✅")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
