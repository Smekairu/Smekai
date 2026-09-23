"""Публикует посты из папки posts/ в Telegram и MAX, когда подошло время.

Формат файла поста: posts/ГГГГ-ММ-ДД-ЧЧММ-название.md
Верх файла (между строками ---):
  time: 2026-09-23 10:00        время по Москве
  channels: telegram, max       куда отправлять
  button: Пройти викторину      текст кнопки (необязательно)
  link: quiz                    ссылка кнопки: quiz, boosty или полный адрес
  image: assets/myslik-navy.png картинка (необязательно)
  animation: assets/anim/myslik-wave.mp4  анимация Мыслика (необязательно, для MAX берётся .mp4)
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
    "quiz": "https://smekairu.github.io/Smekai/viktorina/",
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

def tg_chat(p):
    """Открытый канал по умолчанию, закрытый если в посте указано channel: closed."""
    if str(p.get("channel", "")).strip().lower() in ("closed", "закрытый"):
        return os.environ.get("TG_CHANNEL_CLOSED") or ""
    return os.environ.get("TG_CHANNEL") or "@smekai_ru"

def send_telegram(p):
    token, chat = os.environ.get("TG_BOT_TOKEN"), tg_chat(p)
    if not chat:
        print("Telegram: не задан канал для этого поста, пропускаю"); return None
    if not token:
        print("Telegram: нет TG_BOT_TOKEN, пропускаю"); return False
    base = f"https://api.telegram.org/bot{token}"
    markup = None
    if p.get("button") and p.get("link"):
        markup = json.dumps({"inline_keyboard": [[{"text": p["button"], "url": p["link"]}]]})
    if p.get("animation"):
        data = {"chat_id": chat, "caption": p["text"], "parse_mode": "HTML"}
        if markup: data["reply_markup"] = markup
        anim = ROOT / p["animation"]
        r = http(base + "/sendAnimation", data, files={"animation": (anim.name, anim.read_bytes())})
    elif p.get("image"):
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

def max_chat(p):
    """Открытый канал MAX по умолчанию, закрытый если в посте указано channel: closed."""
    if str(p.get("channel", "")).strip().lower() in ("closed", "закрытый"):
        return os.environ.get("MAX_CHAT_ID_CLOSED") or ""
    return os.environ.get("MAX_CHAT_ID") or ""

SPOILER = re.compile(r"\s*Ответы:\s*<tg-spoiler>(.*?)</tg-spoiler>\s*", re.S)
PENDING = ROOT / "state" / "max_pending.json"
ANSWER_DELAY_MIN = 60

def split_answers(text):
    """Отделяет ответы от задания. В MAX нет скрытого текста, поэтому ответы уходят позже."""
    m = SPOILER.search(text)
    if not m:
        return text.replace("<tg-spoiler>", "").replace("</tg-spoiler>", ""), ""
    body = SPOILER.sub("\n", text).strip()
    return body, m.group(1).strip()

def pending_read():
    if PENDING.exists():
        return json.loads(PENDING.read_text(encoding="utf-8"))
    return []

def pending_write(items):
    PENDING.parent.mkdir(exist_ok=True)
    PENDING.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

def max_upload(kind, path):
    """Загружает файл в MAX. kind: image или video. Возвращает вложение для сообщения или None."""
    token = os.environ.get("MAX_BOT_TOKEN")
    base = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")
    try:
        up = http(f"{base}/uploads?type={kind}", {}, headers={"Authorization": token})
        url = up.get("url")
        if not url:
            print("MAX: не дали адрес загрузки:", up); return None
        res = http(url, {}, files={"data": (Path(path).name, Path(path).read_bytes())})
        if kind == "image":
            photos = res.get("photos") or {}
            tok = next((v.get("token") for v in photos.values() if isinstance(v, dict)), None) or res.get("token")
        else:
            tok = res.get("token") or up.get("token")
        if not tok:
            print("MAX: загрузка без токена:", res); return None
        return {"type": kind, "payload": {"token": tok}}
    except Exception as e:
        detail = e.read().decode() if hasattr(e, "read") else str(e)
        print("MAX: загрузка не удалась:", detail[:200]); return None


def max_send_text(chat, text, markup=None, media=None):
    token = os.environ.get("MAX_BOT_TOKEN")
    base = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")
    body = {"text": text, "format": "html"}
    att = []
    if media: att.append(media)
    if markup: att.append(markup)
    if att: body["attachments"] = att
    import time
    for attempt in range(4):
        try:
            http(f"{base}/messages?chat_id={urllib.parse.quote(str(chat))}", body, headers={"Authorization": token})
            return
        except urllib.error.HTTPError as e:
            detail = e.read().decode()
            if "not.ready" in detail and attempt < 3:
                time.sleep(2); continue      # видео ещё обрабатывается
            raise urllib.error.HTTPError(e.url, e.code, detail, e.hdrs, None)

def send_max_pending():
    """Отправляет ответы, у которых прошёл час после задания."""
    items, left, now = pending_read(), [], datetime.now(MSK)
    for it in items:
        due = datetime.fromisoformat(it["due"])
        if due > now:
            left.append(it); continue
        try:
            max_send_text(it["chat"], "<b>Ответы к заданиям</b>\n\n" + it["text"])
            print("MAX: отправлены ответы к", it.get("post"))
        except Exception as e:
            detail = e.read().decode() if hasattr(e, "read") else str(e)
            print("MAX: ответы не ушли:", detail); left.append(it)
    if items:
        pending_write(left)

def send_max(p):
    token, chat = os.environ.get("MAX_BOT_TOKEN"), max_chat(p)
    if not token or not chat:
        print("MAX: бот ещё не подключён, пропускаю"); return False
    body, answers = split_answers(p["text"])
    markup = None
    if p.get("button") and p.get("link"):
        markup = {"type": "inline_keyboard", "payload": {"buttons": [[{"type": "link", "text": p["button"], "url": p["link"]}]]}}
    media = None
    if p.get("animation"):
        mp4 = ROOT / p["animation"]
        if mp4.suffix.lower() == ".gif":
            mp4 = mp4.with_suffix(".mp4")
        if mp4.exists():
            media = max_upload("video", mp4)
    elif p.get("image"):
        media = max_upload("image", ROOT / p["image"])
    try:
        max_send_text(chat, body, markup, media)
    except Exception as e:
        detail = e.read().decode() if hasattr(e, "read") else str(e)
        print("MAX: ошибка:", detail); return False
    print("MAX: отправлено")
    if answers:
        items = pending_read()
        items.append({"chat": str(chat), "text": answers, "post": p.get("name", ""),
                      "due": (datetime.now(MSK) + timedelta(minutes=ANSWER_DELAY_MIN)).isoformat()})
        pending_write(items)
        print(f"MAX: ответы уйдут через {ANSWER_DELAY_MIN} минут")
    return True

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
    send_max_pending()
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
            if "max" in p["channels"]:
                p["name"] = path.name
                sent = send_max(p) or sent
        except Exception as e:
            print("Ошибка отправки:", e); errors += 1; continue
        if sent:
            done.add(path.name)
    STATE.write_text(json.dumps({"published": sorted(done), "messages": msgs}, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
