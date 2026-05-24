"""
handlers/commands.py — пользовательские команды:
                        /start, /models, /city, /status, /favorites, /help
"""

import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import database as db
from config import settings
from utils.helpers import HELP_TEXT, error_handler, get_status_text
from utils.keyboards import (
    FavoriteCB,
    get_city_keyboard,
    get_main_reply_keyboard,
    get_main_inline_keyboard,
    get_models_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "📱 Главное меню")
@router.message(CommandStart())
@error_handler
async def cmd_start(message: Message) -> None:
    menu_kb = get_main_reply_keyboard()
    inline_kb = get_main_inline_keyboard()
    
    await message.answer(
        "👋 <b>Главное меню ECHELON</b>",
        reply_markup=menu_kb
    )
    await message.answer(
        "Выберите нужный раздел ниже:",
        reply_markup=inline_kb
    )


@router.message(Command("help"))
@error_handler
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("status"))
@error_handler
async def cmd_status(message: Message) -> None:
    await message.answer(await get_status_text(message.from_user.id))


@router.message(Command("models"))
@error_handler
async def cmd_models(message: Message) -> None:
    user_models = await db.get_user_models(message.from_user.id)
    all_models = await db.get_all_models()
    selected = [m.model_id for m in user_models]
    await message.answer(
        "Выбери модели для мониторинга. Уведомления приходят только о выгодных предложениях.",
        reply_markup=get_models_keyboard(selected, all_models),
    )


@router.message(Command("city"))
@error_handler
async def cmd_city(message: Message) -> None:
    cities = await db.get_cities(message.from_user.id)
    await message.answer(
        f"Текущие города: <b>{', '.join(cities)}</b>\n\n"
        f"Выбери города для мониторинга. «Россия» работает по всей стране "
        f"и не сочетается с конкретными городами.",
        reply_markup=get_city_keyboard(cities, settings.CITIES, settings.CITIES_PER_PAGE, page=0),
    )


@router.message(Command("favorites"))
@error_handler
async def cmd_favorites(message: Message) -> None:
    favorites = await db.get_favorites(message.from_user.id)
    if not favorites:
        await message.answer("В избранном пусто.")
        return

    await message.answer(f"⭐ Избранное ({len(favorites)}):")
    for fav in favorites[:10]:
        import html

        price_str = f"{fav['price']}₽" if fav["price"] else "Цена не указана"
        text = (
            f"📱 <b>{html.escape(fav['title'])}</b>\n\n"
            f"💵 <b>{price_str}</b>\n"
            f"📍 {html.escape(fav['city'] or 'Россия')}\n"
            f"📁 {html.escape(fav['model_name'])}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔗 Открыть", url=fav["url"]),
                    InlineKeyboardButton(
                        text="❌ Удалить",
                        callback_data=FavoriteCB(
                            action="remove", listing_id=fav["listing_id"]
                        ).pack(),
                    ),
                ]
            ]
        )
        await message.answer(text, reply_markup=keyboard)
        await asyncio.sleep(0.1)

    if len(favorites) > 10:
        await message.answer(f"Показаны первые 10 из {len(favorites)}.")
