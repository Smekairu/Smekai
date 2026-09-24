"""Недельный отчёт родителю.

Запускается раз в неделю, обычно в воскресенье вечером:
  python report.py            поставить отчёты в очередь: их разошлют боты Telegram и MAX
  python report.py --dry      показать тексты, никому не отправляя

На сервере ставится в cron:
  0 19 * * 0 cd /root/Smekai/bot && set -a && . ./.env && set +a && .venv/bin/python report.py
"""
import argparse, asyncio, logging, os, sys
from datetime import date, timedelta

import db, ids

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
    ap.add_argument("--max", action="store_true", help="оставлено для совместимости, отчёты теперь уходят всем сразу")
    args = ap.parse_args()

    db.init()
    pairs = db.parent_links()
    if not pairs:
        log.info("привязанных родителей нет")
        return
    sent = 0
    for parent_id, child_id in pairs:
        child = db.get_user(child_id)
        if not child or ids.platform(parent_id) == "web":
            continue          # родитель без мессенджера видит отчёт в личном кабинете
        text = build(child)
        if args.dry:
            print("—" * 40)
            print("родителю", parent_id, ids.platform(parent_id))
            print(text)
            continue
        db.outbox_put(parent_id, text)      # доставит бот Telegram или MAX
        sent += 1
    log.info("отчётов в очереди на отправку: %s", sent)


if __name__ == "__main__":
    asyncio.run(main())
