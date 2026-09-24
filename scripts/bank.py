"""Банк заданий: загрузка, выбор без повторов, генератор примеров по математике.

Банк лежит в папке bank: файлы 1-2.json, 3-4.json, 5-6.json, 7-8.json, 9-11.json
и common.json с разборами недели и семейными заданиями.

Формат задания: {"q": "вопрос", "a": "ответ"}.
Чтобы пополнить банк, просто добавьте элементы в нужный список, больше ничего не нужно.
"""
import json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "bank"
USED = ROOT / "state" / "used.json"

BANDS = ["1-2", "3-4", "5-6", "7-8", "9-11"]
SUBJECTS = ["math", "rus", "nature", "logic", "quiz"]


def load(band):
    return json.loads(BANK.joinpath(band + ".json").read_text(encoding="utf-8"))


def load_common():
    return json.loads(BANK.joinpath("common.json").read_text(encoding="utf-8"))


def used_read():
    if USED.exists():
        return json.loads(USED.read_text(encoding="utf-8"))
    return {}


def used_write(d):
    USED.parent.mkdir(exist_ok=True)
    USED.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def pick(band, subject, used, rnd):
    """Берёт задание, которое ещё не выходило. Когда список кончился, начинает круг заново."""
    if subject == "math":
        items = load(band).get("math") or []
        if not items:
            recent = used.setdefault("math_recent", [])
            for _ in range(30):                 # без повторов среди последних 300 примеров
                it = gen_math(band, rnd)
                if it["q"] not in recent:
                    break
            recent.append(it["q"])
            del recent[:-300]
            return it
    else:
        items = load(band).get(subject) or []
    if not items:
        return None
    key = f"{band}|{subject}"
    seen = set(used.get(key, []))
    free = [i for i in range(len(items)) if i not in seen]
    if not free:
        seen, free = set(), list(range(len(items)))
    i = rnd.choice(free)
    used[key] = sorted(seen | {i})
    return items[i]


def pick_common(kind, used, rnd):
    items = load_common().get(kind, [])
    key = f"common|{kind}"
    seen = set(used.get(key, []))
    free = [i for i in range(len(items)) if i not in seen]
    if not free:
        seen, free = set(), list(range(len(items)))
    i = rnd.choice(free)
    used[key] = sorted(seen | {i})
    return items[i]


# ---------- генератор примеров по математике ----------

def plural(n, one, few, many):
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    n %= 10
    return one if n == 1 else few if 2 <= n <= 4 else many


