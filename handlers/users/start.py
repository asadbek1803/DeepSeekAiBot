from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.enums.parse_mode import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.client.session.middlewares.request_logging import logger
from loader import db, bot

from data.config import ADMINS
from componets.messages import messages, buttons
from datetime import datetime

router = Router()

# ReplyKeyboardMarkup uchun funksiyalar
def language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbek")],
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text='🇺🇸 English')]
        ],
        resize_keyboard=True
    )

def get_keyboard(language):
    """Foydalanuvchi tiliga mos Reply tugmalarni qaytaradi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text=buttons[language]["btn_open_webapp"],
                web_app=WebAppInfo(url="https://chat.deepseek.com/")
            )],
            [KeyboardButton(text=buttons[language]["btn_change_lang"])]
        ],
        resize_keyboard=True
    )

@router.message(CommandStart())
async def do_start(message: types.Message):
    """Foydalanuvchini tekshirish va u tanlagan til bo'yicha xabar yuborish."""
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    user = await db.select_user(telegram_id=telegram_id)

    if user:
        language = user.get("language", "uz")
        text = messages[language]["start"].format(name=full_name)
        await message.answer(text=text, parse_mode=ParseMode.HTML, reply_markup=get_keyboard(language))
    else:
        text = f"Assalomu alaykum, <b>{full_name}</b>! 👋\n{messages['uz']['choose_lang']}"
        await message.answer(text=text, reply_markup=language_keyboard(), parse_mode=ParseMode.HTML)

@router.message(Command("change_language"))
@router.message(lambda message: message.text == buttons["uz"]["btn_change_lang"] or \
                             message.text == buttons["ru"]["btn_change_lang"] or \
                             message.text == buttons["eng"]["btn_change_lang"])
async def change_language(message: types.Message):
    """Foydalanuvchiga tilni tanlash menyusini ko‘rsatish."""
    await message.answer("🌍 Iltimos, yangi tilni tanlang:", reply_markup=language_keyboard())

@router.message(lambda message: message.text in ["🇺🇿 O'zbek", "🇷🇺 Русский", "🇺🇸 English"])
async def update_language(message: types.Message):
    """Foydalanuvchining tilini bazada yangilash."""
    telegram_id = message.from_user.id
    language_map = {"🇺🇿 O'zbek": "uz", "🇷🇺 Русский": "ru", "🇺🇸 English": "eng"}
    new_language = language_map[message.text]
    await db.update_user_language(telegram_id, new_language)
    confirmation_messages = {
        "uz": "✅ Til muvaffaqiyatli o‘zgartirildi.",
        "ru": "✅ Язык успешно изменен.",
        "eng": "✅ Language successfully changed."
    }
    await message.answer(text=confirmation_messages[new_language], reply_markup=get_keyboard(new_language))
