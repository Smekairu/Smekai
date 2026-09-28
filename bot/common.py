"""Общее для ботов Telegram и MAX: тексты, персонаж по классу, пределы.

Тексты лежат здесь один раз, чтобы оба бота говорили одинаково.
"""
import os

import ids

SITE_URL = os.environ.get("SITE_URL", "https://myslik.ru/")
PAY_URL = os.environ.get("PAY_URL") or SITE_URL + "oplata.html"
BOOSTY_URL = os.environ.get("BOOSTY_URL", "https://boosty.to/smekai")
CABINET_URL = SITE_URL + "kabinet/"
FREE_LIMIT = int(os.environ.get("FREE_LIMIT", "3"))
PAID_LIMIT = int(os.environ.get("PAID_LIMIT", "30"))
SUB_DAYS = int(os.environ.get("SUB_DAYS", "30"))

# тарифы: одинаковые для сайта, ботов и оплаты
PLANS = {
    "trial_tasks": {"title": "Задания — пробная неделя", "price": 49, "helper": False,
                    "days": 7, "trial": True, "base_plan": "tasks",
                    "about": "закрытый канал с заданиями и разборами на 7 дней"},
    "trial_myslik": {"title": "Мыслик — пробная неделя", "price": 149, "helper": True,
                     "days": 7, "trial": True, "base_plan": "myslik",
                     "about": "30 разборов в день, фото домашки и отчёт родителю на 7 дней"},
    "trial_family": {"title": "Семья — пробная неделя", "price": 299, "helper": True,
                     "days": 7, "trial": True, "base_plan": "family",
                     "about": "возможности тарифа Мыслик для двух детей на 7 дней"},
    "tasks": {"title": "Задания", "price": 390, "helper": False,
              "about": "закрытый канал с ежедневными заданиями и разборами"},
    "myslik": {"title": "Мыслик", "price": 890, "helper": True,
               "about": "30 разборов в день, фото домашки, закрытый канал, отчёт родителю"},
    "family": {"title": "Семья", "price": 1490, "helper": True,
               "about": "всё из тарифа Мыслик для двух детей"},
}
PRICE = str(PLANS["tasks"]["price"])

# 1: в MAX задания бесплатны для всех (по умолчанию выключено; бесплатный доступ для своих через /free)
MAX_FREE_TASKS = os.environ.get("MAX_FREE_TASKS", "0") == "1"


def daily_limit(uid, helper):
    import db
    if db.is_free(uid):
        return 100          # свои занимаются сколько хотят
    if helper:
        return PAID_LIMIT
    if MAX_FREE_TASKS and ids.platform(uid) == "max":
        return PAID_LIMIT
    return FREE_LIMIT

PRAISE = ["Верно!", "Точно!", "Да, именно так.", "Отлично, правильно."]
SOFT = ["Пока не то.", "Почти, но нет.", "Не сходится."]
GRADE_ROWS = ([1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11])
VOICE_NAMES = {"boy": "мягкий, дружелюбный", "girl": "живой, с улыбкой",
               "parent": "спокойный, без спешки", "lev": "Лев, спокойный", "off": "выключен"}

COMMANDS = [
    ("start", "Начать или вернуться в меню"),
    ("task", "Новое задание"),
    ("kabinet", "Личный кабинет"),
    ("progress", "Мой прогресс"),
    ("pay", "Тарифы и оплата"),
    ("voice", "Выбрать голос"),
    ("parent", "Родителю: код и отчёты"),
    ("report", "Отчёт о ребёнке сейчас"),
    ("support", "Помощь: оплата, возврат, вопросы"),
    ("help", "Как это работает"),
]

DESCRIPTION = ("Мыслик помогает школьнику 1–11 класса решать задания самому: задаёт вопросы, "
               "даёт подсказки, разбирает по шагам. Три задания в день бесплатно. "
               "С подпиской: разбор домашки по фото, закрытый канал, отчёт родителю.")
