"""Мыслик в MAX: тот же помощник, что и в Telegram, через Bot API MAX.

Запуск: python max_bot.py
Нужны переменные: MAX_BOT_TOKEN, MAX_ADMIN_ID (ваш user_id в MAX, бот покажет его по /id).
Необязательные: MAX_CHANNEL_INVITE (ссылка в закрытый канал MAX), остальные как у Telegram-бота.
Бесплатный доступ для своих: /free и /unfree у администратора, список /users.

База общая с Telegram и сайтом. Людей из MAX база хранит со знаком минус (ids.py),
поэтому код родителя работает между платформами: ребёнок в MAX, родитель в Telegram.
Отличия от Telegram: нет нижней клавиатуры, меню приходит кнопками под сообщением;
стикеры отправляются картинками из assets/pack/sticker.
"""
import asyncio, json, logging, os, random, re, ssl
from pathlib import Path
from urllib.parse import quote

import aiohttp

import ai, db, ids, report, support, tasks, voice
from common import (who, esc, PRAISE, SOFT, GRADE_ROWS, VOICE_NAMES, HELLO, AFTER_VOICE, HOW,
                    LIMIT_OVER, SUB_TEXT, PARENT_HOW, WRONG_ADD, WRONG_ADD_DEFAULT, progress_text,
                    PAY_URL, BOOSTY_URL, CABINET_URL, PLANS, SUB_DAYS, SUPPORT_HELLO, CABINET_TEXT,
                    MAX_FREE_TASKS, daily_limit, plan_line)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("myslik-max")

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
BASE = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")
ADMIN_MAX = int(os.environ.get("MAX_ADMIN_ID", "0") or 0)          # user_id администратора в MAX
INVITE = os.environ.get("MAX_CHANNEL_INVITE", "")
API_ON = bool(os.environ.get("API_PUBLIC", ""))
PACK = Path(os.environ.get("PACK_DIR") or Path(__file__).resolve().parent.parent / "assets" / "pack" / "sticker")

NUM = re.compile(r"-?\d+(?:[.,]\d+)?")
CODE_RE = re.compile(r"^[A-Z0-9]{6}$")
MOODS = ("wave", "yay", "party", "think", "sad", "angry", "surprised", "sleepy", "love", "idle")


# ---------------- обёртка над API ----------------