def gen_math(band, rnd):
    """Примеры создаются на ходу, поэтому математика в банке не кончается. Ответ всегда считается точно."""
    from fractions import Fraction
    from math import gcd
    if band == "1-2":
        kind = rnd.choice(["sum", "diff", "mult", "task"])
        if kind == "sum":
            a, b = rnd.randint(21, 58), rnd.randint(13, 39)
            return {"q": f"Посчитай: {a} + {b}", "a": str(a + b)}
        if kind == "diff":
            a, b = rnd.randint(52, 96), rnd.randint(14, 38)
            return {"q": f"Посчитай: {a} − {b}", "a": str(a - b)}
        if kind == "mult":
            a, b = rnd.randint(2, 5), rnd.randint(3, 9)
            return {"q": f"Посчитай: {a} · {b}", "a": str(a * b)}
        r, c = rnd.randint(3, 7), rnd.randint(3, 6)
        return {"q": f"В коробке {r} {plural(r, 'ряд', 'ряда', 'рядов')} по {c} {plural(c, 'конфете', 'конфеты', 'конфет')}. Сколько всего конфет?",
                "a": f"{r * c}"}

    if band == "3-4":
        kind = rnd.choice(["mult", "div", "order", "task"])
        if kind == "mult":
            a, b = rnd.randint(14, 48), rnd.randint(3, 9)
            return {"q": f"Посчитай: {a} · {b}", "a": str(a * b)}
        if kind == "div":
            b, q = rnd.randint(3, 9), rnd.randint(12, 40)
            return {"q": f"Посчитай: {b * q} : {b}", "a": str(q)}
        if kind == "order":
            b, c = rnd.randint(3, 9), rnd.randint(4, 12)
            a = b * c + rnd.randint(4, 60)
            return {"q": f"Посчитай: {a} − {b} · {c}", "a": f"{a - b * c}, сначала умножение"}
        price, n = rnd.choice([25, 30, 45, 60]), rnd.randint(3, 8)
        return {"q": f"Тетрадь стоит {price} рублей. Сколько стоят {n} {plural(n, 'тетрадь', 'тетради', 'тетрадей')}?",
                "a": f"{price * n} рублей"}

    if band == "5-6":
        kind = rnd.choice(["order", "frac", "percent", "speed"])
        if kind == "order":
            b, c, d = rnd.randint(3, 8), rnd.randint(9, 18), rnd.randint(2, 9)
            a = b * (c + d) + rnd.randint(5, 60)
            return {"q": f"Вычислите: {a} − {b} · ({c} + {d})", "a": f"{a - b * (c + d)}"}
        if kind == "frac":
            d = rnd.choice([4, 5, 6, 8])
            n = rnd.choice([k for k in range(1, d) if gcd(k, d) == 1])
            whole = d * rnd.randint(3, 9)
            return {"q": f"Найдите {n}/{d} от числа {whole}.", "a": str(whole // d * n)}
        if kind == "percent":
            p, whole = rnd.choice([10, 20, 25, 40, 50]), rnd.choice([120, 240, 360, 480, 600])
            return {"q": f"Найдите {p} процентов от {whole}.", "a": str(whole * p // 100)}
        v, t = rnd.choice([12, 15, 18, 20]), rnd.randint(2, 5)
        return {"q": f"Велосипедист едет со скоростью {v} км/ч. Какой путь он проедет за {t} {plural(t, 'час', 'часа', 'часов')}?",
                "a": f"{v * t} км"}

    if band == "7-8":
        kind = rnd.choice(["linear", "formula", "percent", "geom"])
        if kind == "linear":
            x, a, b = rnd.randint(2, 12), rnd.randint(2, 9), rnd.randint(3, 20)
            return {"q": f"Решите уравнение: {a}x + {b} = {a * x + b}", "a": f"x = {x}"}
        if kind == "formula":
            a, b = rnd.randint(2, 9), rnd.randint(2, 9)
            return {"q": f"Раскройте скобки: ({a}x + {b})²", "a": f"{a*a}x² + {2*a*b}x + {b*b}"}
        p, whole = rnd.choice([15, 18, 24, 35]), rnd.choice([200, 400, 800, 1200])
        if kind == "percent":
            return {"q": f"Товар стоил {whole} рублей и подорожал на {p} {plural(p, 'процент', 'процента', 'процентов')}. Какой стала цена?",
                    "a": f"{whole + whole * p // 100} рублей"}
        a, b = rnd.choice([(3, 4), (6, 8), (5, 12), (9, 12), (8, 15)])
        return {"q": f"Катеты прямоугольного треугольника {a} и {b}. Найдите гипотенузу.",
                "a": f"{int(round((a*a + b*b) ** 0.5))}"}

    # 9-11
    kind = rnd.choice(["quad", "prog", "power", "prob"])
    if kind == "quad":
        r1 = rnd.randint(-6, 6)
        r2 = rnd.choice([k for k in range(-6, 7) if k != r1])
        b, c = -(r1 + r2), r1 * r2
        sb = f"+ {b}x " if b > 0 else f"− {abs(b)}x " if b < 0 else ""
        sc = f"+ {c} " if c > 0 else f"− {abs(c)} " if c < 0 else ""
        lo, hi = sorted((r1, r2))
        return {"q": f"Решите уравнение: x² {sb}{sc}= 0", "a": f"x = {lo} и x = {hi}"}
    if kind == "prog":
        a1, d, n = rnd.randint(2, 9), rnd.randint(2, 7), rnd.randint(8, 20)
        return {"q": f"Арифметическая прогрессия: первый член {a1}, разность {d}. Найдите {n}-й член.",
                "a": str(a1 + d * (n - 1))}
    if kind == "power":
        base, e = rnd.choice([2, 3, 5]), rnd.randint(2, 5)
        return {"q": f"Решите уравнение: {base}ˣ = {base ** e}", "a": f"x = {e}"}
    w, b = rnd.randint(2, 6), rnd.randint(3, 8)
    f = Fraction(w, w + b)
    return {"q": f"В коробке {w} {plural(w, 'белый', 'белых', 'белых')} и {b} {plural(b, 'чёрный', 'чёрных', 'чёрных')} шаров. Какова вероятность вытащить белый?",
            "a": f"{f.numerator}/{f.denominator}"}
