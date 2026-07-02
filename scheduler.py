import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot

from database import Database

logger = logging.getLogger(__name__)


async def check_and_send_notifications(bot: Bot, db: Database):
    now = datetime.now()
    today = now.date().isoformat()

    # Проверяем события, которые начнутся через 24 часа
    tomorrow = (now + timedelta(hours=24)).strftime("%H:%M")
    tomorrow_date = (now + timedelta(hours=24)).date().isoformat()
    await send_notifications_for_event(bot, db, tomorrow_date, tomorrow, "day")

    # Проверяем события, которые начнутся через 1 час
    in_one_hour = (now + timedelta(hours=1)).strftime("%H:%M")
    in_one_hour_date = now.date().isoformat()
    # Если час переходит на следующий день
    if now.hour == 23:
        in_one_hour_date = (now + timedelta(days=1)).date().isoformat()
    await send_notifications_for_event(bot, db, in_one_hour_date, in_one_hour, "hour")


async def send_notifications_for_event(
    bot: Bot, db: Database, event_date: str, event_time: str, notify_type: str
):
    events = await db.get_events_at_datetime(event_date, event_time)

    for event in events:
        participants = await db.get_event_participants(event["id"])

        for participant in participants:
            already_sent = await db.is_notification_sent(
                participant["id"], event["id"], notify_type
            )
            if already_sent:
                continue

            type_label = "завтра" if notify_type == "day" else "через час"
            icon = "🔵" if event["event_type"] == "online" else "🟡"
            location = "Онлайн" if event["event_type"] == "online" else event["location"]

            text = (
                f"🔔 <b>Напоминание!</b>\n\n"
                f"{icon} <b>{event['title']}</b>\n"
                f"📅 Начало {type_label}: {event['date']} в {event['time']}\n"
                f"📍 {location}"
            )

            try:
                await bot.send_message(participant["id"], text, parse_mode="HTML")
                await db.mark_notification_sent(
                    participant["id"], event["id"], notify_type
                )
                logger.info(
                    f"Sent {notify_type} notification to {participant['id']} "
                    f"for event {event['id']}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to send notification to {participant['id']}: {e}"
                )


async def notification_loop(bot: Bot, db: Database):
    logger.info("Notification scheduler started")
    while True:
        try:
            await check_and_send_notifications(bot, db)
        except Exception as e:
            logger.error(f"Notification check error: {e}")
        # Проверяем каждые 5 минут
        await asyncio.sleep(300)