class MaxApi:
    def __init__(self, token, base=BASE):
        self.token, self.base = token, base
        self.session = None
        self.ssl = ssl.create_default_context()

    async def start(self):
        self.session = aiohttp.ClientSession(headers={"Authorization": self.token})

    async def close(self):
        if self.session:
            await self.session.close()

    async def call(self, method, path, params=None, body=None, retries=2):
        url = self.base + path
        for attempt in range(retries + 1):
            try:
                async with self.session.request(method, url, params=params, json=body, ssl=self.ssl,
                                                timeout=aiohttp.ClientTimeout(total=70)) as r:
                    text = await r.text()
                    if r.status >= 400:
                        if "not.ready" in text and attempt < retries:
                            await asyncio.sleep(2); continue
                        raise RuntimeError(f"{method} {path}: {r.status} {text[:300]}")
                    return json.loads(text) if text else {}
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < retries:
                    await asyncio.sleep(1 + attempt); continue
                raise RuntimeError(f"{method} {path}: {e}")

    async def updates(self, marker=None, timeout=30):
        params = {"limit": 100, "timeout": timeout}
        if marker is not None:
            params["marker"] = marker
        return await self.call("GET", "/updates", params=params, retries=0)

    async def send(self, user_id=None, chat_id=None, text=None, keyboard=None, media=None, fmt="html"):
        params = {"user_id": user_id} if user_id else {"chat_id": chat_id}
        body = {"text": text, "format": fmt if text else None}
        att = []
        if media:
            att.append(media)
        if keyboard:
            att.append({"type": "inline_keyboard", "payload": {"buttons": keyboard}})
        if att:
            body["attachments"] = att
        body = {k: v for k, v in body.items() if v is not None}
        return await self.call("POST", "/messages", params=params, body=body)

    async def answer(self, callback_id, text=None, notification=None, keyboard=None):
        body = {}
        if text is not None:
            body["message"] = {"text": text, "format": "html", "attachments": []}
            if keyboard:
                body["message"]["attachments"] = [{"type": "inline_keyboard", "payload": {"buttons": keyboard}}]
        if notification:
            body["notification"] = notification
        if not body:
            body["notification"] = ""
        try:
            return await self.call("POST", "/answers", params={"callback_id": callback_id}, body=body, retries=0)
        except RuntimeError as e:
            log.warning("ответ на кнопку не принят: %s", e)

    async def upload(self, kind, data, filename):
        """kind: image, audio, video, file. Возвращает вложение для сообщения."""
        up = await self.call("POST", "/uploads", params={"type": kind})
        url = up.get("url")
        if not url:
            raise RuntimeError("MAX не дал адрес загрузки")
        form = aiohttp.FormData()
        form.add_field("data", data, filename=filename, content_type="application/octet-stream")
        async with self.session.post(url, data=form, ssl=self.ssl, timeout=aiohttp.ClientTimeout(total=120)) as r:
            text = await r.text()
            res = json.loads(text) if text.strip().startswith("{") else {}
        if kind == "image":
            photos = res.get("photos") or {}
            tok = next((v.get("token") for v in photos.values() if isinstance(v, dict)), None) or res.get("token")
        else:
            tok = up.get("token") or res.get("token")
        if not tok:
            raise RuntimeError(f"загрузка без токена: {text[:200]}")
        return {"type": kind, "payload": {"token": tok}}

    async def download(self, url):
        async with self.session.get(url, ssl=self.ssl, timeout=aiohttp.ClientTimeout(total=60)) as r:
            return await r.read()


api = MaxApi(TOKEN)


async def say(uid, **kw):
    """Сообщение пользователю по его номеру в общей базе."""
    return await api.send(user_id=ids.to_max(uid), **kw)


# ---------------- кнопки ----------------

def btn(text, payload, intent=None):
    b = {"type": "callback", "text": text, "payload": payload}
    if intent:
        b["intent"] = intent
    return b


def link(text, url):
    return {"type": "link", "text": text, "url": url}


def menu_kb():
    return [[btn("📚 Задание", "m:task"), btn("🏠 Кабинет", "m:cabinet")],
            [btn("📊 Мой прогресс", "m:progress"), btn("⭐ Тарифы", "m:sub")],
            [btn("👨‍👩‍👧 Родителю", "m:parent"), btn("🛟 Помощь", "m:support")]]


def pay_kb():
    return [[link("Оплатить на сайте: карта, МИР, СБП", PAY_URL)], [link("Оформить на Boosty", BOOSTY_URL)],
            [btn("В меню", "m:menu")]]


def hint_kb(has_more):
    rows = []
    if has_more:
        rows.append([btn("Подсказка", "hint")])
    rows.append([btn("Показать решение", "solution"), btn("Другое задание", "next", "positive")])
    rows.append([btn("В меню", "m:menu")])
    return rows


def grade_kb():
    return [[btn(str(g), f"grade:{g}") for g in row] for row in GRADE_ROWS]


def voice_kb():
    return [[btn("Как с мальчиком", "voice:boy"), btn("Как с девочкой", "voice:girl")],
            [btn("Спокойно, по-взрослому", "voice:parent"), btn("Без голоса", "voice:off")]]


def support_kb(buttons):
    rows = []
    for b in buttons:
        rows.append([link(b["text"], b["url"])] if b.get("url") else [btn(b["text"], "do:" + b["do"])])
    rows.append([btn("В меню", "m:menu")])
    return rows


