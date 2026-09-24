"""Мыслик: телеграм-бот с подпиской, личным кабинетом и поддержкой.

Математика 1-11 класса, подсказки вместо готового ответа, подписка, закрытый канал,
вход в личный кабинет на сайте, ответы поддержки. Тексты общие с ботом MAX (common.py).

Запуск: python main.py
Переменные окружения перечислены в README.md
"""
import asyncio, logging, os, random, re

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                           Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo)

import ai, db, ids, report, stickers, support, tasks, voice
from common import (who, esc, PRAISE, SOFT, GRADE_ROWS, VOICE_NAMES, HELLO, AFTER_VOICE, HOW,
                    LIMIT_OVER, SUB_TEXT, PARENT_HOW, WRONG_ADD, WRONG_ADD_DEFAULT, progress_text,
                    PAY_URL, BOOSTY_URL, CABINET_URL, PLANS, SUB_DAYS, SUPPORT_HELLO, CABINET_TEXT,
                    daily_limit, plan_line)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("myslik")

TOKEN = os.environ["TG_BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)
CLOSED_CHANNEL = os.environ.get("TG_CHANNEL_CLOSED", "")
API_ON = bool(os.environ.get("API_PUBLIC", ""))      # сервер кабинета запущен и доступен сайту

bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


class Reg(StatesGroup):
    name = State()
    grade = State()


# ---------------- клавиатуры ----------------

def menu():
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📚 Задание"), KeyboardButton(text="🏠 Кабинет")],
        [KeyboardButton(text="📊 Мой прогресс"), KeyboardButton(text="⭐ Тарифы")],
        [KeyboardButton(text="👨‍👩‍👧 Родителю"), KeyboardButton(text="🛟 Помощь")],
    ])


def pay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить на сайте: карта, МИР, СБП", url=PAY_URL)],
        [InlineKeyboardButton(text="Оформить на Boosty", url=BOOSTY_URL)],
    ])


def hint_kb(has_more):
    rows = []
    if has_more:
        rows.append([InlineKeyboardButton(text="Подсказка", callback_data="hint")])
    rows.append([InlineKeyboardButton(text="Показать решение", callback_data="solution"),
                 InlineKeyboardButton(text="Другое задание", callback_data="next")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def voice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Как с мальчиком", callback_data="voice:boy"),
         InlineKeyboardButton(text="Как с девочкой", callback_data="voice:girl")],
        [InlineKeyboardButton(text="Спокойно, по-взрослому", callback_data="voice:parent"),
         InlineKeyboardButton(text="Без голоса", callback_data="voice:off")],
    ])


def support_kb(buttons):
    """Кнопки ответа поддержки: ссылки и действия (возврат, человек)."""
    rows = []
    for b in buttons:
        if b.get("url"):
            rows.append([InlineKeyboardButton(text=b["text"], url=b["url"])])
        else:
            rows.append([InlineKeyboardButton(text=b["text"], callback_data="do:" + b["do"])])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


