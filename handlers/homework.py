from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards import (
    profile_keyboard,
    back_to_profile_keyboard,
    hw_select_event_keyboard,
    hw_list_keyboard,
)

router = Router()


class HWState(StatesGroup):
    waiting_for_event = State()
    waiting_for_file = State()


@router.callback_query(F.data == "hw_submit")
async def hw_submit_start(callback: CallbackQuery, db, user, state: FSMContext):
    if not user:
        await callback.answer("Сначала зарегистрируйся", show_alert=True)
        return

    events = await db.get_user_events(user["id"])
    if not events:
        await callback.answer("Сначала запишись на мероприятие", show_alert=True)
        return

    await state.set_state(HWState.waiting_for_event)
    await callback.message.edit_text(
        "📝 <b>Выбери мероприятие, на которое сдаёшь ДЗ:</b>",
        parse_mode="HTML",
        reply_markup=hw_select_event_keyboard(events),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hw_select:"), HWState.waiting_for_event)
async def hw_select_event(callback: CallbackQuery, db, state: FSMContext):
    event_id = int(callback.data.split(":")[1])
    event = await db.get_event(event_id)
    await state.update_data(event_id=event_id)
    await state.set_state(HWState.waiting_for_file)

    await callback.message.edit_text(
        f"📝 <b>Сдаём ДЗ на «{event['title']}»</b>\n\n"
        f"📸 Отправь <b>фото</b> или <b>документ</b> с выполненным заданием:",
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard(),
    )
    await callback.answer()


@router.message(HWState.waiting_for_file, F.photo | F.document)
async def hw_receive_file(message: Message, db, state: FSMContext):
    data = await state.get_data()
    event_id = data["event_id"]

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    else:
        file_id = message.document.file_id
        file_type = "document"

    await db.submit_homework(message.from_user.id, event_id, file_id, file_type)

    event = await db.get_event(event_id)
    await message.answer(
        f"✅ <b>ДЗ на «{event['title']}» отправлено!</b>\n\n"
        f"⏳ Ожидай проверки администратором.\n"
        f"💰 После одобрения сберкоины будут начислены.",
        parse_mode="HTML",
        reply_markup=profile_keyboard(),
    )
    await state.clear()


@router.message(HWState.waiting_for_file)
async def hw_wrong_type(message: Message):
    await message.answer("❌ Отправь именно <b>фото</b> или <b>документ</b>.", parse_mode="HTML")


@router.callback_query(F.data == "hw_list")
async def hw_list(callback: CallbackQuery, db, user, state: FSMContext):
    await state.clear()
    if not user:
        await callback.answer("Сначала зарегистрируйся", show_alert=True)
        return

    hw_items = await db.get_user_homework(user["id"])

    if not hw_items:
        text = "📝 <b>У тебя пока нет отправленных заданий</b>"
    else:
        text = "📝 <b>Мои задания:</b>\n\n"
        for hw in hw_items:
            status = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(hw["status"], "?")
            coins = f" (+{hw['coins_awarded']} 🪙)" if hw["coins_awarded"] else ""
            text += f"{status} {hw['event_title']}{coins}\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=hw_list_keyboard(hw_items))
    await callback.answer()


@router.callback_query(F.data.startswith("hw_detail:"))
async def hw_detail(callback: CallbackQuery, db, user):
    hw_id = int(callback.data.split(":")[1])
    hw = await db.get_homework_by_id(hw_id)
    if not hw or hw["user_id"] != user["id"]:
        await callback.answer("Не найдено", show_alert=True)
        return

    status = {"pending": "⏳ На проверке", "approved": "✅ Принято", "rejected": "❌ Отклонено"}.get(
        hw["status"], hw["status"]
    )
    coins = f"\n💰 Начислено: {hw['coins_awarded']} сберкоинов" if hw["coins_awarded"] else ""
    comment = f"\n💬 Комментарий: {hw['comment']}" if hw["comment"] else ""

    text = (
        f"📝 <b>ДЗ: {hw['event_title']}</b>\n\n"
        f"📊 Статус: {status}{coins}{comment}"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_profile_keyboard())
    await callback.answer()