def quick_kb():
    items = support.quick()
    return [[btn(q, "sup:" + i) for i, q in items[k:k + 2]] for k in range(0, len(items), 2)]


# ---------------- стикеры и голос ----------------

async def send_mood(uid, mood, w="myslik"):
    """Картинка-стикер с настроением. Тихо пропускает, если файла нет."""
    if mood not in MOODS:
        return
    prefix = w if w in ("junior", "lev") else "myslik"
    key = f"max:{prefix}:{mood}"
    path = PACK / f"{prefix}-{mood}.png"
    if not path.exists():
        return
    try:
        tok = db.file_id_get(key)
        if tok:
            await say(uid, media={"type": "image", "payload": {"token": tok}})
            return
        att = await api.upload("image", path.read_bytes(), path.name)
        await say(uid, media=att)
        db.file_id_set(key, att["payload"]["token"])
    except Exception as e:
        log.warning("стикер %s не отправлен: %s", mood, e)
        db.file_id_del(key)


async def send_voice(uid, text, profile):
    if profile in (None, "", "off") or not voice.available():
        return
    audio = voice.synth(text, profile)
    if not audio:
        return
    try:
        att = await api.upload("audio", audio, "myslik.ogg")
        await say(uid, media=att)
    except Exception as e:
        log.warning("голосовое не отправлено: %s", e)


# ---------------- знакомство ----------------

REG = {}          # uid -> {"step": "name"|"grade", "name": str}


async def start(uid, first_name, payload=None):
    if payload:
        db.set_source(uid, payload)
    u = db.get_user(uid)
    if payload == "support":
        await support_start(uid); return
    if u and u["grade"]:
        if payload in ("kabinet", "cabinet"):
            await cabinet(uid); return
        if payload == "pay":
            await sub(uid); return
        await say(uid, text=f"С возвращением, {esc(u['name'])}. Что делаем?", keyboard=menu_kb())
        return
    REG[uid] = {"step": "name", "first": first_name}
    free = "\n\nВ MAX задания бесплатны: до 30 в день." if MAX_FREE_TASKS else ""
    await say(uid, text=HELLO.replace("\n\nКак тебя зовут?", free + "\n\nКак тебя зовут?"))


async def reg_text(uid, text):
    st = REG.get(uid)
    if not st or st["step"] != "name":
        return False
    name = text.strip()[:30] or st.get("first") or "друг"
    st.update(step="grade", name=name)
    await say(uid, text=f"Приятно познакомиться, {esc(name)}. В каком ты классе?", keyboard=grade_kb())
    return True


async def reg_grade(uid, cb_id, grade, first_name):
    st = REG.pop(uid, {})
    old = db.get_user(uid)
    name = st.get("name") or (old["name"] if old and old["name"] else first_name) or "друг"
    db.save_user(uid, name, grade)
    await api.answer(cb_id, text=f"Записал: {grade} класс.")
    await send_mood(uid, "wave", who({"grade": grade}))
    await say(uid, text="Каким голосом мне с тобой говорить?", keyboard=voice_kb())


async def set_voice(uid, cb_id, profile):
    u = db.get_user(uid)
    if not u:
        await api.answer(cb_id, notification="Сначала напиши /start"); return
    if profile in ("boy", "girl") and who(u) == "lev":
        profile = "lev"
    db.set_voice(uid, profile)
    await api.answer(cb_id, text=f"Голос: {VOICE_NAMES.get(profile, profile)}.")
    if profile != "off" and not voice.available():
        await say(uid, text="Голосовые сообщения включатся чуть позже. Пока отвечаю текстом.")
    after = AFTER_VOICE
    if MAX_FREE_TASKS:
        after = "В MAX задания бесплатны, до 30 в день. Нажимай «Задание», и начнём.\nРазбор домашки по фото входит в тариф «Мыслик»."
    await say(uid, text=after, keyboard=menu_kb())