def quick_kb():
    items = support.quick()
    rows = [[InlineKeyboardButton(text=q, callback_data="sup:" + i) for i, q in items[k:k + 2]]
            for k in range(0, len(items), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------- поддержка: диалог возврата и вопроса человеку ----------------

async def in_dialog(m: Message) -> bool:
    if not m.text or m.text.startswith("/"):
        return False
    return db.dialog_get(m.from_user.id)[0] in ("refund", "human")


@dp.message(in_dialog)
async def dialog_text(m: Message):
    kind, _ = db.dialog_get(m.from_user.id)
    db.dialog_clear(m.from_user.id)
    user = m.from_user
    contact = f"@{user.username}" if user.username else ""
    text, _ = support.flow_done(kind, m.from_user.id, m.text, contact)
    await m.answer(text, reply_markup=menu())


@dp.callback_query(F.data.startswith("do:"))
async def support_do(c: CallbackQuery):
    kind = c.data[3:]
    if kind not in ("refund", "human"):
        await c.answer(); return
    db.dialog_set(c.from_user.id, kind)
    await c.answer()
    await c.message.answer(support.flow_ask(kind))


@dp.callback_query(F.data.startswith("sup:"))
async def support_topic(c: CallbackQuery):
    it = support.item(c.data[4:])
    await c.answer()
    if it:
        await c.message.answer(support.fill(it["a"]), reply_markup=support_kb(support.buttons(it)))


@dp.message(Command("support"))
@dp.message(F.text == "🛟 Помощь")
async def support_start(m: Message):
    await m.answer(SUPPORT_HELLO, reply_markup=quick_kb())


@dp.message(Command("reply"))
async def admin_reply(m: Message):
    """Ответ администратора на обращение: /reply номер текст"""
    if m.from_user.id != ADMIN_ID:
        return
    parts = (m.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await m.answer("Как пользоваться: /reply номер текст ответа"); return
    await m.answer("Отправлено." if support.reply(int(parts[1]), parts[2]) else "Обращение не найдено.")


# ---------------- регистрация ----------------

@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    parts = (m.text or "").split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else ""
    if arg:
        db.set_source(m.from_user.id, arg)   # откуда пришёл: site, quiz, boosty
    u = db.get_user(m.from_user.id)
    if arg == "support":
        await support_start(m); return
    if u and u["grade"]:
        if arg in ("kabinet", "cabinet"):
            await cabinet(m); return
        if arg == "pay":
            await sub(m); return
        await m.answer(f"С возвращением, {esc(u['name'])}. Что делаем?", reply_markup=menu())
        return
    await m.answer(HELLO)
    await state.set_state(Reg.name)


@dp.message(Reg.name)
async def reg_name(m: Message, state: FSMContext):
    name = (m.text or "").strip()[:30] or m.from_user.first_name
    await state.update_data(name=name)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(g), callback_data=f"grade:{g}") for g in row] for row in GRADE_ROWS])
    await m.answer(f"Приятно познакомиться, {esc(name)}. В каком ты классе?", reply_markup=kb)
    await state.set_state(Reg.grade)


@dp.callback_query(F.data.startswith("grade:"))
async def reg_grade(c: CallbackQuery, state: FSMContext):
    grade = int(c.data.split(":")[1])
    data = await state.get_data()
    old = db.get_user(c.from_user.id)
    name = data.get("name") or (old["name"] if old and old["name"] else c.from_user.first_name)
    db.save_user(c.from_user.id, name, grade)
    await state.clear()
    await c.message.edit_text(f"Записал: {grade} класс.")
    await c.answer()
    await stickers.send_mood(bot, c.message.chat.id, "wave", who({"grade": grade}))
    await c.message.answer("Каким голосом мне с тобой говорить?", reply_markup=voice_kb())


@dp.callback_query(F.data.startswith("voice:"))
async def set_voice(c: CallbackQuery):
    profile = c.data.split(":")[1]
    u = db.get_user(c.from_user.id)
    if profile in ("boy", "girl") and who(u) == "lev":
        profile = "lev"      # у старшеклассников говорит Лев
    db.set_voice(c.from_user.id, profile)
    await c.message.edit_text(f"Голос: {VOICE_NAMES.get(profile, profile)}.")
    await c.answer()
    if profile != "off" and not voice.available():
        await c.message.answer("Голосовые сообщения включатся чуть позже. Пока отвечаю текстом.")
    await c.message.answer(AFTER_VOICE, reply_markup=menu())


@dp.message(Command("voice"))
async def voice_cmd(m: Message):
    await m.answer("Каким голосом мне говорить?", reply_markup=voice_kb())


@dp.message(Command("voicetest"))
async def voice_test(m: Message):
    """Присылает одну фразу всеми голосами Яндекса, чтобы выбрать. Только для администратора."""
    if m.from_user.id != ADMIN_ID:
        return
    if not voice.available():
        await m.answer("Ключ Яндекса не настроен, слушать пока нечего."); return
    parts = m.text.split(maxsplit=1)
    phrase = parts[1] if len(parts) > 1 else "Привет, я Мыслик. Половину от двенадцати мы нашли, дальше сам. Что известно и что надо найти?"
    from aiogram.types import BufferedInputFile
    for name, sex, note in voice.CATALOG:
        audio = voice.synth(phrase, voice_name=name)
        if not audio:
            await m.answer(f"{name}: не получилось"); continue
        await bot.send_voice(m.chat.id, BufferedInputFile(audio, filename=f"{name}.ogg"), caption=f"{name} · {sex} · {note}")
    await m.answer("Понравившиеся имена впишите в .env: VOICE_BOY, VOICE_GIRL, VOICE_PARENT, VOICE_LEV.")


