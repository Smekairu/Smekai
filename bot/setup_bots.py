"""Настраивает ботов в Telegram и MAX одной командой: имя, описание, команды, аватар в MAX.

Запуск: GitHub -> Actions -> «Настроить ботов» -> Run workflow,
или на сервере: set -a; . ./.env; set +a; python setup_bots.py

Токены берутся из TG_BOT_TOKEN и MAX_BOT_TOKEN. Если какого-то нет, эта часть пропускается.
Скрипт не падает, а печатает, что получилось и что нет.

Чего скрипт не может (делается руками один раз):
  Telegram: аватар бота (BotFather -> /setuserpic, файл assets/avatar-myslik.png).
  MAX: всё делается через API, руками ничего не нужно.
"""
import json, os, ssl, sys, urllib.parse, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import COMMANDS, DESCRIPTION, SHORT_DESCRIPTION

NAME = os.environ.get("BOT_NAME", "Мыслик · Смекай")
AVATAR_URL = os.environ.get("BOT_AVATAR_URL", "https://smekairu.github.io/Smekai/assets/avatar-myslik.png")
CTX = ssl.create_default_context()


def http(url, body=None, headers=None, method=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
            return json.loads(r.read().decode() or "{}"), None
    except urllib.error.HTTPError as e:
        return None, f"код {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return None, str(e)


def telegram():
    token = os.environ.get("TG_BOT_TOKEN", "").strip()
    if not token:
        print("Telegram: TG_BOT_TOKEN не задан, пропускаю."); return
    api = f"https://api.telegram.org/bot{token}/"
    me, err = http(api + "getMe")
    if err:
        print("Telegram: токен не принят:", err); return
    print("Telegram: бот @%s" % me["result"]["username"])
    steps = [
        ("setMyCommands", {"commands": [{"command": c, "description": d} for c, d in COMMANDS]}),
        ("setMyDescription", {"description": DESCRIPTION}),
        ("setMyShortDescription", {"short_description": SHORT_DESCRIPTION}),
        ("setMyName", {"name": NAME}),
        ("setChatMenuButton", {"menu_button": {"type": "commands"}}),
    ]
    for method, body in steps:
        res, err = http(api + method, body)
        print("  ", method, "ок" if res and res.get("ok") else f"не удалось: {err or res}")
    print("   аватар: BotFather -> /setuserpic -> файл assets/avatar-myslik.png (через API нельзя)")


def max_bot():
    token = os.environ.get("MAX_BOT_TOKEN", "").strip()
    if not token:
        print("MAX: MAX_BOT_TOKEN не задан, пропускаю."); return
    base = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")
    h = {"Authorization": token}
    me, err = http(base + "/me", headers=h)
    if err:
        print("MAX: токен не принят:", err); return
    print("MAX: бот %s (@%s), user_id %s" % (me.get("name"), me.get("username"), me.get("user_id")))
    commands = [{"name": c, "description": d} for c, d in COMMANDS]
    body = {"name": NAME, "description": DESCRIPTION, "commands": commands, "photo": {"url": AVATAR_URL}}
    res, err = http(base + "/me", body, headers=h, method="PATCH")
    if err:
        print("   PATCH /me целиком не прошёл:", err)
        for part in ({"name": NAME}, {"description": DESCRIPTION}, {"commands": commands}, {"photo": {"url": AVATAR_URL}}):
            res, err = http(base + "/me", part, headers=h, method="PATCH")
            print("   ", list(part)[0], "ок" if not err else f"не удалось: {err}")
        res, err = http(base + "/me/commands", {"commands": commands}, headers=h, method="PATCH")
        print("    команды через /me/commands:", "ок" if not err else f"не удалось: {err}")
    else:
        print("   имя, описание, команды и аватар записаны")
    me, err = http(base + "/me", headers=h)
    if me:
        print("   сейчас:", me.get("name"), "| команд:", len(me.get("commands") or []),
              "| описание:", (me.get("description") or "")[:60])


if __name__ == "__main__":
    telegram()
    print()
    max_bot()