# ---------------- личный кабинет ----------------

async def cabinet(uid):
    u = db.get_user(uid)
    if not u or not u["grade"]:
        await say(uid, text="Сначала познакомимся: напиши /start."); return
    if API_ON:
        url = f"{CABINET_URL}#login={db.login_token(uid)}"
        extra = ""
    else:
        url = f"{CABINET_URL}#name={quote(u['name'] or '')}&grade={u['grade']}"
        extra = "\n\nПрогресс в кабинете пока считается на том устройстве, где он открыт."
    s = db.stats(uid)
    await say(uid, text=f"{CABINET_TEXT}\n\n{plan_line(db.plan_of(uid), db.paid_until(uid))} Решено всего: {s['total']}.{extra}",
              keyboard=[[link("Открыть личный кабинет", url)], [btn("В меню", "m:menu")]])


# ---------------- задания ----------------

async def give_task(uid, user):
    left = daily_limit(uid, db.has_helper(uid)) - db.attempts_today(uid)
    if left <= 0:
        await send_mood(uid, "sleepy", who(user))
        text = "На сегодня хватит, завтра будут новые задания." if MAX_FREE_TASKS else LIMIT_OVER
        await say(uid, text=text, keyboard=pay_kb() if not MAX_FREE_TASKS else menu_kb())
        return
    t = tasks.make(user["grade"])
    db.set_current(uid, t)
    await say(uid, text=f"<b>Задание</b>\n\n{esc(t['q'])}\n\nНапиши ответ числом.", keyboard=hint_kb(True))


async def hint(uid, cb_id, user):
    cur = db.get_current(uid)
    if not cur:
        await api.answer(cb_id, notification="Сначала возьми задание"); return
    hints, i = cur["hints"], cur["hint_used"]
    if i >= len(hints):
        await api.answer(cb_id, notification="Подсказки кончились, попробуй решить"); return
    db.bump_hint(uid)
    await api.answer(cb_id, notification="Подсказка ниже")
    if i == 0:
        await send_mood(uid, "think", who(user))
    await say(uid, text=f"<b>Подсказка {i + 1}</b>\n{esc(hints[i])}", keyboard=hint_kb(i + 1 < len(hints)))
    await send_voice(uid, hints[i], user["voice"])


async def solution(uid, cb_id):
    cur = db.get_current(uid)
    if not cur:
        await api.answer(cb_id, notification="Сначала возьми задание"); return
    db.close_current(uid, solved=False)
    await api.answer(cb_id, notification="Разбор ниже")
    await say(uid, text=f"<b>Разбор</b>\n{esc(cur['steps'])}\n\nОтвет: {cur['a']}\n\nВозьми похожее задание и попробуй сам.",
              keyboard=hint_kb(False))


async def check_answer(uid, user, text):
    cur = db.get_current(uid)
    if not cur:
        return False
    given = NUM.search(text).group(0).replace(",", ".")
    if abs(float(given) - float(cur["a"])) < 1e-6:
        db.close_current(uid, solved=True)
        stat = db.stats(uid)
        streak = db.bump_streak(uid, True)
        praise = random.choice(PRAISE) + (" И без подсказок." if cur["hint_used"] == 0 else "")
        if streak and streak % 3 == 0:
            await send_mood(uid, "party", who(user)); praise += f" Уже {streak} подряд!"
        else:
            await send_mood(uid, "yay", who(user))
        await say(uid, text=f"{praise}\nРешено сегодня: {stat['today']}.", keyboard=hint_kb(False))
        await send_voice(uid, praise, user["voice"])
    else:
        db.bump_try(uid)
        db.bump_streak(uid, False)
        tries = cur["tries"] + 1
        if tries == 2:
            await send_mood(uid, "sad", who(user))
        await say(uid, text=f"{random.choice(SOFT)} {WRONG_ADD.get(tries, WRONG_ADD_DEFAULT)}",
                  keyboard=hint_kb(cur["hint_used"] < len(cur["hints"])))
    return True