# ---------------- личный кабинет ----------------

@dp.message(Command("kabinet"))
@dp.message(F.text == "🏠 Кабинет")
async def cabinet(m: Message):
    uid = m.from_user.id
    u = db.get_user(uid)
    if not u or not u["grade"]:
        await m.answer("Сначала познакомимся: напиши /start."); return
    rows = []
    if API_ON:
        tok = db.login_token(uid)
        rows.append([InlineKeyboardButton(text="Открыть здесь, в Telegram", web_app=WebAppInfo(url=CABINET_URL + "?from=tg"))])
        rows.append([InlineKeyboardButton(text="Открыть на планшете или компьютере", url=f"{CABINET_URL}#login={tok}")])
        extra = ""
    else:
        # сервер кабинета ещё не запущен: кабинет открывается с именем и классом, прогресс хранится на устройстве
        from urllib.parse import quote
        rows.append([InlineKeyboardButton(text="Открыть личный кабинет",
                                          url=f"{CABINET_URL}#name={quote(u['name'] or '')}&grade={u['grade']}")])
        extra = "\n\nПрогресс в кабинете пока считается на том устройстве, где он открыт."
    s = db.stats(uid)
    await m.answer(f"{CABINET_TEXT}\n\n{plan_line(db.plan_of(uid), db.paid_until(uid))} Решено всего: {s['total']}.{extra}",
                   reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


# ---------------- задания ----------------

async def give_task(m: Message, user):
    uid = user["id"]
    left = daily_limit(uid, db.has_helper(uid)) - db.attempts_today(uid)
    if left <= 0:
        await stickers.send_mood(bot, m.chat.id, "sleepy", who(user))
        await m.answer(LIMIT_OVER, reply_markup=pay_kb())
        return
    t = tasks.make(user["grade"])
    db.set_current(uid, t)
    await m.answer(f"<b>Задание</b>\n\n{esc(t['q'])}\n\nНапиши ответ числом.", reply_markup=hint_kb(True))


@dp.message(F.text == "📚 Задание")
@dp.message(Command("task"))
async def task_btn(m: Message):
    user = db.get_user(m.from_user.id)
    if not user or not user["grade"]:
        await m.answer("Напиши /start, чтобы познакомиться.")
        return
    await give_task(m, user)


@dp.callback_query(F.data == "next")
async def next_task(c: CallbackQuery):
    user = db.get_user(c.from_user.id)
    await c.answer()
    if user:
        await give_task(c.message, user)


@dp.callback_query(F.data == "hint")
async def hint(c: CallbackQuery):
    user = db.get_user(c.from_user.id)
    cur = db.get_current(user["id"]) if user else None
    if not cur:
        await c.answer("Сначала возьми задание", show_alert=True); return
    hints, i = cur["hints"], cur["hint_used"]
    if i >= len(hints):
        await c.answer("Подсказки кончились, попробуй решить", show_alert=True); return
    db.bump_hint(user["id"])
    if i == 0:
        await stickers.send_mood(bot, c.message.chat.id, "think", who(user))
    await c.message.answer(f"<b>Подсказка {i + 1}</b>\n{esc(hints[i])}", reply_markup=hint_kb(i + 1 < len(hints)))
    await c.answer()
    await voice.send_voice(bot, c.message.chat.id, hints[i], user["voice"])


@dp.callback_query(F.data == "solution")
async def solution(c: CallbackQuery):
    user = db.get_user(c.from_user.id)
    cur = db.get_current(user["id"]) if user else None
    if not cur:
        await c.answer("Сначала возьми задание", show_alert=True); return
    db.close_current(user["id"], solved=False)
    await c.message.answer(f"<b>Разбор</b>\n{esc(cur['steps'])}\n\nОтвет: {cur['a']}\n\nВозьми похожее задание и попробуй сам.",
                           reply_markup=hint_kb(False))
    await c.answer()


NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


async def has_task(m: Message) -> bool:
    return bool(m.text and NUM.search(m.text) and (db.get_current(m.from_user.id) or db.photo_get(m.from_user.id)))


@dp.message(has_task)
async def check_answer(m: Message):
    user = db.get_user(m.from_user.id)
    if not user:
        return
    if db.photo_get(user["id"]):
        await ai_turn(m, user, m.text.strip()); return
    cur = db.get_current(user["id"])
    given = NUM.search(m.text).group(0).replace(",", ".")
    ok = abs(float(given) - float(cur["a"])) < 1e-6
    if ok:
        db.close_current(user["id"], solved=True)
        stat = db.stats(user["id"])
        streak = db.bump_streak(user["id"], True)
        praise = random.choice(PRAISE) + (" И без подсказок." if cur["hint_used"] == 0 else "")
        if streak and streak % 3 == 0:
            await stickers.send_mood(bot, m.chat.id, "party", who(user))
            praise += f" Уже {streak} подряд!"
        else:
            await stickers.send_mood(bot, m.chat.id, "yay", who(user))
        await m.answer(f"{praise}\nРешено сегодня: {stat['today']}.", reply_markup=hint_kb(False))
        await voice.send_voice(bot, m.chat.id, praise, user["voice"])
    else:
        db.bump_try(user["id"])
        db.bump_streak(user["id"], False)
        tries = cur["tries"] + 1
        if tries == 2:
            await stickers.send_mood(bot, m.chat.id, "sad", who(user))
        add = WRONG_ADD.get(tries, WRONG_ADD_DEFAULT)
        await m.answer(f"{random.choice(SOFT)} {add}", reply_markup=hint_kb(cur["hint_used"] < len(cur["hints"])))


# ---------------- разбор задания с фотографии ----------------

@dp.message(F.photo)
async def photo(m: Message):
    user = db.get_user(m.from_user.id)
    if not user or not user["grade"]:
        await m.answer("Напиши /start, чтобы познакомиться."); return
    if not db.has_helper(user["id"]):
        await m.answer("Разбор заданий по фотографии входит в тарифы «Мыслик» и «Семья».", reply_markup=pay_kb()); return
    if not ai.available():
        await m.answer("Разбор по фото пока отключён. Напиши задание текстом, я помогу."); return
    await stickers.send_mood(bot, m.chat.id, "think", who(user))
    await bot.send_chat_action(m.chat.id, "typing")
    f = await bot.get_file(m.photo[-1].file_id)
    buf = await bot.download_file(f.file_path)
    text = ai.ocr(buf.read())
    if not text:
        await m.answer("Не смог разобрать текст. Сфотографируй ещё раз, ближе и ровнее, или просто напиши задание словами.")
        return
    db.photo_start(user["id"], text)
    short = text if len(text) < 400 else text[:400] + "…"
    await m.answer(f"<b>Вижу задание</b>\n{esc(short)}\n\nДавай разберёмся.")
    await ai_turn(m, user)


async def ai_turn(m: Message, user, answer=None):
    cur = db.photo_get(user["id"])
    if not cur:
        return
    hist = cur["history"]
    if answer:
        hist.append(["user", answer])
    await bot.send_chat_action(m.chat.id, "typing")
    reply = ai.ask(user["grade"], cur["task"], hist, cur["step"] + 1)
    if not reply:
        await m.answer("Связь с помощником пропала. Попробуй ещё раз через минуту.")
        return
    hist.append(["assistant", reply])
    db.photo_step(user["id"], hist)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Показать решение", callback_data="ai_solve"),
        InlineKeyboardButton(text="Закончить", callback_data="ai_done")]])
    await m.answer(esc(reply), reply_markup=kb)
    await voice.send_voice(bot, m.chat.id, reply, user["voice"])


