"""Публикует посты из папки posts/ в Telegram и MAX, когда подошло время.

Формат файла поста: posts/ГГГГ-ММ-ДД-ЧЧММ-название.md
Верх файла (между строками ---):
  time: 2026-09-23 10:00        время по Москве
  channels: telegram, max       куда отправлять
  button: Пройти викторину      текст кнопки (необязательно)
  link: quiz                    ссылка кнопки: quiz, boosty или полный адрес
  image: assets/myslik-navy.png картинка (необязательно)
Ниже: текст поста. Разметка Telegram HTML: <b>жирный</b>, <i>курсив</i>, <a href="...">ссылка</a>.
"""
import json, os, re, sys, urllib.request, urllib.parse, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
STATE = ROOT / "state" / "published.json"
MSK = timezone(timedelta(hours=3))
LINKS = {
    "quiz": "https://smekairu.github.io/Smekai/",
    "boosty": "https://boosty.to/smekai",
    "telegram": "https://t.me/smekai_ru",
}

def parse(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        raise ValueError(f"{path.name}: нет блока настроек между ---")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    meta["text"] = m.group(2).strip()
    meta["time"] = datetime.strptime(meta["time"], "%Y-%m-%d %H:%M").replace(tzinfo=MSK)
    meta["channels"] = [c.strip() for c in meta.get("channels", "telegram").split(",") if c.strip()]
    if meta.get("link"):
        meta["link"] = LINKS.get(meta["link"], meta["link"])
    return meta

def http(url, data=None, headers=None, files=None):
    headers = dict(headers or {})
    if files:
        boundary = uuid.uuid4().hex
        body = b""
        for k, v in (data or {}).items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        for k, (fname, content) in files.items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode() + content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=headers, method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")

def send_telegram(p):
    token, chat = os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHANNEL") or "@smekai_ru"
    if not token:
        print("Telegram: нет TG_BOT_TOKEN, пропускаю"); return False
    base = f"https://api.telegram.org/bot{token}"
    markup = None
    if p.get("button") and p.get("link"):
        markup = json.dumps({"inline_keyboard": [[{"text": p["button"], "url": p["link"]}]]})
    if p.get("image"):
        data = {"chat_id": chat, "caption": p["text"], "parse_mode": "HTML"}
        if markup: data["reply_markup"] = markup
        img = ROOT / p["image"]
        r = http(base + "/sendPhoto", data, files={"photo": (img.name, img.read_bytes())})
    else:
        data = {"chat_id": chat, "text": p["text"], "parse_mode": "HTML", "disable_web_page_preview": False}
        if markup: data["reply_markup"] = json.loads(markup)
        r = http(base + "/sendMessage", data)
    ok = bool(r.get("ok")); print("Telegram:", "отправлено" if ok else r)
    return (r.get("result") or {}).get("message_id") if ok else None

def send_max(p):
    token, chat = os.environ.get("MAX_BOT_TOKEN"), os.environ.get("MAX_CHAT_ID")
    if not token or not chat:
        print("MAX: бот ещё не подключён, пропускаю"); return False
    base = os.environ.get("MAX_API_BASE", "https://platform-api.max.ru")
    body = {"text": p["text"], "format": "html"}
    if p.get("button") and p.get("link"):
        body["attachments"] = [{"type": "inline_keyboard", "payload": {"buttons": [[{"type": "link", "text": p["button"], "url": p["link"]}]]}}]
    r = http(f"{base}/messages?chat_id={urllib.parse.quote(chat)}", body, headers={"Authorization": token})
    print("MAX: отправлено"); return True

def check_telegram():
    """Проверка: токен рабочий, бот администратор канала и может публиковать."""
    token, chat = os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHANNEL") or "@smekai_ru"
    if not token:
        print("ПРОВЕРКА: нет секрета TG_BOT_TOKEN"); return False
    try:
        me = http(f"https://api.telegram.org/bot{token}/getMe")["result"]
        print("ПРОВЕРКА: бот", "@" + me["username"])
        m = http(f"https://api.telegram.org/bot{token}/getChatMember?chat_id={urllib.parse.quote(chat)}&user_id={me['id']}")["result"]
    except Exception as e:
        print("ПРОВЕРКА: ошибка Telegram:", e); return False
    ok = m.get("status") == "administrator" and m.get("can_post_messages", False)
    print("ПРОВЕРКА: в канале", chat, "статус", m.get("status"), "может публиковать:", m.get("can_post_messages"))
    return ok

def main():
    if not check_telegram():
        print("Проверка не пройдена, публикация остановлена"); sys.exit(1)
    state = json.loads(STATE.read_text(encoding="utf-8"))
    done = set(state.get("published", []))
    msgs = dict(state.get("messages", {}))
    now = datetime.now(MSK)
    errors = 0
    for path in sorted(POSTS.glob("*.md")):
        if path.name in done: continue
        try:
            p = parse(path)
        except Exception as e:
            print("Ошибка в файле:", e); errors += 1; continue
        if p["time"] > now: continue
        print(f"Публикую {path.name}")
        sent = False
        try:
            if "telegram" in p["channels"]:
                mid = send_telegram(p)
                if mid:
                    sent = True
                    msgs[path.name] = mid
            if "max" in p["channels"]: sent = send_max(p) or sent
        except Exception as e:
            print("Ошибка отправки:", e); errors += 1; continue
        if sent:
            done.add(path.name)
    STATE.write_text(json.dumps({"published": sorted(done), "messages": msgs}, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