# ---------------- разбор по фотографии ----------------

async def photo(uid, user, url):
    if not db.has_helper(uid):
        await say(uid, text="Разбор заданий по фотографии входит в тарифы «Мыслик» и «Семья».", keyboard=pay_kb()); return
    if not ai.available():
        await say(uid, text="Разбор по фото пока отключён. Напиши задание текстом, я помогу."); return
    await send_mood(uid, "think", who(user))
    try:
        data = await api.download(url)
    except Exception as e:
        log.warning("фото не скачалось: %s", e); data = b""
    text = ai.ocr(data) if data else ""
    if not text:
        await say(uid, text="Не смог разобрать текст. Сфотографируй ещё раз, ближе и ровнее, или просто напиши задание словами.")
        return
    db.photo_start(uid, text)
    short = text if len(text) < 400 else text[:400] + "…"
    await say(uid, text=f"<b>Вижу задание</b>\n{esc(short)}\n\nДавай разберёмся.")
    await ai_turn(uid, user)


async def ai_turn(uid, user, answer=None):
    cur = db.photo_get(uid)
    if not cur:
        return
    hist = cur["history"]
    if answer:
        hist.append(["user", answer])
    reply = ai.ask(user["grade"], cur["task"], hist, cur["step"] + 1)
    if not reply:
        await say(uid, text="Связь с помощником пропала. Попробуй ещё раз через минуту."); return
    hist.append(["assistant", reply])
    db.photo_step(uid, hist)
    await say(uid, text=esc(reply), keyboard=[[btn("Показать решение", "ai_solve"), btn("Закончить", "ai_done")]])
    await send_voice(uid, reply, user["voice"])


async def ai_solve(uid, cb_id, user):
    cur = db.photo_get(uid)
    if not cur:
        await api.answer(cb_id, notification="Сначала пришли фотографию задания"); return
    await api.answer(cb_id, notification="Собираю разбор")
    reply = ai.ask(user["grade"], cur["task"], cur["history"], 5)
    db.photo_close(uid)
    await say(uid, text=esc(reply or "Не получилось собрать разбор, попробуй ещё раз."), keyboard=menu_kb())


# ---------------- родитель, тарифы, прогресс ----------------

async def parent_menu(uid):
    kids = db.children_of(uid)
    if kids:
        lines = ["<b>Ваши дети в Смекае</b>", ""]
        for kid in kids:
            ch = db.get_user(kid)
            if not ch:
                continue
            r = db.week_report(kid)
            lines.append(f"{esc(ch['name'])}, {ch['grade']} класс: за неделю решено {r['solved']} из {r['tasks']}, "
                         f"занимался дней {r['days']}")
        lines += ["", "Полный отчёт приходит в воскресенье вечером. Команда /report покажет его сейчас."]
        await say(uid, text="\n".join(lines), keyboard=menu_kb()); return
    user = db.get_user(uid)
    code = db.make_code(uid) if user else None
    await say(uid, text=PARENT_HOW + (f"Ваш код для родителя: <b>{code}</b>" if code else ""), keyboard=menu_kb())


async def link_code(uid, text):
    child_id = db.use_code(text, uid)
    if not child_id:
        await say(uid, text="Такого кода нет или он уже использован. Попросите ребёнка открыть «Родителю» ещё раз."); return
    ch = db.get_user(child_id)
    await say(uid, text=f"Готово. Теперь вы получаете отчёты про {esc(ch['name'])}, {ch['grade']} класс.\n\n"
                        "Первый отчёт придёт в воскресенье вечером.", keyboard=menu_kb())
    db.outbox_put(child_id, "Родитель подключил отчёты о твоих занятиях. Он будет видеть, сколько заданий решено и где было трудно.")