@dp.callback_query(F.data == "ai_solve")
async def ai_solve(c: CallbackQuery):
    user = db.get_user(c.from_user.id)
    cur = db.photo_get(user["id"]) if user else None
    if not cur:
        await c.answer("Сначала пришли фотографию задания", show_alert=True); return
    await c.answer()
    await bot.send_chat_action(c.message.chat.id, "typing")
    reply = ai.ask(user["grade"], cur["task"], cur["history"], 5)
    db.photo_close(user["id"])
    await c.message.answer(esc(reply or "Не получилось собрать разбор, попробуй ещё раз."))


@dp.callback_query(F.data == "ai_done")
async def ai_done(c: CallbackQuery):
    user = db.get_user(c.from_user.id)
    if user:
        db.photo_close(user["id"])
    await c.answer("Хорошо")
    await c.message.answer("Закончили. Присылай следующее задание, когда будешь готов.")


# ---------------- родитель ----------------

@dp.message(F.text == "👨‍👩‍👧 Родителю")
@dp.message(Command("parent"))
async def parent_menu(m: Message):
    kids = db.children_of(m.from_user.id)
    if kids:
        lines = ["<b>Ваши дети в Смекае</b>", ""]
        for kid in kids:
            ch = db.get_user(kid)
            if not ch:
                continue
            r = db.week_report(kid)
            lines.append(f"{esc(ch['name'])}, {ch['grade']} класс: за неделю решено {r['solved']} из {r['tasks']}, занимался дней {r['days']}")
        lines += ["", "Полный отчёт приходит в воскресенье вечером. Команда /report покажет его сейчас."]
        await m.answer("\n".join(lines))
        return
    user = db.get_user(m.from_user.id)
    code = db.make_code(user["id"]) if user else None
    await m.answer(PARENT_HOW + (f"Ваш код для родителя: <b>{code}</b>" if code else ""))


