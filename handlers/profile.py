from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards import profile_keyboard, back_to_profile_keyboard, my_events_keyboard

router = Router()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, db, user):
    if not user:
        await callback.answer("Сначала зарегистрируйся через /start", show_alert=True)
        return

    events = await db.get_user_events(user["id"])
    hw_items = await db.get_user_homework(user["id"])

    events_text = ""
    if events:
        for ev in events:
            icon = "🔵" if ev["event_type"] == "online" else "🟡"
            events_text += f"  {icon} {ev['date']} {ev['time']} — {ev['title']}\n"
    else:
        events_text = "  Пока нет записей\n"

    pending = sum(1 for h in hw_items if h["status"] == "pending")
    approved = sum(1 for h in hw_items if h["status"] == "approved")

    text = (
        f"👤 <b>{user['full_name']}</b>\n"
        f"💰 Сберкоины: <b>{user['sbercoins']}</b>\n\n"
        f"📋 <b>Мои мероприятия:</b>\n{events_text}\n"
        f"📝 <b>ДЗ:</b> отправлено {len(hw_items)}, "
        f"одобрено {approved}, на проверке {pending}"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=profile_keyboard())
    await callback.answer()


@router.callback_query(F.data == "my_events")
async def show_my_events(callback: CallbackQuery, db, user):
    if not user:
        await callback.answer("Сначала зарегистрируйся", show_alert=True)
        return

    events = await db.get_user_events(user["id"])

    if not events:
        text = "🟡 <b>Ты пока не записан ни на одно мероприятие</b>\n\nПерейди в расписание, чтобы записаться!"
    else:
        text = "📅 <b>Твои мероприятия:</b>\n\n"
        for ev in events:
            icon = "🔵" if ev["event_type"] == "online" else "🟡"
            label = "Онлайн" if ev["event_type"] == "online" else ev["location"]
            text += f"{icon} <b>{ev['title']}</b>\n📅 {ev['date']} {ev['time']} | {label}\n\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=my_events_keyboard())
    await callback.answer()


@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: CallbackQuery, db, user):
    if not user:
        await callback.answer("Сначала зарегистрируйся", show_alert=True)
        return

    leaders = await db.get_leaderboard()

    if not leaders:
        text = "🏆 <b>Рейтинг участников</b>\n\nПока никто не заработал сберкоины"
    else:
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        text = "🏆 <b>Рейтинг участников</b>\n\n"
        for i, leader in enumerate(leaders):
            medal = medals.get(i, f" {i + 1}.")
            marker = " 👈 Ты" if leader["full_name"] == user["full_name"] else ""
            text += f"{medal} {leader['full_name']} — {leader['sbercoins']} 🪙{marker}\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_profile_keyboard())
    await callback.answer()