async def report_now(uid):
    kids = db.children_of(uid)
    if not kids:
        await say(uid, text="Сначала привяжите ребёнка: кнопка «Родителю».", keyboard=menu_kb()); return
    for kid in kids:
        ch = db.get_user(kid)
        if ch:
            await say(uid, text=report.build(ch))


async def sub(uid):
    head = plan_line(db.plan_of(uid), db.paid_until(uid))
    free = "\n\nВ MAX задания для детей бесплатны. Тарифы нужны для разбора домашки по фото, закрытого канала и отчётов." if MAX_FREE_TASKS else ""
    await say(uid, text=f"{head}\n\n{SUB_TEXT}{free}", keyboard=pay_kb())


async def grant(uid, text):
    """Ручная выдача тарифа администратором: /grant <user_id в MAX> [дней] [tasks|myslik|family]"""
    if uid != ids.from_max(ADMIN_MAX):
        return
    parts = text.split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await say(uid, text="Как пользоваться: /grant user_id [дней] [tasks|myslik|family]"); return
    target = ids.from_max(int(parts[1]))
    days = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else SUB_DAYS
    plan = parts[3] if len(parts) > 3 and parts[3] in PLANS else "myslik"
    until, kids = db.grant_plan(target, plan, days, 0, "manual")
    await say(uid, text=f"Тариф «{PLANS[plan]['title']}» для {parts[1]} до {until}.")
    for t in [target, *kids]:
        db.outbox_put(t, f"Тариф «{PLANS[plan]['title']}» открыт до {until}." + (f"\nЗакрытый канал в MAX:\n{INVITE}" if INVITE else ""))


# ---------------- поддержка ----------------

async def support_start(uid):
    await say(uid, text=SUPPORT_HELLO, keyboard=quick_kb() + [[btn("В меню", "m:menu")]])


async def support_text(uid, text):
    ans, buttons, understood = support.answer(text)
    await say(uid, text=ans, keyboard=support_kb(buttons) if buttons else menu_kb())


async def admin_users(uid):
    if uid != ids.from_max(ADMIN_MAX):
        return
    free = db.free_ids()
    lines = ["<b>Последние пользователи</b> (номер · платформа · имя · класс)", ""]
    for u in db.recent_users(20):
        mark = " · бесплатно" if u["id"] in free else ""
        lines.append(f"{u['id']} · {ids.platform(u['id'])} · {esc(u['name'] or '')} · {u['grade']}{mark}")
    lines += ["", "Бесплатный доступ навсегда: /free номер заметка", "Убрать: /unfree номер"]
    await say(uid, text="\n".join(lines))


async def admin_free(uid, text, add=True):
    """/free номер [заметка] и /unfree номер. Номер как в /users: у людей из MAX со знаком минус."""
    if uid != ids.from_max(ADMIN_MAX):
        return
    parts = text.split(maxsplit=2)
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        lst = db.free_list()
        body = "\n".join(f"{x['uid']} {esc(x['note'] or '')}" for x in lst) or "пока никого"
        await say(uid, text=f"<b>Бесплатный доступ</b>\n{body}\n\nДобавить: /free номер заметка (номер из /users)"); return
    target = int(parts[1])
    if not add:
        db.free_del(target)
        await say(uid, text="Убрал из бесплатного доступа."); return
    db.free_add(target, parts[2] if len(parts) > 2 else "")
    await say(uid, text=f"Готово: {target} занимается бесплатно.")
    msg = "Для тебя все задания Смекая бесплатны. Нажимай «Задание»!"
    if ids.platform(target) == "max" and INVITE:
        msg += f"\n\nЗакрытый канал с заданиями в MAX:\n{INVITE}"
    db.outbox_put(target, msg)


async def admin_reply(uid, text):
    if uid != ids.from_max(ADMIN_MAX):
        return
    parts = text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await say(uid, text="Как пользоваться: /reply номер текст ответа"); return
    await say(uid, text="Отправлено." if support.reply(int(parts[1]), parts[2]) else "Обращение не найдено.")


