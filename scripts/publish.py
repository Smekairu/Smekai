"""Публикует посты из папки posts/ в Telegram и MAX, когда подошло время.

Формат файла поста: posts/ГГГГ-ММ-ДД-ЧЧММ-название.md
Верх файла (между строками ---):
  time: 2026-09-23 10:00        время по Москве
  channels: telegram, max       куда отправлять
  button: Пройти викторину      текст кнопки (необязательно)
  link: quiz                    ссылка кнопки: quiz, boosty или полный адрес
  image: assets/posts/2026-09-25-1830.jpg  картинка (необязательно)
  channel: closed               закрытый канал: в Telegram TG_CHANNEL_CLOSED, в MAX MAX_CHAT_ID_CLOSED
  animation: assets/anim/myslik-wave.mp4  анимация Мыслика (необязательно, для MAX берётся .mp4)
Ниже: текст поста. Разметка Telegram HTML: <b>жирный</b>, <i>курсив</i>, <a href="...">ссылка</a>.
"""
import json, os, re, sys, urllib.request, urllib.parse, uuid
from hashlib import sha256
from html import unescape
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
STATE = ROOT / "state" / "published.json"
MSK = timezone(timedelta(hours=3))
SITE = "https://myslik.ru/"
LINKS = {
    "quiz": SITE + "viktorina/",
    "kabinet": SITE + "kabinet/",
    "oplata": SITE + "oplata.html",
    "lev": SITE + "lev.html",
    "site": SITE,
    "boosty": SITE + "oplata.html",
    "telegram": "https://t.me/smekai_ru",
    "max": "https://max.ru/join/nQJFTVidgdh_w-lFQo9rbmy54ErMxxp_vbMRjOdTJFo",
}
CAPTION_MAX = 1000       # у Telegram подпись к картинке до 1024 знаков
MENTOR = {'telegram':'https://t.me/smekai_ru_bot?start=chat','max':'https://max.ru/id501807779599_bot?start=chat'}
DELIVERY = ROOT/'state'/'delivery.json'

def save_json(path, value):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(path)

def button_link(post,channel):
    if post.get('link') in ('duel1','duel2'):
        seed = '20261127' if post['link']=='duel1' else '20261204'
        query = urllib.parse.urlencode({'mode':'class','round':seed,'utm_source':channel,'utm_campaign':post['link']})
        return SITE + 'viktorina/?' + query
    return MENTOR[channel] if post.get('link')=='mentor' else post.get('link')

def record(book,name,channel,status,mid=None):
    entry={'status':status,'time':datetime.now(MSK).isoformat(timespec='seconds')}
    if mid:entry['message_id']=mid
    book.setdefault(name,{})[channel]=entry
    save_json(DELIVERY,book)

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
        markup = json.dumps({"inline_keyboard": [[{"text": p["button"], "url": button_link(p,'telegram')}]]})
    media = None
    if p.get("animation") and (ROOT / p["animation"]).exists():
        media = ("sendAnimation", "animation", ROOT / p["animation"])
    elif p.get("image") and (ROOT / p["image"]).exists():
        media = ("sendPhoto", "photo", ROOT / p["image"])
    if media and len(re.sub(r"<[^>]+>", "", p["text"])) > CAPTION_MAX:
        # длинный пост: сначала картинка без подписи, потом текст отдельным сообщением
        media = None
    if media:
        data = {"chat_id": chat, "caption": p["text"], "parse_mode": "HTML"}
        if markup: data["reply_markup"] = markup
        r = http(base + "/" + media[0], data, files={media[1]: (media[2].name, media[2].read_bytes())})
    else:
        data = {"chat_id": chat, "text": p["text"], "parse_mode": "HTML", "disable_web_page_preview": False}
        if markup: data["reply_markup"] = json.loads(markup)
        r = http(base + "/sendMessage", data)
    ok = bool(r.get("ok")); print("Telegram:", "отправлено" if ok else r)
    return (r.get("result") or {}).get("message_id") if ok else None

def max_chat(p):
    """Открытый канал MAX по умолчанию, закрытый для постов с channel: closed.
    Если закрытого канала в MAX нет, такие посты в MAX не уходят.
    MAX_TASKS_FREE=1 отправит их в открытый канал для всех (по умолчанию выключено)."""
    if str(p.get("channel", "")).strip().lower() in ("closed", "закрытый"):
        if os.environ.get("MAX_TASKS_FREE", "0") == "1":
            return os.environ.get("MAX_CHAT_ID") or ""
        return os.environ.get("MAX_CHAT_ID_CLOSED") or ""
    return os.environ.get("MAX_CHAT_ID") or ""

