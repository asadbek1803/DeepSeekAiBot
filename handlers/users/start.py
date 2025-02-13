from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.enums.parse_mode import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.session.middlewares.request_logging import logger
from loader import db, bot

from data.config import ADMINS
from componets.messages import messages, buttons
from datetime import datetime

router = Router()

# Tilni tanlash uchun Reply Keyboard
language_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="\U0001F1FA\U0001F1FF O'zbek")],
        [KeyboardButton(text="\U0001F1F7\U0001F1FA Русский")],
        [KeyboardButton(text="\U0001F1FA\U0001F1F8 English")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

def get_keyboard(language):
    """Foydalanuvchi tiliga mos tugmalarni qaytaradi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=buttons[language]["btn_open_webapp"])],
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
        text = f"Assalomu alaykum, <b>{full_name}</b>! \U0001F44B\n{messages['uz']['choose_lang']}"
        await message.answer(text=text, reply_markup=language_keyboard, parse_mode=ParseMode.HTML)

@router.message(lambda message: message.text in ["🇺🇿 O'zbek", "🇷🇺 Русский", "🇺🇸 English"])
async def create_account(message: types.Message):
    """Foydalanuvchini bazaga qo'shish va unga til tanlanganiga qarab xabar yuborish."""
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    language_map = {"🇺🇿 O'zbek": "uz", "🇷🇺 Русский": "ru", "🇺🇸 English": "eng"}
    language = language_map[message.text]

    welcome_messages = {
        "uz": ("Akkaunt muvaffaqiyatli yaratildi ✅", 
               f"Assalomu alaykum <b>{full_name}</b>! Bizning DeepSeek AI botga xush kelibsiz 😊"),
        "ru": ("Аккаунт успешно создан ✅", 
               f"Привет <b>{full_name}</b>! Добро пожаловать в наш AI-бот DeepSeek 😊"),
        "eng": ("Account created successfully ✅", 
                f"Hello <b>{full_name}</b>! Welcome to our DeepSeek AI bot 😊")
    }

    try:
        await db.add_user(telegram_id=telegram_id, full_name=full_name, username=username, language=language)
        success_msg, welcome_msg = welcome_messages[language]
        await message.answer(text=success_msg)
        await bot.send_message(chat_id=telegram_id, text=welcome_msg, parse_mode=ParseMode.HTML, reply_markup=get_keyboard(language))
        now = datetime.now()
        # Adminlarga xabar yuborish
        admin_msg = (
            f"Yangi foydalanuvchi ro'yxatdan o'tdi ✅\n"
            f"👤 Ism: <b>{full_name}</b>\n"
            f"📌 Telegram ID: <code>{telegram_id}</code>\n"
            f"🌍 Til: <b>{language.upper()}</b>\n"
            f"📅 Qo'shilgan sana: <b>{now}</b>\n"
            f"📊 Bazadagi a'zolar soni: <b>{int(db.count_users())}</b>"
        )
        for admin in ADMINS:
            try:
                await bot.send_message(chat_id=admin, text=admin_msg, parse_mode=ParseMode.HTML)
            except Exception as error:
                logger.info(f"Xatolik: Admin {admin} ga xabar jo'natilmadi. {error}")
    except Exception as e:
        await message.answer(text=f"Xatolik yuz berdi ❌\n{str(e)}")

@router.message(Command("change_language"))
async def change_language(message: types.Message):
    """Foydalanuvchiga tilni tanlash menyusini ko‘rsatish."""
    await message.answer("🌍 Iltimos, yangi tilni tanlang:", reply_markup=language_keyboard)

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
