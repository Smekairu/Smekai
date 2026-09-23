"""Анимированный Мыслик в Telegram: видеостикеры и анимации.

Файлы лежат в assets/anim рядом с репозиторием:
  myslik-<настроение>.webm  видеостикер с прозрачностью, 512x512
  myslik-<настроение>.mp4   та же анимация на жёлтом фоне, если стикер не прошёл
  myslik-<настроение>.gif   для MAX и превью

После первой отправки Telegram выдаёт file_id, он запоминается в базе,
и дальше файл не грузится заново.
"""
import logging, os
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile

import db

log = logging.getLogger("stickers")
ANIM = Path(os.environ.get("ANIM_DIR") or Path(__file__).resolve().parent.parent / "assets" / "anim")
MOODS = ("wave", "yay", "party", "think", "sad", "angry", "surprised", "sleepy", "love", "idle")


def path(mood, ext):
    p = ANIM / f"myslik-{mood}.{ext}"
    return p if p.exists() else None


async def send_mood(bot: Bot, chat_id: int, mood: str):
    """Присылает стикер с нужным настроением. Тихо пропускает, если файлов нет."""
    if mood not in MOODS:
        return
    key = f"tg:{mood}"
    cached = db.file_id_get(key)
    try:
        if cached:
            kind, fid = cached.split("|", 1)
            if kind == "sticker":
                await bot.send_sticker(chat_id, fid)
            else:
                await bot.send_animation(chat_id, fid)
            return
        webm = path(mood, "webm")
        if webm:
            msg = await bot.send_sticker(chat_id, FSInputFile(webm))
            db.file_id_set(key, "sticker|" + msg.sticker.file_id)
            return
        mp4 = path(mood, "mp4")
        if mp4:
            msg = await bot.send_animation(chat_id, FSInputFile(mp4))
            db.file_id_set(key, "animation|" + msg.animation.file_id)
    except Exception as e:
        log.warning("стикер %s не отправлен: %s", mood, e)
        db.file_id_del(key)
