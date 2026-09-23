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

import db, tasks

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

PRAISE = ["Верно!", "Точно!", "Да, именно так.", "Отлично, правильно."]
SOFT = ["Пока не то.", "Почти, но нет.", "Не сходится."]


class Reg(StatesGroup):
    name = State()
    grade = State()


def menu():
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📚 Задание"), KeyboardButton(text="📊 Мой прогресс")],
        [KeyboardButton(text="⭐ Подписка"), KeyboardButton(text="❓ Как это работает")],
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
    await c.message.answer(
        "Три задания в день бесплатно. Нажимай «Задание», и начнём.",
        reply_markup=menu())
    await c.answer()


# ---------------- задания ----------------

async def give_task(m: Message, user):
    left = db.attempts_left(user["id"], FREE_LIMIT, PAID_LIMIT)
    if left <= 0:
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
    await c.message.answer(f"<b>Подсказка {i + 1}</b>\n{hints[i]}",
                           reply_markup=hint_kb(i + 1 < len(hints)))
    await c.answer()


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
    cur = db.get_current(user["id"])
    if not cur:
        return
    given = NUM.search(m.text).group(0).replace(",", ".")
    ok = abs(float(given) - float(cur["a"])) < 1e-6
    if ok:
        db.close_current(user["id"], solved=True)
        stat = db.stats(user["id"])
        await m.answer(
            f"{random.choice(PRAISE)} {'Без подсказок, отлично.' if cur['hint_used'] == 0 else ''}\n"
            f"Решено сегодня: {stat['today']}.",
            reply_markup=hint_kb(False))
    else:
        db.bump_try(user["id"])
        tries = cur["tries"] + 1
        if tries == 1:
            add = "Проверь, что нашёл именно то, о чём спрашивают."
        elif tries == 2:
            add = "Попробуй записать условие в черновике и посчитать по шагам."
        else:
            add = "Возьми подсказку, она ниже."
        await m.answer(f"{random.choice(SOFT)} {add}",
                       reply_markup=hint_kb(cur["hint_used"] < len(cur["hints"])))


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
        link = await make_invite()
        await bot.send_message(uid, "Подписка активна. Вот ссылка в закрытый канал:\n" + link)
    except Exception as e:
        log.warning("не удалось отправить приглашение: %s", e)


async def make_invite():
    if not CLOSED_CHANNEL:
        return PAY_URL
    link = await bot.create_chat_invite_link(CLOSED_CHANNEL, member_limit=1,
                                             name="Подписка Смекай")
    return link.invite_link


async def main():
    db.init()
    log.info("Мыслик запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
