from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.enums.parse_mode import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from loader import db, bot

from data.config import ADMINS
from componets.messages import messages, buttons
from datetime import datetime

router = Router()

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
    username = message.from_user.username or "Noma'lum"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = await db.select_user(telegram_id=telegram_id)

    if user:
        # Mavjud foydalanuvchi uchun
        language = user.get("language", "uz")
        text = messages[language]["start"].format(name=full_name)
        await message.answer(text=text, parse_mode=ParseMode.HTML, reply_markup=get_keyboard(language))
    else:
        # Yangi foydalanuvchi uchun faqat til tanlash menyusini ko'rsatamiz
        text = f"Assalomu alaykum, <b>{full_name}</b>! 👋\n{messages['uz']['choose_lang']}"
        await message.answer(text=text, reply_markup=language_keyboard(), parse_mode=ParseMode.HTML)

@router.message(lambda message: message.text in ["🇺🇿 O'zbek", "🇷🇺 Русский", "🇺🇸 English"])
async def handle_language_selection(message: types.Message):
    """Foydalanuvchining tilini tanlash va bazaga qo'shish."""
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username or "Noma'lum"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    language_map = {
        "🇺🇿 O'zbek": "uz",
        "🇷🇺 Русский": "ru",
        "🇺🇸 English": "eng"
    }
    selected_language = language_map[message.text]
    
    user = await db.select_user(telegram_id=telegram_id)
    if not user:
        # Yangi foydalanuvchini bazaga qo'shamiz
        await db.add_user(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            language=selected_language
        )
        
        # Adminlarga xabar yuborish
        admin_text = (f"✅ <b>Yangi foydalanuvchi qo'shildi!</b>\n\n"
                     f"👤 <b>Ism:</b> {full_name}\n"
                     f"👥 <b>Username:</b> @{username}\n"
                     f"🔑 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
                     f"🌐 <b>Tanlangan til:</b> {message.text}\n"
                     f"⏰ <b>Ro'yxatdan o'tgan vaqti:</b> {created_at}")
        
        for admin in ADMINS:
            await bot.send_message(chat_id=admin, text=admin_text, parse_mode=ParseMode.HTML)
    else:
        # Mavjud foydalanuvchi uchun tilni yangilaymiz
        await db.update_user_language(telegram_id, selected_language)
    
    # Foydalanuvchiga uning tanlagan tilidagi xabarni yuboramiz
    text = messages[selected_language]["start"].format(name=full_name)
    await message.answer(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_keyboard(selected_language)
    )

@router.message(Command("change_language"))
@router.message(lambda message: message.text in [buttons["uz"]["btn_change_lang"], 
                                               buttons["ru"]["btn_change_lang"], 
                                               buttons["eng"]["btn_change_lang"]])
async def change_language(message: types.Message):
    """Foydalanuvchiga tilni tanlash menyusini ko'rsatish."""
    await message.answer("🌍 Iltimos, yangi tilni tanlang:", reply_markup=language_keyboard())