# ---------------- разбор событий ----------------

async def on_menu(uid, cb_id, key, user):
    await api.answer(cb_id, notification="")
    if key == "task":
        if not user or not user["grade"]:
            await say(uid, text="Напиши /start, чтобы познакомиться."); return
        await give_task(uid, user)
    elif key == "cabinet":
        await cabinet(uid)
    elif key == "progress":
        if user and user["grade"]:
            await say(uid, text=progress_text(user, db.stats(uid)), keyboard=menu_kb())
    elif key == "sub":
        await sub(uid)
    elif key == "parent":
        await parent_menu(uid)
    elif key == "support":
        await support_start(uid)
    elif key == "how":
        await say(uid, text=HOW, keyboard=menu_kb())
    else:
        await say(uid, text="Что делаем?", keyboard=menu_kb())


async def on_callback(upd):
    cb = upd.get("callback") or {}
    user_obj = cb.get("user") or {}
    mid, cb_id, payload = user_obj.get("user_id"), cb.get("callback_id"), cb.get("payload") or ""
    if not mid or not cb_id:
        return
    uid = ids.from_max(mid)
    user = db.get_user(uid)
    first = user_obj.get("first_name") or user_obj.get("name") or ""
    if payload.startswith("grade:"):
        await reg_grade(uid, cb_id, int(payload.split(":")[1]), first)
    elif payload.startswith("voice:"):
        await set_voice(uid, cb_id, payload.split(":")[1])
    elif payload.startswith("m:"):
        await on_menu(uid, cb_id, payload[2:], user)
    elif payload.startswith("sup:"):
        await api.answer(cb_id, notification="")
        it = support.item(payload[4:])
        if it:
            await say(uid, text=support.fill(it["a"]), keyboard=support_kb(support.buttons(it)))
    elif payload.startswith("do:"):
        kind = payload[3:]
        await api.answer(cb_id, notification="")
        if kind in ("refund", "human"):
            db.dialog_set(uid, kind)
            await say(uid, text=support.flow_ask(kind))
    elif payload == "hint":
        await hint(uid, cb_id, user) if user else await api.answer(cb_id, notification="Напиши /start")
    elif payload == "solution":
        await solution(uid, cb_id)
    elif payload == "next":
        await api.answer(cb_id, notification="")
        if user:
            await give_task(uid, user)
    elif payload == "ai_solve":
        await ai_solve(uid, cb_id, user) if user else await api.answer(cb_id, notification="Напиши /start")
    elif payload == "ai_done":
        if user:
            db.photo_close(uid)
        await api.answer(cb_id, notification="Хорошо")
        await say(uid, text="Закончили. Присылай следующее задание, когда будешь готов.", keyboard=menu_kb())
    else:
        await api.answer(cb_id, notification="")


