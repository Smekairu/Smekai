"""Номера пользователей в общей базе.

Telegram  как есть, положительный id
MAX       минус id пользователя MAX, чтобы не пересечься с Telegram
сайт      от WEB_BASE и выше, аккаунт без мессенджера
"""
WEB_BASE = 9_000_000_000_000_000


def platform(uid):
    uid = int(uid)
    if uid >= WEB_BASE:
        return "web"
    return "max" if uid < 0 else "tg"


def from_max(max_user_id):
    return -int(max_user_id)


def to_max(uid):
    return -int(uid)