SHORT_DESCRIPTION = "Помощник по учёбе для 1–11 класса. Подсказки вместо готовых ответов."
DESCRIPTION_MAX = DESCRIPTION


def who(user):
    """Персонаж по классу: 1–3 младший Мыслик, 4–8 Мыслик, 9–11 Лев."""
    try:
        g = (user["grade"] or 0) if user else 0
    except (KeyError, IndexError, TypeError):
        g = 0
    return "lev" if g >= 9 else "junior" if 0 < g <= 3 else "myslik"


def plan_line(plan, until):
    if plan in PLANS and until and until.startswith("9999"):
        return "Все задания бесплатно."
    if plan in PLANS and until:
        return f"Тариф «{PLANS[plan]['title']}» до {until}."
    return "Тариф «Знакомство»: 3 задания в день бесплатно."


def name_of(user):
    return "Лев" if who(user) == "lev" else "Мыслик"


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


HELLO = ("Привет! Я Мыслик, помощник по учёбе.\n\n"
         "Я не решаю задания за тебя. Я задаю вопросы и даю подсказки, "
         "а решение ты находишь сам. Так знания остаются в голове.\n\n"
         "Как тебя зовут?")

AFTER_VOICE = ("Три задания в день бесплатно. Нажимай «Задание», и начнём.\n"
               "С подпиской можно присылать фотографию задания из учебника.")

HOW = ("Я даю задание по твоему классу. Ты отвечаешь числом.\n\n"
       "Ошибся — подскажу, куда смотреть. Нужна помощь — нажми «Подсказка», их три.\n"
       "Совсем застрял — «Показать решение», там разбор по шагам.\n\n"
       "Готовый ответ сразу я не даю специально: списанное забывается к утру.")

LIMIT_OVER = ("На сегодня бесплатные задания кончились.\n\n"
              f"С подпиской их {PAID_LIMIT} в день, плюс разбор домашки и отчёт родителю.")

SUB_TEXT = ("<b>Тарифы</b>\n\n"
            "<b>Пробная неделя, один раз:</b> Задания — 49 ₽, Мыслик — 149 ₽, Семья — 299 ₽.\n\n"
            f"• <b>Задания</b>, {PLANS['tasks']['price']} ₽ в месяц: {PLANS['tasks']['about']}\n"
            f"• <b>Мыслик</b>, {PLANS['myslik']['price']} ₽ в месяц: {PLANS['myslik']['about']}\n"
            f"• <b>Семья</b>, {PLANS['family']['price']} ₽ в месяц: {PLANS['family']['about']}\n\n"
            "Оплата на сайте картой, МИР или по QR-коду СБП. Отменить можно в любой момент.")

SUPPORT_HELLO = ("Я Мыслик, помогаю не только с уроками. Спросите про оплату, возврат, доступ "
                 "или занятия. Можно своими словами.")

CABINET_TEXT = ("<b>Личный кабинет</b>\n\n"
                "Там занятие с Мысликом на большом экране, прогресс по дням, тариф и настройки. "
                "С планшета и компьютера заниматься удобнее там. Ссылка для входа одноразовая, "
                "действует 30 минут.")

PARENT_HOW = ("<b>Как подключить отчёты</b>\n\n"
              "Отчёт получает тот, кто привяжет ребёнка к себе.\n\n"
              "1. Откройте этого бота с телефона ребёнка и нажмите «Родителю», там будет код.\n"
              "2. Пришлите мне этот код со своего телефона: просто отправьте его сообщением.\n\n")

WRONG_ADD = {1: "Проверь, что нашёл именно то, о чём спрашивают.",
             2: "Попробуй записать условие в черновике и посчитать по шагам."}
WRONG_ADD_DEFAULT = "Возьми подсказку, она ниже."


def progress_text(user, s):
    return (f"<b>{esc(user['name'])}, {user['grade']} класс</b>\n\n"
            f"Сегодня решено: {s['today']}\nВсего решено: {s['total']}\n"
            f"Без подсказок: {s['clean']}\nДней подряд: {s['streak']}")