CODE_RE = re.compile(r"^[A-Z0-9]{6}$")


@dp.message(F.text.func(lambda t: bool(t) and CODE_RE.match(t.strip().upper())))
async def link_code(m: Message):
    child_id = db.use_code(m.text, m.from_user.id)
    if not child_id:
        await m.answer("Такого кода нет или он уже использован. Попросите ребёнка открыть «Родителю» ещё раз.")
        return
    ch = db.get_user(child_id)
    await m.answer(f"Готово. Теперь вы получаете отчёты про {esc(ch['name'])}, {ch['grade']} класс.\n\nПервый отчёт придёт в воскресенье вечером.")
    db.outbox_put(child_id, "Родитель подключил отчёты о твоих занятиях. Он будет видеть, сколько заданий решено и где было трудно.")


@dp.message(Command("report"))
async def report_now(m: Message):
    kids = db.children_of(m.from_user.id)
    if not kids:
        await m.answer("Сначала привяжите ребёнка: кнопка «Родителю»."); return
    for kid in kids:
        ch = db.get_user(kid)
        if ch:
            await m.answer(report.build(ch))


# ---------------- тарифы и прогресс ----------------

@dp.message(F.text == "⭐ Тарифы")
@dp.message(Command("pay"))
async def sub(m: Message):
    uid = m.from_user.id
    head = plan_line(db.plan_of(uid), db.paid_until(uid))
    await m.answer(f"{head}\n\n{SUB_TEXT}", reply_markup=pay_kb())


@dp.message(F.text == "📊 Мой прогресс")
@dp.message(Command("progress"))
async def progress(m: Message):
    user = db.get_user(m.from_user.id)
    if not user or not user["grade"]:
        return
    await m.answer(progress_text(user, db.stats(user["id"])))


@dp.message(F.text == "❓ Как это работает")
@dp.message(Command("help"))
async def how(m: Message):
    await m.answer(HOW)


@dp.message(Command("grant"))
async def grant(m: Message):
    """Ручная выдача подписки: /grant telegram_id [дней] [tasks|myslik|family]"""
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await m.answer("Как пользоваться: /grant id [дней] [tasks|myslik|family]\nДля MAX id со знаком минус."); return
    uid = int(parts[1])
    days = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else SUB_DAYS
    plan = parts[3] if len(parts) > 3 and parts[3] in PLANS else "myslik"
    until, kids = db.grant_plan(uid, plan, days, 0, "manual")
    await m.answer(f"Тариф «{PLANS[plan]['title']}» для {uid} до {until}." + (f" Дети: {kids}" if kids else ""))
    for who_id in [uid, *kids]:
        text = f"Тариф «{PLANS[plan]['title']}» открыт до {until}."
        if ids.platform(who_id) == "tg":
            try:
                await stickers.send_mood(bot, who_id, "love", who(db.get_user(who_id)))
                text += "\nСсылка в закрытый канал:\n" + await make_invite()
            except Exception as e:
                log.warning("приглашение не создано: %s", e)
        elif ids.platform(who_id) == "max" and os.environ.get("MAX_CHANNEL_INVITE"):
            text += "\nЗакрытый канал в MAX:\n" + os.environ["MAX_CHANNEL_INVITE"]
        db.outbox_put(who_id, text)


