"""Ставит название и логотип «Мыслик» каналам в Telegram и MAX.

Запуск: GitHub -> Actions -> «Обновить оформление каналов» -> Run workflow.
Telegram: бот должен быть администратором канала с правом «Изменение профиля канала».
MAX: бот должен быть администратором канала.
"""
import json, os, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "brand" / "logo-myslik.png"
LOGO_URL = "https://myslik.ru/assets/brand/logo-myslik.png"
TITLE = os.environ.get("BRAND_TITLE", "Мыслик")


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
        print("Telegram: нет токена"); return False
    success = True
    for chat in (os.environ.get("TG_CHANNEL") or "@smekai_ru", os.environ.get("TG_CHANNEL_CLOSED", "")):
        if not chat:
            continue
        title_res, title_err = call(f"https://api.telegram.org/bot{token}/setChatTitle",
                                    {"chat_id": chat, "title": TITLE})
        title_ok = bool(title_res and title_res.get("ok"))
        res, err = call(f"https://api.telegram.org/bot{token}/setChatPhoto", {"chat_id": chat},
                        files={"photo": (LOGO.name, LOGO.read_bytes())})
        logo_ok = bool(res and res.get("ok"))
        print(f"Telegram {chat}: название —",
              "поставлено" if title_ok else f"не получилось: {title_err or title_res}")
        print(f"Telegram {chat}: логотип —",
              "поставлен" if logo_ok else f"не получилось: {err or res}")
        success = success and title_ok and logo_ok
        if not title_ok or not logo_ok:
            print("   Проверьте, что у бота в канале есть право «Изменение профиля канала».")
    return success


def max_channels():
    token = os.environ.get("MAX_BOT_TOKEN", "")
    base = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")
    if not token:
        print("MAX: нет токена"); return False
    success = True
    for chat in (os.environ.get("MAX_CHAT_ID", ""), os.environ.get("MAX_CHAT_ID_CLOSED", "")):
        if not chat:
            continue
        res, err = call(f"{base}/chats/{urllib.parse.quote(chat)}",
                        {"title": TITLE, "icon": {"url": LOGO_URL}},
                        headers={"Authorization": token}, method="PATCH")
        ok = res is not None
        print(f"MAX {chat}:", "название и логотип поставлены" if ok else f"не получилось: {err}")
        success = success and ok
    return success


if __name__ == "__main__":
    raise SystemExit(0 if telegram() and max_channels() else 1)
