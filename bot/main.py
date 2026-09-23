"""Мыслик: телеграм-бот с подпиской и разбором заданий.

Первый этап: математика 1-6 класса, подсказки вместо готового ответа,
подписка через Tribute, доступ в закрытый канал.

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
                           Message, ReplyKeyboardMarkup, KeyboardButton)

import ai, db, report, stickers, tasks, voice


def who(user):
    """Старшеклассникам отвечает Лев: другие стикеры и голос."""
    try:
        return "lev" if user and (user["grade"] or 0) >= 9 else "myslik"
    except (KeyError, IndexError, TypeError):
        return "myslik"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("myslik")

TOKEN = os.environ["TG_BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
PAY_URL = os.environ.get("PAY_URL", "https://boosty.to/smekai")
CLOSED_CHANNEL = os.environ.get("TG_CHANNEL_CLOSED", "")
FREE_LIMIT = int(os.environ.get("FREE_LIMIT", "3"))
PAID_LIMIT = int(os.environ.get("PAID_LIMIT", "30"))

bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


PRAISE = ["Верно!", "Точно!", "Да, именно так.", "Отлично, правильно."]
SOFT = ["Пока не то.", "Почти, но нет.", "Не сходится."]


class Reg(StatesGroup):
    name = State()
    grade = State()


def menu():
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📚 Задание"), KeyboardButton(text="📊 Мой прогресс")],
        [KeyboardButton(text="⭐ Подписка"), KeyboardButton(text="👨‍👩‍👧 Родителю")],
        [KeyboardButton(text="❓ Как это работает")],
    ])


def pay_kb():
    rows = [[InlineKeyboardButton(text="Оформить подписку", url=PAY_URL)]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hint_kb(has_more):
    rows = []
    if has_more:
        rows.append([InlineKeyboardButton(text="Подсказка", callback_data="hint")])
    rows.append([InlineKeyboardButton(text="Показать решение", callback_data="solution"),
                 InlineKeyboardButton(text="Другое задание", callback_data="next")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------- регистрация ----------------

@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) > 1 and parts[1].strip():
        db.set_source(m.from_user.id, parts[1].strip())   # откуда пришёл: site, chat5a, boosty
    u = db.get_user(m.from_user.id)
    if u and u["grade"]:
        await m.answer(f"С возвращением, {u['name']}. Что делаем?", reply_markup=menu())
        return
    await m.answer(
        "Привет! Я Мыслик, помощник по учёбе.\n\n"
        "Я не решаю задания за тебя. Я задаю вопросы и даю подсказки, "
        "а решение ты находишь сам. Так знания остаются в голове.\n\n"
        "Как тебя зовут?")
    await state.set_state(Reg.name)


@dp.message(Reg.name)
async def reg_name(m: Message, state: FSMContext):
    name = m.text.strip()[:30]
    await state.update_data(name=name)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(g), callback_data=f"grade:{g}") for g in row]
        for row in ([1, 2, 3], [4, 5, 6])
    ])
    await m.answer(f"Приятно познакомиться, {name}. В каком ты классе?", reply_markup=kb)
    await state.set_state(Reg.grade)


@dp.callback_query(F.data.startswith("grade:"))
async def reg_grade(c: CallbackQuery, state: FSMContext):
    grade = int(c.data.split(":")[1])
    data = await state.get_data()
    db.save_user(c.from_user.id, data.get("name") or c.from_user.first_name, grade)
    await state.clear()
    await c.message.edit_text(f"Записал: {grade} класс.")
    await c.answer()
    await stickers.send_mood(bot, c.message.chat.id, "wave", "lev" if grade >= 9 else "myslik")
    await c.message.answer("Каким голосом мне с тобой говорить?", reply_markup=voice_kb())


def voice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Как с мальчиком", callback_data="voice:boy"),
         InlineKeyboardButton(text="Как с девочкой", callback_data="voice:girl")],
        [InlineKeyboardButton(text="Спокойно, по-взрослому", callback_data="voice:parent"),
         InlineKeyboardButton(text="Без голоса", callback_data="voice:off")],
    ])


@dp.callback_query(F.data.startswith("voice:"))
async def set_voice(c: CallbackQuery):
    profile = c.data.split(":")[1]
    u = db.get_user(c.from_user.id)
    if profile in ("boy", "girl") and who(u) == "lev":
        profile = "lev"      # у старшеклассников говорит Лев
    db.set_voice(c.from_user.id, profile)
    names = {"boy": "бодрый, как с другом", "girl": "тёплый, с улыбкой", "parent": "спокойный, по делу", "lev": "Лев, спокойный", "off": "выключен"}
    await c.message.edit_text(f"Голос: {names.get(profile, profile)}.")
    await c.answer()
    if profile != "off" and not voice.available():
        await c.message.answer("Голосовые сообщения включатся, когда на сервере появится ключ Яндекса. Пока отвечаю текстом.")
    await c.message.answer(
        "Три задания в день бесплатно. Нажимай «Задание», и начнём.\n"
        "С подпиской можно присылать фотографию задания из учебника.",
        reply_markup=menu())


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
        await bot.send_voice(m.chat.id, BufferedInputFile(audio, filename=f"{name}.ogg"),
                             caption=f"{name} · {sex} · {note}")
    await m.answer("Понравившиеся имена впишите в .env: VOICE_BOY, VOICE_GIRL, VOICE_PARENT, VOICE_LEV.")


# ---------------- задания ----------------

async def give_task(m: Message, user):
    left = db.attempts_left(user["id"], FREE_LIMIT, PAID_LIMIT)
    if left <= 0:
        await stickers.send_mood(bot, m.chat.id, "sleepy", who(user))
        await m.answer(
            "На сегодня бесплатные задания кончились.\n\n"
            "С подпиской их 30 в день, плюс разбор домашки и отчёт родителю.",
            reply_markup=pay_kb())
        return
    t = tasks.make(user["grade"])
    db.set_current(user["id"], t)
    await m.answer(f"<b>Задание</b>\n\n{t['q']}\n\nНапиши ответ числом.",
                   reply_markup=hint_kb(True))


@dp.message(F.text == "📚 Задание")
async def task_btn(m: Message):
    user = db.get_user(m.from_user.id)
    if not user:
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
    hints = cur["hints"]
    i = cur["hint_used"]
    if i >= len(hints):
        await c.answer("Подсказки кончились, попробуй решить", show_alert=True); return
    db.bump_hint(user["id"])
    if i == 0:
        await stickers.send_mood(bot, c.message.chat.id, "think", who(user))
    await c.message.answer(f"<b>Подсказка {i + 1}</b>\n{hints[i]}",
                           reply_markup=hint_kb(i + 1 < len(hints)))
    await c.answer()
    await voice.send_voice(bot, c.message.chat.id, hints[i], user["voice"])


@dp.callback_query(F.data == "solution")
async def solution(c: CallbackQuery):
    user = db.get_user(c.from_user.id)
    cur = db.get_current(user["id"]) if user else None
    if not cur:
        await c.answer("Сначала возьми задание", show_alert=True); return
    db.close_current(user["id"], solved=False)
    await c.message.answer(
        f"<b>Разбор</b>\n{cur['steps']}\n\nОтвет: {cur['a']}\n\n"
        "Возьми похожее задание и попробуй сам.",
        reply_markup=hint_kb(False))
    await c.answer()


NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


@dp.message(F.text.regexp(NUM))
async def check_answer(m: Message):
    user = db.get_user(m.from_user.id)
    if not user:
        return
    if db.photo_get(user["id"]):
        await ai_turn(m, user, m.text.strip()); return
    cur = db.get_current(user["id"])
    if not cur:
        return
    given = NUM.search(m.text).group(0).replace(",", ".")
    ok = abs(float(given) - float(cur["a"])) < 1e-6
    if ok:
        db.close_current(user["id"], solved=True)
        stat = db.stats(user["id"])
        streak = db.bump_streak(user["id"], True)
        praise = random.choice(PRAISE) + (" Без подсказок, отлично." if cur["hint_used"] == 0 else "")
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
        if tries == 1:
            add = "Проверь, что нашёл именно то, о чём спрашивают."
        elif tries == 2:
            add = "Попробуй записать условие в черновике и посчитать по шагам."
        else:
            add = "Возьми подсказку, она ниже."
        await m.answer(f"{random.choice(SOFT)} {add}",
                       reply_markup=hint_kb(cur["hint_used"] < len(cur["hints"])))


# ---------------- разбор задания с фотографии ----------------

@dp.message(F.photo)
async def photo(m: Message):
    user = db.get_user(m.from_user.id)
    if not user:
        await m.answer("Напиши /start, чтобы познакомиться."); return
    if not db.is_paid(user["id"]):
        await m.answer("Разбор заданий по фотографии входит в подписку.", reply_markup=pay_kb()); return
    if not ai.available():
        await m.answer("Разбор по фото пока отключён. Напиши задание текстом, я помогу."); return

    await stickers.send_mood(bot, m.chat.id, "think", who(user))
    await bot.send_chat_action(m.chat.id, "typing")
    f = await bot.get_file(m.photo[-1].file_id)
    buf = await bot.download_file(f.file_path)
    text = ai.ocr(buf.read())
    if not text:
        await m.answer("Не смог разобрать текст. Сфотографируй ещё раз, ближе и ровнее, "
                       "или просто напиши задание словами.")
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
    await m.answer(reply, reply_markup=kb)
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
    await c.message.answer(reply or "Не получилось собрать разбор, попробуй ещё раз.")


@dp.callback_query(F.data == "ai_done")
async def ai_done(c: CallbackQuery):
    user = db.get_user(c.from_user.id)
    if user:
        db.photo_close(user["id"])
    await c.answer("Хорошо")
    await c.message.answer("Закончили. Присылай следующее задание, когда будешь готов.")


# ---------------- родитель ----------------

@dp.message(F.text == "👨‍👩‍👧 Родителю")
async def parent_menu(m: Message):
    kids = db.children_of(m.from_user.id)
    if kids:
        lines = ["<b>Ваши дети в Смекае</b>", ""]
        for kid in kids:
            ch = db.get_user(kid)
            if not ch:
                continue
            r = db.week_report(kid)
            lines.append(f"{ch['name']}, {ch['grade']} класс: за неделю решено {r['solved']} из {r['tasks']}, "
                         f"занимался дней {r['days']}")
        lines += ["", "Полный отчёт приходит в воскресенье вечером."]
        await m.answer("\n".join(lines))
        return
    user = db.get_user(m.from_user.id)
    code = db.make_code(user["id"]) if user else None
    await m.answer(
        "<b>Как подключить отчёты</b>\n\n"
        "Отчёт получает тот, кто привяжет ребёнка к себе.\n\n"
        "1. Откройте этого бота с телефона ребёнка и нажмите «Родителю», там будет код.\n"
        "2. Пришлите мне этот код со своего телефона: просто отправьте его сообщением.\n\n"
        + (f"Ваш код для родителя: <b>{code}</b>" if code else ""))


CODE_RE = re.compile(r"^[A-Z0-9]{6}$")


@dp.message(F.text.func(lambda t: bool(t) and CODE_RE.match(t.strip().upper())))
async def link_code(m: Message):
    child_id = db.use_code(m.text, m.from_user.id)
    if not child_id:
        await m.answer("Такого кода нет или он уже использован. Попросите ребёнка открыть «Родителю» ещё раз.")
        return
    ch = db.get_user(child_id)
    await m.answer(f"Готово. Теперь вы получаете отчёты про {ch['name']}, {ch['grade']} класс.\n\n"
                   "Первый отчёт придёт в воскресенье вечером.")
    try:
        await bot.send_message(child_id, "Родитель подключил отчёты о твоих занятиях. "
                                         "Он будет видеть, сколько заданий решено и где было трудно.")
    except Exception:
        pass


@dp.message(Command("report"))
async def report_now(m: Message):
    """Показать отчёт прямо сейчас, не дожидаясь воскресенья."""
    kids = db.children_of(m.from_user.id)
    if not kids:
        await m.answer("Сначала привяжите ребёнка: кнопка «Родителю»."); return
    for kid in kids:
        ch = db.get_user(kid)
        if ch:
            await m.answer(report.build(ch))


# ---------------- подписка и прогресс ----------------

@dp.message(F.text == "⭐ Подписка")
async def sub(m: Message):
    user = db.get_user(m.from_user.id)
    if user and db.is_paid(user["id"]):
        until = db.paid_until(user["id"])
        await m.answer(f"Подписка активна до {until}.\nЗаданий в день: {PAID_LIMIT}.")
        return
    await m.answer(
        "<b>Что даёт подписка</b>\n\n"
        f"• {PAID_LIMIT} заданий в день вместо {FREE_LIMIT}\n"
        "• разбор домашки: присылаешь задание, Мыслик ведёт к ответу\n"
        "• закрытый канал с ежедневными заданиями по классу\n"
        "• отчёт родителю раз в неделю\n\n"
        "390 рублей в месяц, отменить можно в любой момент.",
        reply_markup=pay_kb())


@dp.message(F.text == "📊 Мой прогресс")
async def progress(m: Message):
    user = db.get_user(m.from_user.id)
    if not user:
        return
    s = db.stats(user["id"])
    await m.answer(
        f"<b>{user['name']}, {user['grade']} класс</b>\n\n"
        f"Сегодня решено: {s['today']}\n"
        f"Всего решено: {s['total']}\n"
        f"Без подсказок: {s['clean']}\n"
        f"Дней подряд: {s['streak']}")


@dp.message(F.text == "❓ Как это работает")
async def how(m: Message):
    await m.answer(
        "Я даю задание по твоему классу. Ты отвечаешь числом.\n\n"
        "Ошибся — подскажу, куда смотреть. Нужна помощь — нажми «Подсказка», их три.\n"
        "Совсем застрял — «Показать решение», там разбор по шагам.\n\n"
        "Готовый ответ сразу я не даю специально: списанное забывается к утру.")


@dp.message(Command("grant"))
async def grant(m: Message):
    """Ручная выдача подписки: /grant 123456789 30"""
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("Как пользоваться: /grant telegram_id дней"); return
    uid, days = int(parts[1]), int(parts[2]) if len(parts) > 2 else 30
    db.grant(uid, days)
    await m.answer(f"Подписка для {uid} продлена на {days} дней.")
    try:
        await stickers.send_mood(bot, uid, "love", who(db.get_user(uid)))
        link = await make_invite()
        await bot.send_message(uid, "Подписка активна. Вот ссылка в закрытый канал:\n" + link)
    except Exception as e:
        log.warning("не удалось отправить приглашение: %s", e)


@dp.message(F.text)
async def free_text(m: Message):
    user = db.get_user(m.from_user.id)
    if user and db.photo_get(user["id"]):
        await ai_turn(m, user, m.text.strip())


async def make_invite():
    if not CLOSED_CHANNEL:
        return PAY_URL
    link = await bot.create_chat_invite_link(CLOSED_CHANNEL, member_limit=1,
                                             name="Подписка Смекай")
    return link.invite_link


async def main():
    db.init()
    log.info("Мыслик запущен, модель: %s", ai.PROVIDER if ai.available() else "не подключена")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
