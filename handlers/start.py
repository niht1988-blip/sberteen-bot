from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards import main_menu_keyboard

router = Router()


class RegistrationState(StatesGroup):
    waiting_for_name = State()


WELCOME_TEXT = (
    "🟡 <b>Привет, {name}!</b>\n\n"
    "Добро пожаловать в <b>SberTeen</b> — образовательное пространство для подростков!\n\n"
    "📅 Записывайся на мероприятия\n"
    "📝 Сдавай задания\n"
    "💰 Копи сберкоины\n\n"
    "Нажми <b>Зарегистрироваться</b>, чтобы начать!"
)


@router.message(CommandStart())
async def cmd_start(message: Message, db, user, state: FSMContext):
    if user:
        is_admin = user["role"] == "admin"
        await message.answer(
            f"🟡 С возвращением, <b>{user['full_name']}</b>!\n"
            f"💰 Баланс: {user['sbercoins']} сберкоинов",
            reply_markup=main_menu_keyboard(is_admin),
        )
        return

    await message.answer(
        WELCOME_TEXT.format(name=message.from_user.first_name),
        parse_mode="HTML",
    )
    await message.answer("✏️ Введи своё <b>имя и фамилию</b>:", parse_mode="HTML")
    await state.set_state(RegistrationState.waiting_for_name)


@router.message(RegistrationState.waiting_for_name)
async def process_name(message: Message, db, state: FSMContext):
    full_name = message.text.strip()
    if len(full_name) < 2:
        await message.answer("Имя слишком короткое. Попробуй ещё раз:")
        return

    await db.create_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=full_name,
    )

    await message.answer(
        f"🟢 Регистрация завершена, <b>{full_name}</b>!\n\n"
        f"Ты участник SberTeen. Зарабатывай сберкоины за активность!",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()


@router.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery, db, user):
    if not user:
        await callback.answer("Сначала зарегистрируйся через /start", show_alert=True)
        return
    is_admin = user["role"] == "admin"
    await callback.message.edit_text(
        f"🟡 <b>Главное меню</b>\n\n"
        f"💰 Баланс: <b>{user['sbercoins']}</b> сберкоинов",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(is_admin),
    )
    await callback.answer()