SPOILER = re.compile(r"\s*Ответы?:\s*<tg-spoiler>(.*?)</tg-spoiler>\s*", re.S)
PENDING = ROOT / "state" / "max_pending.json"
ANSWER_DELAY_MIN = 60
PUBLIC_ANSWERS = ROOT / "viktorina" / "razbory.json"

def public_answer_card(post):
    if post.get("channel", "").strip().lower() not in ("", "open"):
        return None
    if "max" not in post["channels"] or not post.get("name"):
        return None
    snippets = SPOILER.findall(post["text"])
    if not snippets:
        return None
    def plain(fragment):
        fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
        return unescape(re.sub(r"</?[a-zA-Z][^>]*>", "", fragment)).strip()
    heading = re.search(r"<b>(.*?)</b>", post["text"], re.S)
    title = plain(heading[1]) if heading else "Разбор задания"
    answer = "\n\n".join(plain(fragment) for fragment in snippets).strip()
    if not answer:
        return None
    key = sha256((post["name"] + "\n" + post["text"]).encode("utf-8")).hexdigest()
    return key, {"title": title, "answer": answer}

def max_question_content(post):
    body, _ = split_answers(post["text"])
    rows = []
    card = public_answer_card(post)
    if card:
        key, value = card
        try:
            catalog = json.loads(PUBLIC_ANSWERS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            catalog = {}
        if isinstance(catalog, dict) and catalog.get(key) == value:
            rows.append([{"type": "link", "text": "Проверить ответ",
                          "url": SITE + "viktorina/razbor.html#" + key}])
        else:
            # An editorial correction may reach the feed before the website catalogue.
            body = SPOILER.sub(lambda m: "\n\n<b>Ответ для самопроверки</b>\n" + m[1].strip() + "\n\n", post["text"]).strip()
    if post.get("button") and post.get("link"):
        link_row = [{"type": "link", "text": post["button"], "url": button_link(post, "max")}]
        if post.get("link") in ("duel1", "duel2"):
            rows.insert(0, link_row)
        else:
            rows.append(link_row)
    markup = {"type": "inline_keyboard", "payload": {"buttons": rows}} if rows else None
    return body, markup

def split_answers(text):
    """Отделяет ответы от задания. В MAX нет скрытого текста, поэтому ответы уходят позже."""
    answers = SPOILER.findall(text)
    if not answers:
        return text.replace("<tg-spoiler>", "").replace("</tg-spoiler>", ""), ""
    body = SPOILER.sub("\n\n", text).strip()+"\n\nРазбор появится здесь отдельным сообщением."
    return body, "\n\n".join(answer.strip() for answer in answers)

def pending_read():
    if PENDING.exists():
        return json.loads(PENDING.read_text(encoding="utf-8"))
    return []

def pending_write(items):
    PENDING.parent.mkdir(exist_ok=True)
    save_json(PENDING,items)

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
            result=http(f"{base}/messages?chat_id={urllib.parse.quote(str(chat))}", body, headers={"Authorization": token})
            return ((result.get('message') or {}).get('body') or {}).get('mid') or True
        except urllib.error.HTTPError as e:
            detail = e.read().decode()
            if "not.ready" in detail and attempt < 3:
                time.sleep(2); continue      # видео ещё обрабатывается
            raise urllib.error.HTTPError(e.url, e.code, detail, e.hdrs, None)

def send_max_pending(book):
    """Отправляет ответы, у которых прошёл час после задания."""
    items, left, now = pending_read(), [], datetime.now(MSK)
    for it in items:
        due = datetime.fromisoformat(it["due"])
        name=it.get('post') or it['due']
        if book.get(name,{}).get('max_answer',{}).get('status')=='sent':continue
        if due > now:
            left.append(it); continue
        try:
            head = f"<b>Ответ к посту «{it['title']}»</b>" if it.get("title") else "<b>Ответы к заданиям</b>"
            mid=max_send_text(it["chat"], head + "\n\n" + it["text"])
            record(book,name,'max_answer','sent',mid if isinstance(mid,str) else None)
            print("MAX: отправлены ответы к", it.get("post"))
        except Exception as e:
            detail = e.read().decode() if hasattr(e, "read") else str(e)
            print("MAX: ответы не ушли:", detail); left.append(it)
    if items:
        pending_write(left)

def send_max(p):
    token, chat = os.environ.get("MAX_BOT_TOKEN"), max_chat(p)
    if not token:
        print("MAX: нет MAX_BOT_TOKEN, пропускаю"); return False
    if not chat:
        print("MAX: канал для этого поста не задан, пропускаю"); return False
    body, markup = max_question_content(p)
    media = None
    if p.get("animation"):
        mp4 = ROOT / p["animation"]
        if mp4.suffix.lower() == ".gif":
            mp4 = mp4.with_suffix(".mp4")
        if mp4.exists():
            media = max_upload("video", mp4)
    elif p.get("image") and (ROOT / p["image"]).exists():
        media = max_upload("image", ROOT / p["image"])
    try:
        mid=max_send_text(chat, body, markup, media)
    except Exception as e:
        detail = e.read().decode() if hasattr(e, "read") else str(e)
        print("MAX: ошибка:", detail); return False
    print("MAX: отправлено")
    return mid

def queue_max_answer(p,book):
    if book.get(p['name'],{}).get('max_answer',{}).get('status')=='sent':return
    body,answers=split_answers(p['text'])
    if answers:
        items = pending_read()
        if any(it.get('post')==p['name'] for it in items):return
        t = re.search(r"<b>(.*?)</b>", body)
        sent=datetime.fromisoformat(book[p['name']]['max']['time'])
        items.append({"chat": str(max_chat(p)), "text": answers, "post": p['name'],
                      "title": re.sub(r"<[^>]+>", "", t.group(1)).strip() if t else "",
                      "due": (sent + timedelta(minutes=ANSWER_DELAY_MIN)).isoformat()})
        pending_write(items)
        print(f"MAX: ответы уйдут через {ANSWER_DELAY_MIN} минут")

def refresh_max_views(book,now):
    token=os.environ.get('MAX_BOT_TOKEN')
    if not token:return
    day=now.date().isoformat()
    targets={}
    for deliveries in book.values():
        for channel in ('max','max_answer'):
            item=deliveries.get(channel,{})
            mid=item.get('message_id')
            if (mid and item.get('status')=='sent' and item.get('sample_day')!=day
                    and now-datetime.fromisoformat(item['time'])<timedelta(days=9)):
                targets[mid]=item
    ids=list(targets)
    for pos in range(0,len(ids),25):
        batch=ids[pos:pos+25]
        query=urllib.parse.urlencode({'message_ids':','.join(batch)})
        try:
            base=os.environ.get('MAX_API_BASE','https://platform-api2.max.ru')
            data=http(base+'/messages?'+query,headers={'Authorization':token})
        except Exception as exc:
            print('MAX: статистика недоступна',type(exc).__name__);return
        for msg in data.get('messages',[]):
            mid=(msg.get('body') or {}).get('mid')
            views=(msg.get('stat') or {}).get('views')
            if mid in targets and isinstance(views,int):
                targets[mid].update(views=views,views_at=now.isoformat(timespec='seconds'))
        for mid in batch:targets[mid]['sample_day']=day
        save_json(DELIVERY,book)

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
    book=json.loads(DELIVERY.read_text('utf8')) if DELIVERY.exists() else {}
    send_max_pending(book)
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
        if p.get("channel") in ("closed","закрытый"):
            print("Закрытый выпуск обслуживает Selectel");continue
        if p["time"] > now: continue
        print(f"Публикую {path.name}")
        p["name"]=path.name
        for channel in p['channels']:
            status=book.get(path.name,{}).get(channel,{}).get('status')
            if status in ('sent','expired'):continue
            if now-p['time']>timedelta(days=1):
                record(book,path.name,channel,'expired')
                print(channel,'просрочен',path.name);continue
            target=tg_chat(p) if channel=='telegram' else max_chat(p)
            if not target:
                if status!='unconfigured':record(book,path.name,channel,'unconfigured')
                print(channel,'не настроен адрес канала',path.name);continue
            try:
                mid=send_telegram(p) if channel=='telegram' else send_max(p)
            except Exception as exc:
                print(channel,'ошибка',type(exc).__name__,getattr(exc,'code',''));mid=None
            if not mid:
                errors+=1;record(book,path.name,channel,'failed');continue
            record(book,path.name,channel,'sent',None if mid is True else mid)
            if channel=='telegram':msgs[path.name]=mid
        if book.get(path.name,{}).get('max',{}).get('status')=='sent':
            queue_max_answer(p,book)
        if all(book[path.name][c]['status']=='sent' for c in p['channels']):
            done.add(path.name)
    state.update(published=sorted(done),messages=msgs)
    save_json(STATE,state)
    refresh_max_views(book,now)
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()