async def on_message(upd):
    msg = upd.get("message") or {}
    sender = msg.get("sender") or {}
    mid = sender.get("user_id")
    rec = msg.get("recipient") or {}
    if not mid or sender.get("is_bot") or rec.get("chat_type") not in (None, "dialog"):
        return                      # в группах и каналах бот молчит
    uid = ids.from_max(mid)
    body = msg.get("body") or {}
    text = (body.get("text") or "").strip()
    first = sender.get("first_name") or sender.get("name") or ""
    user = db.get_user(uid)
    photos = [a for a in (body.get("attachments") or []) if a.get("type") == "image"]

    if text.startswith("/"):
        cmd, _, rest = text[1:].partition(" ")
        cmd = cmd.lower().split("@")[0]
        db.dialog_clear(uid)
        registered = bool(user and user["grade"])
        if cmd == "start":
            await start(uid, first, rest.strip() or None)
        elif cmd == "task":
            await give_task(uid, user) if registered else await start(uid, first)
        elif cmd in ("kabinet", "cabinet"):
            await cabinet(uid)
        elif cmd == "progress":
            if registered:
                await say(uid, text=progress_text(user, db.stats(uid)), keyboard=menu_kb())
        elif cmd == "pay":
            await sub(uid)
        elif cmd == "voice":
            await say(uid, text="Каким голосом мне говорить?", keyboard=voice_kb())
        elif cmd == "parent":
            await parent_menu(uid)
        elif cmd == "report":
            await report_now(uid)
        elif cmd == "support":
            await support_start(uid)
        elif cmd == "help":
            await say(uid, text=HOW, keyboard=menu_kb())
        elif cmd == "grant":
            await grant(uid, text)
        elif cmd == "reply":
            await admin_reply(uid, text)
        elif cmd == "users":
            await admin_users(uid)
        elif cmd == "free":
            await admin_free(uid, text)
        elif cmd == "unfree":
            await admin_free(uid, text, add=False)
        elif cmd == "id":
            await say(uid, text=f"Ваш user_id в MAX: <b>{mid}</b>")
        else:
            await say(uid, text="Что делаем?", keyboard=menu_kb())
        return

    state, _ = db.dialog_get(uid)
    if state in ("refund", "human") and text:
        db.dialog_clear(uid)
        ans, _ = support.flow_done(state, uid, text, sender.get("username") or "")
        await say(uid, text=ans, keyboard=menu_kb())
        return
    if await reg_text(uid, text):
        return
    if photos:
        if not user or not user["grade"]:
            await say(uid, text="Напиши /start, чтобы познакомиться."); return
        url = (photos[-1].get("payload") or {}).get("url")
        if url:
            await photo(uid, user, url)
        return
    registered = bool(user and user["grade"])
    if registered and db.photo_get(uid):
        await ai_turn(uid, user, text); return
    if registered and db.get_current(uid) and NUM.search(text):
        await check_answer(uid, user, text); return
    if CODE_RE.match(text.upper()):
        await link_code(uid, text); return          # родитель может не регистрироваться
    if not registered:
        await start(uid, first); return
    await support_text(uid, text)


async def handle(upd):
    kind = upd.get("update_type")
    try:
        if kind == "bot_started":
            u = upd.get("user") or {}
            if u.get("user_id"):
                await start(ids.from_max(u["user_id"]), u.get("first_name") or u.get("name") or "", upd.get("payload") or None)
        elif kind == "message_created":
            await on_message(upd)
        elif kind == "message_callback":
            await on_callback(upd)
    except Exception as e:
        log.exception("ошибка в обработке %s: %s", kind, e)


# ---------------- доставка сообщений из общей очереди ----------------

async def outbox_loop():
    while True:
        try:
            for msg in db.outbox_take("max"):
                kb = [[link(b["text"], b["url"]) for b in row] for row in msg["buttons"]] if msg["buttons"] else None
                try:
                    await say(msg["uid"], text=msg["text"], keyboard=kb)
                    db.outbox_done(msg["id"], True)
                except Exception as e:
                    log.warning("не доставлено %s: %s", msg["uid"], e)
                    db.outbox_done(msg["id"], False)
        except Exception as e:
            log.error("очередь: %s", e)
        await asyncio.sleep(4)


async def main():
    if not TOKEN:
        raise SystemExit("Нет MAX_BOT_TOKEN")
    db.init()
    await api.start()
    me = await api.call("GET", "/me")
    log.info("Мыслик в MAX запущен: %s (@%s), задания бесплатно: %s", me.get("name"), me.get("username"),
             "да" if MAX_FREE_TASKS else "нет")
    asyncio.create_task(outbox_loop())
    marker = None
    try:
        while True:
            try:
                res = await api.updates(marker)
            except Exception as e:
                log.warning("updates: %s", e); await asyncio.sleep(3); continue
            for upd in res.get("updates") or []:
                await handle(upd)
            marker = res.get("marker", marker)
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
