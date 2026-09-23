"""Собирает посты с заданиями на ближайшие дни и кладёт их в папку posts.

Запускается автоматически перед публикацией. Ничего настраивать не нужно.
Расписание недели: понедельник математика, вторник русский, среда природа,
четверг логика, пятница викторина, суббота разбор недели, воскресенье семейное задание.
"""
import argparse, random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bank

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
MSK = timezone(timedelta(hours=3))

DAY = {
    0: ("math", "🔢 Понедельник. Математика"),
    1: ("rus", "✏️ Вторник. Русский язык"),
    2: ("nature", "🌍 Среда. Окружающий мир и природа"),
    3: ("🧠", "логика"),
    4: ("quiz", "🎯 Пятница. Викторина"),
    5: ("razbor", "📘 Суббота. Разбор недели"),
    6: ("family", "👨‍👩‍👧 Воскресенье. Задание для всей семьи"),
}
DAY[3] = ("logic", "🧠 Четверг. Логика")

FOOTER = {
    "math": "Не диктуйте ход решения. Спросите: что известно и что надо найти.",
    "rus": "Сомневаетесь в гласной — подберите слово, где на неё падает ударение.",
    "nature": "Хороший вопрос после ответа: а как это проверить самим?",
    "logic": "Если ребёнок застрял, дайте подумать минуту молча. Это и есть работа.",
    "quiz": "Считайте очки всей семьёй. Проигрыш взрослого поднимает интерес сильнее похвалы.",
}

BAND_TITLE = {
    "1-2": "1–2 класс", "3-4": "3–4 класс", "5-6": "5–6 класс",
    "7-8": "7–8 класс", "9-11": "9–11 класс",
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(day, used):
    subject, title = DAY[day.weekday()]
    rnd = random.Random(day.strftime("%Y%m%d"))

    if subject in ("razbor", "family"):
        item = bank.pick_common(subject, used, rnd)
        body = [f"<b>{esc(title)}</b>", "", f"<b>{esc(item['title'])}</b>", esc(item["text"])]
        if subject == "razbor":
            extra = {b: bank.pick(b, "math", used, rnd) for b in ("1-2", "5-6", "9-11")}
            body += ["", "<b>Задачи на выходные</b>"]
            body += [f"{BAND_TITLE[b]}: {esc(it['q'])}" for b, it in extra.items() if it]
            answers = " | ".join(f"{BAND_TITLE[b]}: {esc(it['a'])}" for b, it in extra.items() if it)
            body += ["", f"Ответы: <tg-spoiler>{answers}</tg-spoiler>"]
        return subject, "\n".join(body)

    picked = {b: bank.pick(b, subject, used, rnd) for b in bank.BANDS}
    body = [f"<b>{esc(title)}</b>", ""]
    for b in bank.BANDS:
        it = picked.get(b)
        if it:
            body.append(f"<b>{BAND_TITLE[b]}</b>\n{esc(it['q'])}\n")
    answers = "  ".join(f"{BAND_TITLE[b]}: {esc(it['a'])}." for b, it in picked.items() if it)
    body.append(f"Ответы: <tg-spoiler>{answers}</tg-spoiler>")
    foot = FOOTER.get(subject)
    if foot:
        body += ["", esc(foot)]
    return subject, "\n".join(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3, help="на сколько дней вперёд готовить посты")
    ap.add_argument("--time", default="09:00", help="время публикации по Москве")
    args = ap.parse_args()

    used = bank.used_read()
    today = datetime.now(MSK).date()
    made = 0
    for i in range(args.days):
        day = today + timedelta(days=i)
        when = datetime.strptime(f"{day:%Y-%m-%d} {args.time}", "%Y-%m-%d %H:%M").replace(tzinfo=MSK)
        if when < datetime.now(MSK):
            continue
        if list(POSTS.glob(f"{day:%Y-%m-%d}-*.md")):
            continue   # на этот день пост уже есть, написанный руками или собранный раньше
        subject, text = build(day, used)
        name = f"{day:%Y-%m-%d}-{args.time.replace(':', '')}-{subject}.md"
        path = POSTS / name
        head = (f"---\ntime: {day:%Y-%m-%d} {args.time}\nchannels: telegram, max\n"
                f"channel: closed\nauto: yes\n---\n")
        path.write_text(head + text + "\n", encoding="utf-8")
        print("собран пост:", name)
        made += 1
    bank.used_write(used)
    if not made:
        print("новые посты не нужны, всё уже собрано")


if __name__ == "__main__":
    main()
