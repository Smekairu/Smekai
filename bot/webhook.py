"""Приём уведомлений об оплате. Открывает подписку и присылает ссылку в закрытый канал.

Запускается рядом с ботом: python webhook.py
Адрес для настройки в Tribute: https://ваш-домен/pay

Формат уведомления у площадок разный, поэтому берём первое подходящее поле:
telegram_user_id, user_id, telegram_id или subscriber_id.
"""
import json, logging, os

from aiohttp import web
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

import db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pay")

SECRET = os.environ.get("PAY_WEBHOOK_SECRET", "")
DAYS = int(os.environ.get("SUB_DAYS", "30"))
CLOSED_CHANNEL = os.environ.get("TG_CHANNEL_CLOSED", "")
bot = Bot(os.environ["TG_BOT_TOKEN"], default=DefaultBotProperties(parse_mode="HTML"))


def find_user_id(data):
    for key in ("telegram_user_id", "user_id", "telegram_id", "subscriber_id"):
        v = data.get(key)
        if v:
            try:
                return int(v)
            except (TypeError, ValueError):
                pass
    payload = data.get("payload") or data.get("data") or {}
    if isinstance(payload, dict):
        return find_user_id(payload)
    return None


async def handle(request: web.Request):
    if SECRET:
        got = request.headers.get("X-Api-Key") or request.query.get("secret") or ""
        if got != SECRET:
            log.warning("отклонено: неверный ключ")
            return web.json_response({"ok": False}, status=403)
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"ok": False, "error": "не json"}, status=400)
    log.info("уведомление: %s", json.dumps(data, ensure_ascii=False)[:500])

    uid = find_user_id(data)
    if not uid:
        log.warning("не нашёл telegram id в уведомлении")
        return web.json_response({"ok": True, "note": "нет telegram id"})

    amount = float(data.get("amount") or 0)
    until = db.grant(uid, DAYS, amount=amount, source="tribute")
    text = [f"Оплата получена. Подписка активна до {until}.", ""]
    if CLOSED_CHANNEL:
        try:
            link = await bot.create_chat_invite_link(CLOSED_CHANNEL, member_limit=1,
                                                     name=f"Подписка {uid}")
            text.append("Ссылка в закрытый канал с заданиями, она одноразовая:")
            text.append(link.invite_link)
        except Exception as e:
            log.error("не смог создать приглашение: %s", e)
    text.append("")
    text.append("Теперь доступно 30 заданий в день и разбор домашки. Напишите «Задание».")
    try:
        await bot.send_message(uid, "\n".join(text))
    except Exception as e:
        log.error("не смог написать пользователю %s: %s", uid, e)
    return web.json_response({"ok": True})


async def health(request):
    return web.json_response({"ok": True})


def main():
    db.init()
    app = web.Application()
    app.router.add_post("/pay", handle)
    app.router.add_get("/health", health)
    web.run_app(app, port=int(os.environ.get("PORT", "8080")))


if __name__ == "__main__":
    main()
