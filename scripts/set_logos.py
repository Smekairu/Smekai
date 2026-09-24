"""Ставит логотип Смекай аватаркой каналов в Telegram и MAX.

Запуск: GitHub -> Actions -> «Обновить логотипы» -> Run workflow.
Telegram: бот должен быть администратором канала с правом «Изменение профиля канала».
MAX: бот должен быть администратором канала.
"""
import json, os, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "brand" / "logo-smekai.png"
LOGO_URL = "https://smekairu.github.io/Smekai/assets/brand/logo-smekai.png"


def call(url, data=None, headers=None, files=None, method=None):
    headers = dict(headers or {})
    body = None
    if files:
        b = uuid.uuid4().hex
        body = b""
        for k, v in (data or {}).items():
            body += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        for k, (fn, content) in files.items():
            body += (f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fn}\"\r\n"
                     "Content-Type: image/png\r\n\r\n").encode() + content + b"\r\n"
        body += f"--{b}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={b}"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method or ("POST" if body else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or "{}"), None
    except urllib.error.HTTPError as e:
        return None, f"{e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return None, str(e)


def telegram():
    token = os.environ.get("TG_BOT_TOKEN", "")
    if not token:
        print("Telegram: нет токена"); return
    for chat in (os.environ.get("TG_CHANNEL") or "@smekai_ru", os.environ.get("TG_CHANNEL_CLOSED", "")):
        if not chat:
            continue
        res, err = call(f"https://api.telegram.org/bot{token}/setChatPhoto", {"chat_id": chat},
                        files={"photo": (LOGO.name, LOGO.read_bytes())})
        ok = res and res.get("ok")
        print(f"Telegram {chat}:", "логотип поставлен" if ok else f"не получилось: {err or res}")
        if not ok:
            print("   Проверьте, что у бота в канале есть право «Изменение профиля канала».")


def max_channels():
    token = os.environ.get("MAX_BOT_TOKEN", "")
    base = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")
    if not token:
        print("MAX: нет токена"); return
    for chat in (os.environ.get("MAX_CHAT_ID", ""), os.environ.get("MAX_CHAT_ID_CLOSED", "")):
        if not chat:
            continue
        res, err = call(f"{base}/chats/{urllib.parse.quote(chat)}", {"icon": {"url": LOGO_URL}},
                        headers={"Authorization": token}, method="PATCH")
        print(f"MAX {chat}:", "логотип поставлен" if res is not None else f"не получилось: {err}")


if __name__ == "__main__":
    telegram()
    max_channels()