@dp.message(Command("users"))
async def admin_users(m: Message):
    """Последние пользователи с номерами: чтобы найти своих и выдать им бесплатный доступ."""
    if m.from_user.id != ADMIN_ID:
        return
    free = db.free_ids()
    lines = ["<b>Последние пользователи</b> (номер · платформа · имя · класс)", ""]
    for u in db.recent_users(20):
        mark = " · бесплатно" if u["id"] in free else ""
        lines.append(f"<code>{u['id']}</code> · {ids.platform(u['id'])} · {esc(u['name'] or '')} · {u['grade']}{mark}")
    lines += ["", "Выдать бесплатный доступ навсегда: /free номер заметка", "Убрать: /unfree номер"]
    await m.answer("\n".join(lines))


@dp.message(Command("free"))
async def admin_free(m: Message):
    """/free номер [заметка]: все задания бесплатно и без ограничений, доступ в закрытый канал."""
    if m.from_user.id != ADMIN_ID:
        return
    parts = (m.text or "").split(maxsplit=2)
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        lst = db.free_list()
        body = "\n".join(f"<code>{x['uid']}</code> {esc(x['note'] or '')}" for x in lst) or "пока никого"
        await m.answer(f"<b>Бесплатный доступ</b>\n{body}\n\nДобавить: /free номер заметка (номер из /users)"); return
    uid = int(parts[1])
    db.free_add(uid, parts[2] if len(parts) > 2 else "")
    await m.answer(f"Готово: {uid} занимается бесплатно.")
    text = "Для тебя все задания Смекая бесплатны. Нажимай «Задание»!"
    if ids.platform(uid) == "tg" and CLOSED_CHANNEL:
        try:
            text += "\n\nСсылка в закрытый канал с заданиями:\n" + await make_invite()
        except Exception as e:
            log.warning("приглашение не создано: %s", e)
    elif ids.platform(uid) == "max" and os.environ.get("MAX_CHANNEL_INVITE"):
        text += "\n\nЗакрытый канал с заданиями в MAX:\n" + os.environ["MAX_CHANNEL_INVITE"]
    db.outbox_put(uid, text)


@dp.message(Command("unfree"))
async def admin_unfree(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    parts = (m.text or "").split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await m.answer("Как пользоваться: /unfree номер"); return
    db.free_del(int(parts[1]))
    await m.answer("Убрал из бесплатного доступа.")


async def make_invite():
    if not CLOSED_CHANNEL:
        return PAY_URL
    link = await bot.create_chat_invite_link(CLOSED_CHANNEL, member_limit=1, name="Подписка Смекай")
    return link.invite_link


# ---------------- всё остальное: вопросы поддержки ----------------

@dp.message(F.text)
async def free_text(m: Message):
    user = db.get_user(m.from_user.id)
    if user and db.photo_get(user["id"]):
        await ai_turn(m, user, m.text.strip()); return
    text, buttons, understood = support.answer(m.text)
    await m.answer(text, reply_markup=support_kb(buttons) or (menu() if not understood else None))


# ---------------- доставка сообщений из общей очереди ----------------

async def outbox_loop():
    while True:
        try:
            for msg in db.outbox_take("tg"):
                kb = None
                if msg["buttons"]:
                    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=b["text"], url=b["url"]) for b in row]
                                                               for row in msg["buttons"]])
                try:
                    await bot.send_message(msg["uid"], msg["text"], reply_markup=kb, disable_web_page_preview=True)
                    db.outbox_done(msg["id"], True)
                except Exception as e:
                    log.warning("не доставлено %s: %s", msg["uid"], e)
                    db.outbox_done(msg["id"], False)
        except Exception as e:
            log.error("очередь: %s", e)
        await asyncio.sleep(4)


async def main():
    db.init()
    log.info("Мыслик запущен, модель: %s, кабинет: %s", ai.PROVIDER if ai.available() else "не подключена",
             "сервер" if API_ON else "на устройстве")
    asyncio.create_task(outbox_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
