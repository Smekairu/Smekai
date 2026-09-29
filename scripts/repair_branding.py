"""Обновляет уже опубликованные посты Telegram и MAX после перехода на «Мыслик».

Без BRANDING_APPLY=1 работает как безопасная проверка и только печатает план.
"""
import html, json, os, re, time, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

from publish import ROOT, POSTS, STATE, parse, split_answers, max_upload, tg_chat

APPLY = os.environ.get("BRANDING_APPLY") == "1"
TAG = re.compile(r"<[^>]+>")
WORD = re.compile(r"[a-zа-яё0-9]+", re.I)


def request(url, data=None, headers=None, files=None, method=None):
    headers = dict(headers or {})
    body = None
    if files:
        boundary, body = uuid.uuid4().hex, b""
        for key, value in (data or {}).items():
            body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n'
                     f'{value}\r\n').encode()
        for key, (name, content) in files.items():
            body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; filename="{name}"\r\n'
                     'Content-Type: image/jpeg\r\n\r\n').encode() + content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        body = json.dumps(data, ensure_ascii=False).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers,
                                 method=method or ("POST" if body is not None else "GET"))
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode() or "{}")


def request_or_skip(url, data=None, headers=None, files=None, method=None):
    """Не прерывает весь ремонт из-за уже исправленного или удалённого поста."""
    try:
        return request(url, data, headers, files, method)
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        if error.code == 400:
            print(f"  пропущено: HTTP 400: {detail[:300]}")
            return None
        raise urllib.error.HTTPError(error.url, error.code, detail, error.hdrs, None)


def plain(text):
    return html.unescape(TAG.sub(" ", str(text or ""))).replace("Смекай", "Мыслик")


def words(text):
    return set(WORD.findall(plain(text).lower()))


def posts():
    out = []
    for path in sorted(POSTS.glob("*.md")):
        try:
            p = parse(path)
        except Exception:
            continue
        p["path"], p["name"] = path, path.name
        p["match"] = words(p["text"])
        out.append(p)
    return out


def best_post(text, items):
    sample = words(text)
    scored = []
    for post in items:
        overlap = len(sample & post["match"])
        score = overlap / max(1, min(len(sample), len(post["match"])))
        if overlap >= 3:
            scored.append((score, overlap, post))
    return max(scored, default=(0, 0, None), key=lambda x: (x[0], x[1]))[2]


def markup(post):
    if post.get("button") and post.get("link"):
        return {"inline_keyboard": [[{"text": post["button"], "url": post["link"]}]]}
    return None


def telegram(items):
    token = os.environ.get("TG_BOT_TOKEN", "")
    if not token:
        print("Telegram: нет токена"); return
    state = json.loads(STATE.read_text(encoding="utf-8"))
    by_name = {p["name"]: p for p in items}
    for name, message_id in state.get("messages", {}).items():
        post = by_name.get(name)
        if not post or "telegram" not in post["channels"]:
            continue
        chat = tg_chat(post)
        if not chat:
            print(f"Telegram: {name} — канал не задан, пропущено")
            continue
        image = ROOT / post.get("image", "") if post.get("image") else None
        print(f"Telegram: {name}, сообщение {message_id}" + (" — обновляю" if APPLY else " — запланировано"))
        if not APPLY:
            continue
        base = f"https://api.telegram.org/bot{token}"
        reply = markup(post)
        if image and image.exists():
            media = {"type": "photo", "media": "attach://photo", "caption": post["text"], "parse_mode": "HTML"}
            data = {"chat_id": chat, "message_id": message_id,
                    "media": json.dumps(media, ensure_ascii=False)}
            if reply:
                data["reply_markup"] = json.dumps(reply, ensure_ascii=False)
            request_or_skip(base + "/editMessageMedia", data, files={"photo": (image.name, image.read_bytes())})
        else:
            data = {"chat_id": chat, "message_id": message_id, "text": post["text"], "parse_mode": "HTML"}
            if reply:
                data["reply_markup"] = reply
            request_or_skip(base + "/editMessageText", data)


def max_posts(items):
    token = os.environ.get("MAX_BOT_TOKEN", "")
    chat = os.environ.get("MAX_CHAT_ID", "")
    if not token or not chat:
        print("MAX: нет токена или MAX_CHAT_ID"); return
    base = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")
    result = request(f"{base}/messages?chat_id={urllib.parse.quote(chat)}&count=100",
                     headers={"Authorization": token})
    for message in result.get("messages", []):
        body = message.get("body") or {}
        mid, current = body.get("mid"), body.get("text") or ""
        post = best_post(current, items)
        if not mid or not post or "max" not in post["channels"]:
            continue
        image = ROOT / post.get("image", "") if post.get("image") else None
        print(f"MAX: {post['name']}, сообщение {mid}" + (" — обновляю" if APPLY else " — запланировано"))
        if not APPLY:
            continue
        text, _ = split_answers(post["text"])
        attachments = []
        if image and image.exists():
            media = max_upload("image", image)
            if media:
                attachments.append(media)
        if post.get("button") and post.get("link"):
            attachments.append({"type": "inline_keyboard", "payload": {"buttons": [[{
                "type": "link", "text": post["button"], "url": post["link"]
            }]]}})
        request(f"{base}/messages?message_id={urllib.parse.quote(str(mid))}",
                {"text": text, "format": "html", "attachments": attachments or None},
                headers={"Authorization": token}, method="PUT")
        time.sleep(0.6)


if __name__ == "__main__":
    all_posts = posts()
    telegram(all_posts)
    max_posts(all_posts)
    print("Готово" if APPLY else "Проверка завершена. Для применения задайте BRANDING_APPLY=1.")
