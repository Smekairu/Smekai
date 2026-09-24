"""Мыслик в роли поддержки: отвечает на частые вопросы, даёт ссылку на оплату, принимает заявки на возврат.

Вопросы и ответы лежат в assets/support.json. Этот же файл читает сайт, поэтому
бот и сайт отвечают одинаково. Чтобы поправить ответ, правится только JSON.
"""
import json, os, re
from pathlib import Path

import db

ROOT = Path(__file__).resolve().parent.parent
FILE = Path(os.environ.get("SUPPORT_FILE") or ROOT / "assets" / "support.json")
SITE = os.environ.get("SITE_URL", "https://smekairu.github.io/Smekai/")
MAX_LINK = os.environ.get("MAX_CHANNEL_URL", "https://max.ru/join/nQJFTVidgdh_w-lFQo9rbmy54ErMxxp_vbMRjOdTJFo")


def admin_ids():
    """Куда слать обращения: администратор в Telegram и в MAX (в базе MAX со знаком минус)."""
    out = []
    tg, mx = os.environ.get("ADMIN_ID", "").strip(), os.environ.get("MAX_ADMIN_ID", "").strip()
    if tg.isdigit():
        out.append(int(tg))
    if mx.isdigit():
        out.append(-int(mx))
    return out


_data = None


def data():
    global _data
    if _data is None:
        _data = json.loads(FILE.read_text(encoding="utf-8"))
    return _data


def fill(s):
    return s.replace("{SITE}", SITE).replace("{MAX}", MAX_LINK)


def norm(text):
    t = (text or "").lower().replace("ё", "е")
    return " " + re.sub(r"[^a-zа-я0-9 ]+", " ", t) + " "


def match(text):
    """Лучший ответ и его вес. Вес 0 значит, что вопрос не понят."""
    t = norm(text)
    best, score = None, 0
    for it in data()["items"]:
        s = 0
        for k in it["keys"]:
            k2 = norm(k).strip()
            if not k2:
                continue
            if (" " + k2) in t:
                s += 2 if " " in k2 else 1
        if s > score:
            best, score = it, s
    return best, score


def item(item_id):
    return next((i for i in data()["items"] if i["id"] == item_id), None)


def buttons(it):
    """Кнопки ответа: [{'text', 'url'}] или [{'text', 'do'}]."""
    out = []
    for a in (it or {}).get("actions", []):
        act = data()["actions"].get(a)
        if not act:
            continue
        b = {"text": act["text"], "id": a}
        if act.get("url"):
            b["url"] = fill(act["url"])
        else:
            b["do"] = act["do"]
        out.append(b)
    return out


def quick():
    """Кнопки тем для первого экрана поддержки."""
    return [(i["id"], i["q"]) for i in (item(x) for x in data()["quick"]) if i]


def answer(text):
    """(текст ответа, кнопки, понял ли вопрос)."""
    it, score = match(text)
    if not it:
        return fill(data()["fallback"]), buttons({"actions": ["human", "pay"]}), False
    return fill(it["a"]), buttons(it), True


def flow_ask(kind):
    return data()["flows"][kind]["ask"]


def flow_done(kind, uid, text, contact=""):
    """Сохраняет обращение, сообщает администратору, возвращает ответ пользователю."""
    tid = db.ticket_new(uid, kind, text, contact)
    title = "Заявка на возврат" if kind == "refund" else "Вопрос в поддержку"
    who = db.get_user(uid)
    name = (who["name"] if who and who["name"] else "без имени")
    import ids
    note = (f"<b>{title} №{tid}</b>\nот: {esc(name)}, {ids.platform(uid)}, id {uid}\n"
            f"контакт: {esc(contact) or 'через бота'}\n\n{esc(text)}\n\n"
            f"Ответить: /reply {tid} текст")
    for a in admin_ids():
        db.outbox_put(a, note)
    return data()["flows"][kind]["done"].replace("{N}", str(tid)), tid


def reply(tid, text):
    """Ответ администратора на обращение: уходит пользователю в его мессенджер."""
    t = db.ticket_get(tid)
    if not t:
        return False
    db.outbox_put(t["uid"], f"<b>Ответ поддержки на обращение №{tid}</b>\n\n{esc(text)}")
    db.ticket_close(tid)
    return True


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
