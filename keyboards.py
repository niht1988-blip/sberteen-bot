from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📅 Расписание", callback_data="schedule"),
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
        ],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def schedule_keyboard(page: int, total_pages: int, events: list[dict]) -> InlineKeyboardMarkup:
    buttons = []

    for ev in events:
        icon = "🔵" if ev["event_type"] == "online" else "🟡"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {ev['title']} — {ev['date']} {ev['time']}",
            callback_data=f"sched_show:{ev['id']}",
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"sched_page:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"sched_page:{page + 1}"))
    buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def event_keyboard(event_id: int, is_registered: bool) -> InlineKeyboardMarkup:
    if is_registered:
        btn = InlineKeyboardButton(
            text="❌ Отменить запись", callback_data=f"sched_unregister:{event_id}"
        )
    else:
        btn = InlineKeyboardButton(
            text="✅ Записаться", callback_data=f"sched_register:{event_id}"
        )
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn],
        [InlineKeyboardButton(text="◀️ К расписанию", callback_data="schedule")],
    ])


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Сдать ДЗ", callback_data="hw_submit")],
        [InlineKeyboardButton(text="📋 Мои задания", callback_data="hw_list")],
        [InlineKeyboardButton(text="📅 Мои мероприятия", callback_data="my_events")],
        [InlineKeyboardButton(text="🏆 Рейтинг участников", callback_data="leaderboard")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])


def back_to_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")],
    ])


def my_events_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")],
    ])


def hw_select_event_keyboard(events: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"📋 {e['title']} ({e['date']})",
            callback_data=f"hw_select:{e['id']}",
        )]
        for e in events
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="profile")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def hw_list_keyboard(hw_items: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for hw in hw_items:
        status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(hw["status"], "?")
        buttons.append([InlineKeyboardButton(
            text=f"{status_icon} {hw['event_title']}",
            callback_data=f"hw_detail:{hw['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="profile")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Admin keyboards ──

def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Расписание", callback_data="admin_schedule")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📝 Проверка ДЗ", callback_data="admin_hw")],
        [InlineKeyboardButton(text="💰 Начислить коины", callback_data="admin_coins")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])


def admin_schedule_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить мероприятие", callback_data="admin_add_event")],
        [InlineKeyboardButton(text="📋 Список мероприятий", callback_data="admin_list_events")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
    ])


def admin_event_actions(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit:{event_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete:{event_id}"),
        ],
        [InlineKeyboardButton(text="👥 Участники", callback_data=f"admin_participants:{event_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_schedule")],
    ])


def admin_hw_keyboard(hw_items: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for hw in hw_items:
        buttons.append([InlineKeyboardButton(
            text=f"⏳ {hw['full_name']} — {hw['event_title']}",
            callback_data=f"admin_hw_review:{hw['id']}",
        )])
    if not hw_items:
        buttons.append([InlineKeyboardButton(text="Нет заданий на проверке", callback_data="noop")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_hw_review_keyboard(hw_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять (+10 🪙)", callback_data=f"admin_hw_approve:{hw_id}:10"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_hw_reject:{hw_id}"),
        ],
        [
            InlineKeyboardButton(text="✅ Принять (+20 🪙)", callback_data=f"admin_hw_approve:{hw_id}:20"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="admin_hw"),
        ],
    ])


def admin_users_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Экспорт CSV", callback_data="admin_export")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
    ])


def admin_coins_keyboard(users: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for u in users[:10]:
        buttons.append([InlineKeyboardButton(
            text=f"👤 {u['full_name']} ({u['sbercoins']} 🪙)",
            callback_data=f"admin_coin_user:{u['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
