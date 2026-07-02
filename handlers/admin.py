import csv
import io
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import date

from config import ADMIN_PASSWORD
from keyboards import (
    admin_menu_keyboard,
    admin_schedule_keyboard,
    admin_event_actions,
    admin_hw_keyboard,
    admin_hw_review_keyboard,
    admin_users_keyboard,
    admin_coins_keyboard,
    main_menu_keyboard,
)

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message, db, user, state: FSMContext):
    await state.clear()
    if not user:
        await message.answer("Сначала зарегистрируйся через /start")
        return
    if is_admin_user(user):
        await message.answer(
            "🟡 <b>Панель администратора</b>",
            parse_mode="HTML",
            reply_markup=admin_menu_keyboard(),
        )
    else:
        await message.answer(
            "🔑 Введи <b>пароль администратора</b>:", parse_mode="HTML"
        )
        await state.set_state(AdminState.waiting_password)


class AdminState(StatesGroup):
    waiting_password = State()
    add_title = State()
    add_date = State()
    add_time = State()
    add_type = State()
    add_location = State()
    add_description = State()
    edit_field = State()
    coins_select_user = State()
    coins_enter_amount = State()


def is_admin_user(user) -> bool:
    return user is not None and user["role"] == "admin"


@router.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery, db, user, state: FSMContext):
    await state.clear()
    if not is_admin_user(user):
        await callback.answer("🔒 Введи пароль администратора", show_alert=True)
        await callback.message.edit_text(
            "🔑 Введи <b>пароль администратора</b>:", parse_mode="HTML"
        )
        await state.set_state(AdminState.waiting_password)
        return

    await callback.message.edit_text(
        "🟡 <b>Панель администратора</b>",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


@router.message(AdminState.waiting_password)
async def check_password(message: Message, db, state: FSMContext):
    if message.text.strip() == ADMIN_PASSWORD:
        await db.set_role(message.from_user.id, "admin")
        await state.clear()
        await message.answer(
            "🟢 <b>Доступ получен!</b>",
            parse_mode="HTML",
            reply_markup=admin_menu_keyboard(),
        )
    else:
        await message.answer("❌ Неверный пароль. Попробуй ещё раз:")


# ── Управление расписанием ──

@router.callback_query(F.data == "admin_schedule")
async def admin_schedule(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "📅 <b>Управление расписанием</b>",
        parse_mode="HTML",
        reply_markup=admin_schedule_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users_list(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        await callback.answer("Нет доступа", show_alert=True)
        return
    users = await db.get_all_users()
    text = f"👥 <b>Пользователи ({len(users)})</b>\n\n"
    for u in users[:20]:
        role_icon = "⚙️" if u["role"] == "admin" else "👤"
        text += f"{role_icon} {u['full_name']} (@{u['username'] or '—'}) — {u['sbercoins']} 🪙\n"
    if len(users) > 20:
        text += f"\n... и ещё {len(users) - 20}"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_users_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_add_event")
async def admin_add_start(callback: CallbackQuery, db, user, state: FSMContext):
    if not is_admin_user(user):
        return
    await state.set_state(AdminState.add_title)
    await callback.message.edit_text(
        "➕ <b>Новое мероприятие</b>\n\n📝 Введи <b>название</b>:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminState.add_title)
async def admin_add_date(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminState.add_date)
    await message.answer(
        "📅 Введи <b>дату</b> (ГГГГ-ММ-ДД), например <code>2026-07-03</code>:",
        parse_mode="HTML",
    )


@router.message(AdminState.add_date)
async def admin_add_time(message: Message, state: FSMContext):
    try:
        date.fromisoformat(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный формат. Используй ГГГГ-ММ-ДД:")
        return
    await state.update_data(date=message.text.strip())
    await state.set_state(AdminState.add_time)
    await message.answer("⏰ Введи <b>время</b> (ЧЧ:ММ), например <code>11:00</code>:", parse_mode="HTML")


@router.message(AdminState.add_time)
async def admin_add_type(message: Message, state: FSMContext):
    time_str = message.text.strip()
    if len(time_str) != 5 or time_str[2] != ":":
        await message.answer("❌ Неверный формат. Используй ЧЧ:ММ:")
        return
    await state.update_data(time=time_str)
    await state.set_state(AdminState.add_type)
    await message.answer(
        "📍 Тип мероприятия:\n"
        "• <b>1</b> — Онлайн\n"
        "• <b>2</b> — Оффлайн (введите город)",
        parse_mode="HTML",
    )


@router.message(AdminState.add_type)
async def admin_add_location(message: Message, state: FSMContext):
    choice = message.text.strip()
    if choice == "1":
        await state.update_data(event_type="online", location="online")
        await state.set_state(AdminState.add_description)
        await message.answer("📝 Введи <b>описание</b> (или «-» чтобы пропустить):", parse_mode="HTML")
    elif choice == "2":
        await state.update_data(event_type="offline")
        await state.set_state(AdminState.add_location)
        await message.answer("🏙 Введи <b>город</b>:", parse_mode="HTML")
    else:
        await message.answer("❌ Выбери 1 или 2:")


@router.message(AdminState.add_location)
async def admin_add_location_done(message: Message, state: FSMContext):
    await state.update_data(location=message.text.strip())
    await state.set_state(AdminState.add_description)
    await message.answer("📝 Введи <b>описание</b> (или «-» чтобы пропустить):", parse_mode="HTML")


@router.message(AdminState.add_description)
async def admin_add_finish(message: Message, db, state: FSMContext):
    data = await state.get_data()
    description = message.text.strip() if message.text.strip() != "-" else ""

    await db.create_event(
        title=data["title"],
        ev_date=data["date"],
        ev_time=data["time"],
        location=data["location"],
        event_type=data["event_type"],
        description=description,
    )

    await state.clear()
    await message.answer(
        f"✅ <b>Мероприятие создано!</b>\n\n"
        f"📌 {data['title']}\n"
        f"📅 {data['date']} {data['time']}\n"
        f"📍 {data['location']}",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(),
    )


@router.callback_query(F.data == "admin_list_events")
async def admin_list_events(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        return
    events = await db.get_events_page(0, 100)
    if not events:
        text = "🟡 Расписание пусто"
    else:
        text = "📅 <b>Все мероприятия:</b>\n\n"
        for ev in events:
            icon = "🔵" if ev["event_type"] == "online" else "🟡"
            text += f"{icon} <b>{ev['title']}</b>\n📅 {ev['date']} {ev['time']} | {ev['location']}\n\n"

    from keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [
        [InlineKeyboardButton(
            text=f"📌 {ev['title']}", callback_data=f"admin_ev:{ev['id']}"
        )]
        for ev in events
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_schedule")])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_ev:"))
async def admin_event_detail(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        return
    event_id = int(callback.data.split(":")[1])
    event = await db.get_event(event_id)
    if not event:
        await callback.answer("Не найдено", show_alert=True)
        return

    participants = await db.get_event_participants(event_id)
    p_text = "\n".join(f"  👤 {p['full_name']}" for p in participants) or "  Нет записей"

    text = (
        f"📌 <b>{event['title']}</b>\n"
        f"📅 {event['date']} {event['time']}\n"
        f"📍 {event['location']}\n\n"
        f"👥 Участники ({len(participants)}):\n{p_text}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_event_actions(event_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete:"))
async def admin_delete_event(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        return
    event_id = int(callback.data.split(":")[1])
    event = await db.get_event(event_id)
    await db.delete_event(event_id)
    await callback.answer(f"🗑 «{event['title']}» удалено", show_alert=True)
    await callback.message.edit_text(
        "🟡 <b>Мероприятие удалено</b>",
        parse_mode="HTML",
        reply_markup=admin_schedule_keyboard(),
    )


@router.callback_query(F.data.startswith("admin_participants:"))
async def admin_participants(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        return
    event_id = int(callback.data.split(":")[1])
    event = await db.get_event(event_id)
    participants = await db.get_event_participants(event_id)

    text = f"👥 <b>Участники «{event['title']}»:</b>\n\n"
    if participants:
        for i, p in enumerate(participants, 1):
            text += f"{i}. {p['full_name']} (@{p['username'] or 'нет'})\n"
    else:
        text += "  Пока нет записей"

    from keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin_ev:{event_id}")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


# ── Проверка ДЗ ──

@router.callback_query(F.data == "admin_hw")
async def admin_hw_queue(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        return
    pending = await db.get_pending_homework()
    await callback.message.edit_text(
        f"📝 <b>Очередь ДЗ на проверку ({len(pending)})</b>",
        parse_mode="HTML",
        reply_markup=admin_hw_keyboard(pending),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_hw_review:"))
async def admin_hw_review(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        return
    hw_id = int(callback.data.split(":")[1])
    hw = await db.get_homework_by_id(hw_id)
    if not hw:
        await callback.answer("Не найдено", show_alert=True)
        return

    # Пересылаем вложение админу
    if hw["file_type"] == "photo":
        from aiogram.types import InputMediaPhoto
        await callback.message.answer_photo(
            hw["file_id"],
            caption=f"📝 <b>ДЗ от {hw.get('user_id', '?')}</b>",
            parse_mode="HTML",
        )
    else:
        await callback.message.answer_document(
            hw["file_id"],
            caption=f"📝 <b>ДЗ от {hw.get('user_id', '?')}</b>",
            parse_mode="HTML",
        )

    await callback.message.answer(
        f"📝 <b>Проверка ДЗ</b>\n\n"
        f"👤 Пользователь ID: {hw['user_id']}\n"
        f"📌 Мероприятие: {hw.get('event_title', '?')}\n"
        f"📅 Отправлено: {hw['submitted_at']}",
        parse_mode="HTML",
        reply_markup=admin_hw_review_keyboard(hw_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_hw_approve:"))
async def admin_hw_approve(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        return
    parts = callback.data.split(":")
    hw_id = int(parts[1])
    coins = int(parts[2])

    hw = await db.get_homework_by_id(hw_id)
    await db.review_homework(hw_id, "approved", "Одобрено", coins)
    await db.add_coins(hw["user_id"], coins)

    await callback.answer(f"✅ ДЗ одобрено! Начислено {coins} 🪙", show_alert=True)
    # Обновляем список
    pending = await db.get_pending_homework()
    await callback.message.edit_text(
        f"📝 <b>Очередь ДЗ ({len(pending)} на проверку)</b>",
        parse_mode="HTML",
        reply_markup=admin_hw_keyboard(pending),
    )


@router.callback_query(F.data.startswith("admin_hw_reject:"))
async def admin_hw_reject(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        return
    hw_id = int(callback.data.split(":")[1])
    await db.review_homework(hw_id, "rejected", "Требуется доработка", 0)

    await callback.answer("❌ ДЗ отклонено", show_alert=True)
    pending = await db.get_pending_homework()
    await callback.message.edit_text(
        f"📝 <b>Очередь ДЗ ({len(pending)} на проверку)</b>",
        parse_mode="HTML",
        reply_markup=admin_hw_keyboard(pending),
    )


# ── Экспорт пользователей ──

@router.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery, db, user):
    if not is_admin_user(user):
        return

    users = await db.get_all_users()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Username", "Имя", "Дата регистрации", "Роль", "Сберкоины"])
    for u in users:
        writer.writerow([u["id"], u["username"], u["full_name"], u["registered_at"], u["role"], u["sbercoins"]])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    file = BufferedInputFile(csv_bytes, filename="sberteen_users.csv")

    await callback.message.answer_document(file, caption="📥 Экспорт пользователей SberTeen")
    await callback.answer()


# ── Начисление сберкоинов ──

@router.callback_query(F.data == "admin_coins")
async def admin_coins_start(callback: CallbackQuery, db, user, state: FSMContext):
    if not is_admin_user(user):
        return
    users = await db.get_all_users()
    await callback.message.edit_text(
        "💰 <b>Выбери пользователя для начисления сберкоинов:</b>",
        parse_mode="HTML",
        reply_markup=admin_coins_keyboard(users),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_coin_user:"))
async def admin_coin_select_user(callback: CallbackQuery, db, user, state: FSMContext):
    if not is_admin_user(user):
        return
    user_id = int(callback.data.split(":")[1])
    target = await db.get_user(user_id)
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminState.coins_enter_amount)

    await callback.message.edit_text(
        f"💰 Начисление сберкоинов\n\n"
        f"👤 <b>{target['full_name']}</b>\n"
        f"💰 Текущий баланс: {target['sbercoins']}\n\n"
        f"Введи <b>количество сберкоинов</b> (отрицательное — штраф):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminState.coins_enter_amount)
async def admin_coin_process(message: Message, db, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи целое число:")
        return

    data = await state.get_data()
    target_id = data["target_user_id"]
    await db.add_coins(target_id, amount)
    target = await db.get_user(target_id)

    await state.clear()
    await message.answer(
        f"💰 <b>Начислено {'+' if amount >= 0 else ''}{amount} сберкоинов</b>\n\n"
        f"👤 {target['full_name']}\n"
        f"💰 Новый баланс: {target['sbercoins']}",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(),
    )
