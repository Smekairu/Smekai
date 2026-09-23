"""Недельный отчёт родителю.

Запускается раз в неделю, обычно в воскресенье вечером:
  python report.py            отправить отчёты всем привязанным родителям
  python report.py --dry      показать тексты, никому не отправляя

На сервере ставится в cron:
  0 19 * * 0 cd /root/Smekai/bot && set -a && . ./.env && set +a && .venv/bin/python report.py
"""
import argparse, asyncio, logging, os
from datetime import date, timedelta

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("report")


def word(n, one, few, many):
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    n %= 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many


def build(child):
    r = db.week_report(child["id"])
    name = child["name"] or "Ребёнок"
    grade = child["grade"]
    if r["tasks"] == 0:
        return (f"<b>Отчёт за неделю. {name}</b>\n\n"
                "На этой неделе занятий не было.\n\n"
                "Иногда достаточно сесть рядом и вместе открыть бота: первое задание обычно "
                "втягивает. Начните с чего-то лёгкого, чтобы получилось с первого раза.")

    solved, tasks, hints = r["solved"], r["tasks"], r["hints"]
    clean = max(0, solved - r.get("with_hints", 0))
    days = r.get("days", 0)
    share = round(solved / tasks * 100) if tasks else 0

    lines = [f"<b>Отчёт за неделю. {name}, {grade} класс</b>", ""]
    lines.append(f"Решено: {solved} из {tasks} {word(tasks, 'задания', 'заданий', 'заданий')}, это {share} процентов")
    lines.append(f"Без подсказок: {clean}")
    lines.append(f"Занимался дней: {days} из 7" if days else "")
    lines.append("")

    if share >= 80 and hints <= solved:
        lines.append("Неделя сильная. Решает почти всё и редко просит помощь. "
                     "Можно понемногу давать задания посложнее, иначе станет скучно.")
    elif share >= 50:
        lines.append("Ровная неделя. Основное получается, трудности в отдельных типах заданий.")
    else:
        lines.append("Неделя тяжёлая. Больше половины заданий не доведены до конца. "
                     "Чаще всего дело не в лени, а в непонятой теме.")

    if hints > solved * 2 and solved:
        lines.append("Подсказками пользуется часто. Это нормально, но попробуйте перед подсказкой "
                     "спрашивать: что тут известно и что надо найти. Обычно этого хватает.")
    if days and days <= 2:
        lines.append("Занимались всего пару дней. Пятнадцать минут каждый день работают лучше, "
                     "чем час в воскресенье.")

    lines.append("")
    lines.append("Что сделать на этой неделе: попросите пересказать одно задание своими словами, "
                 "не глядя в тетрадь. Если пересказ сбивчивый, тему стоит повторить.")
    return "\n".join(l for l in lines if l != "" or True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="не отправлять, только показать")
    args = ap.parse_args()

    db.init()
    pairs = db.parent_links()
    if not pairs:
        log.info("привязанных родителей нет")
        return
    bot = None if args.dry else Bot(os.environ["TG_BOT_TOKEN"],
                                    default=DefaultBotProperties(parse_mode="HTML"))
    sent = 0
    for parent_id, child_id in pairs:
        child = db.get_user(child_id)
        if not child:
            continue
        text = build(child)
        if args.dry:
            print("—" * 40)
            print("родителю", parent_id)
            print(text)
            continue
        try:
            await bot.send_message(parent_id, text)
            sent += 1
        except Exception as e:
            log.error("не доставлено родителю %s: %s", parent_id, e)
    if bot:
        await bot.session.close()
    log.info("отправлено отчётов: %s", sent)


if __name__ == "__main__":
    asyncio.run(main())
