from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from keyboards import schedule_keyboard, event_keyboard, main_menu_keyboard

router = Router()
EVENTS_PER_PAGE = 5


def format_event(event: dict) -> str:
    type_icon = "🔵" if event["event_type"] == "online" else "🟡"
    type_label = "Онлайн" if event["event_type"] == "online" else event["location"]
    return (
        f"{type_icon} <b>{event['title']}</b>\n"
        f"📅 {event['date']} в {event['time']}\n"
        f"📍 {type_label}\n"
    )


async def show_schedule(callback: CallbackQuery, db, page: int = 0):
    total = await db.count_events()
    total_pages = max(1, (total + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    events = await db.get_events_page(page, EVENTS_PER_PAGE)

    if not events:
        text = "🟡 <b>Расписание пусто</b>\n\nМероприятия скоро появятся!"
    else:
        text = "📅 <b>Расписание SberTeen — Июль 2026</b>\n\n"
        for ev in events:
            text += format_event(ev) + "\n"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=schedule_keyboard(page, total_pages, events),
    )
    await callback.answer()


@router.callback_query(F.data == "schedule")
async def show_schedule_page(callback: CallbackQuery, db, user):
    if not user:
        await callback.answer("Сначала зарегистрируйся через /start", show_alert=True)
        return
    await show_schedule(callback, db, page=0)


@router.callback_query(F.data.startswith("sched_page:"))
async def paginate_schedule(callback: CallbackQuery, db):
    page = int(callback.data.split(":")[1])
    await show_schedule(callback, db, page)


@router.callback_query(F.data.startswith("sched_show:"))
async def show_event_detail(callback: CallbackQuery, db, user):
    event_id = int(callback.data.split(":")[1])
    event = await db.get_event(event_id)
    if not event:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    is_registered = await db.is_registered(user["id"], event_id)

    type_icon = "🔵" if event["event_type"] == "online" else "🟡"
    type_label = "Онлайн" if event["event_type"] == "online" else event["location"]
    status = "✅ Ты записан" if is_registered else "ℹ️ Ты не записан"

    text = (
        f"{type_icon} <b>{event['title']}</b>\n\n"
        f"📅 Дата: {event['date']}\n"
        f"⏰ Время: {event['time']}\n"
        f"📍 Место: {type_label}\n"
    )
    if event["description"]:
        text += f"\n📝 {event['description']}\n"
    text += f"\n{status}"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=event_keyboard(event_id, is_registered),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sched_register:"))
async def register_event(callback: CallbackQuery, db, user):
    event_id = int(callback.data.split(":")[1])
    success = await db.register_for_event(user["id"], event_id)
    event = await db.get_event(event_id)

    if success:
        await callback.answer(f"✅ Записался на «{event['title']}»!", show_alert=True)
    else:
        await callback.answer("Ты уже записан на это мероприятие", show_alert=True)
        return

    is_registered = True
    type_icon = "🔵" if event["event_type"] == "online" else "🟡"
    type_label = "Онлайн" if event["event_type"] == "online" else event["location"]

    text = (
        f"{type_icon} <b>{event['title']}</b>\n\n"
        f"📅 {event['date']} в {event['time']}\n"
        f"📍 {type_label}\n\n"
        f"✅ Ты записан!"
    )
    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=event_keyboard(event_id, is_registered)
    )


@router.callback_query(F.data.startswith("sched_unregister:"))
async def unregister_event(callback: CallbackQuery, db, user):
    event_id = int(callback.data.split(":")[1])
    success = await db.unregister_from_event(user["id"], event_id)
    event = await db.get_event(event_id)

    if success:
        await callback.answer(f"❌ Запись на «{event['title']}» отменена", show_alert=True)
    else:
        await callback.answer("Ты не был записан", show_alert=True)
        return

    is_registered = False
    type_icon = "🔵" if event["event_type"] == "online" else "🟡"
    type_label = "Онлайн" if event["event_type"] == "online" else event["location"]

    text = (
        f"{type_icon} <b>{event['title']}</b>\n\n"
        f"📅 {event['date']} в {event['time']}\n"
        f"📍 {type_label}\n\n"
        f"ℹ️ Ты не записан"
    )
    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=event_keyboard(event_id, is_registered)
    )


# ── Показ карточки из списка ──

@router.callback_query(F.data.startswith("sched_detail:"))
async def sched_detail(callback: CallbackQuery, db, user):
    """Показать карточку мероприятия (переход из расписания)."""
    if not user:
        await callback.answer("Сначала зарегистрируйся", show_alert=True)
        return
    event_id = int(callback.data.split(":")[1])
    await show_event_detail_inner(callback, db, user, event_id)


async def show_event_detail_inner(callback, db, user, event_id):
    event = await db.get_event(event_id)
    if not event:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return
    is_registered = await db.is_registered(user["id"], event_id)
    type_icon = "🔵" if event["event_type"] == "online" else "🟡"
    type_label = "Онлайн" if event["event_type"] == "online" else event["location"]
    status = "✅ Ты записан" if is_registered else "ℹ️ Ты не записан"
    text = (
        f"{type_icon} <b>{event['title']}</b>\n\n"
        f"📅 Дата: {event['date']}\n"
        f"⏰ Время: {event['time']}\n"
        f"📍 Место: {type_label}\n"
    )
    if event["description"]:
        text += f"\n📝 {event['description']}\n"
    text += f"\n{status}"
    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=event_keyboard(event_id, is_registered)
    )
    await callback.answer()
