"""Задания для бота: математика 1-6 класса с подсказками и разбором по шагам.

Ответ всегда число, оно считается программой, а не нейросетью.
Поэтому ошибиться в проверке бот не может.
"""
import random


def make(grade):
    grade = grade or 3
    if grade <= 2:
        return random.choice([_add, _sub, _mult_small, _rows])()
    if grade <= 4:
        return random.choice([_mult, _div, _order, _price])()
    return random.choice([_order5, _part, _percent, _speed, _two_parts])()


# ---------- 1-2 класс ----------

def _add():
    a, b = random.randint(23, 58), random.randint(14, 39)
    return {"q": f"Посчитай: {a} + {b}", "a": a + b,
            "hints": ["Сложи сначала десятки, потом единицы.",
                      f"Десятки: {a // 10 * 10} + {b // 10 * 10} = {a // 10 * 10 + b // 10 * 10}.",
                      f"Единицы: {a % 10} + {b % 10} = {a % 10 + b % 10}. Осталось сложить два результата."],
            "steps": f"{a // 10 * 10} + {b // 10 * 10} = {a // 10 * 10 + b // 10 * 10}, "
                     f"{a % 10} + {b % 10} = {a % 10 + b % 10}, вместе {a + b}"}


def _sub():
    a, b = random.randint(52, 96), random.randint(14, 38)
    return {"q": f"Посчитай: {a} − {b}", "a": a - b,
            "hints": ["Вычитай по частям: сначала десятки, потом единицы.",
                      f"{a} − {b // 10 * 10} = {a - b // 10 * 10}.",
                      f"Теперь от {a - b // 10 * 10} отними {b % 10}."],
            "steps": f"{a} − {b // 10 * 10} = {a - b // 10 * 10}, затем − {b % 10} = {a - b}"}


def _mult_small():
    a, b = random.randint(2, 5), random.randint(3, 9)
    return {"q": f"Посчитай: {a} · {b}", "a": a * b,
            "hints": [f"Это {a} раз по {b}.",
                      f"Сложи {b} + {b} и посмотри, сколько получилось за два раза.",
                      f"Вспомни таблицу умножения на {a}."],
            "steps": f"{a} · {b} это {b} сложить {a} раза, получится {a * b}"}


def _rows():
    r, c = random.randint(3, 7), random.randint(3, 6)
    return {"q": f"В коробке {r} рядов, в каждом по {c} конфет. Сколько конфет всего?", "a": r * c,
            "hints": ["Рядов несколько, в каждом поровну. Это умножение.",
                      f"Посчитай {r} раз по {c}.",
                      f"{r} · {c} — вспомни таблицу."],
            "steps": f"{r} рядов по {c} конфет, значит {r} · {c} = {r * c}"}


# ---------- 3-4 класс ----------

def _mult():
    a, b = random.randint(14, 48), random.randint(3, 9)
    t, o = a // 10 * 10, a % 10
    return {"q": f"Посчитай: {a} · {b}", "a": a * b,
            "hints": ["Разложи первое число на десятки и единицы.",
                      f"{t} · {b} = {t * b}.",
                      f"{o} · {b} = {o * b}. Сложи оба результата."],
            "steps": f"{t} · {b} = {t * b}, {o} · {b} = {o * b}, вместе {a * b}"}


def _div():
    b, q = random.randint(3, 9), random.randint(12, 40)
    return {"q": f"Посчитай: {b * q} : {b}", "a": q,
            "hints": [f"Спроси себя: сколько раз по {b} помещается в {b * q}.",
                      f"Попробуй прикинуть: {b} · 10 = {b * 10}. Это больше или меньше?",
                      f"Ответ между {max(1, q - 3)} и {q + 3}."],
            "steps": f"{b} · {q} = {b * q}, значит {b * q} : {b} = {q}"}


def _order():
    a, b, c = random.randint(40, 90), random.randint(3, 9), random.randint(4, 11)
    return {"q": f"Посчитай: {a} − {b} · {c}", "a": a - b * c,
            "hints": ["Сначала умножение, потом вычитание.",
                      f"{b} · {c} = {b * c}.",
                      f"Теперь {a} − {b * c}."],
            "steps": f"{b} · {c} = {b * c}, затем {a} − {b * c} = {a - b * c}"}


def _price():
    price, n = random.choice([25, 30, 45, 60]), random.randint(3, 8)
    return {"q": f"Тетрадь стоит {price} рублей. Сколько стоят {n} тетрадей?", "a": price * n,
            "hints": ["Цена одной известна, нужно узнать цену нескольких. Это умножение.",
                      f"{price} · {n}.",
                      f"Посчитай {price} · 10 = {price * 10} и убери лишнее."],
            "steps": f"{price} · {n} = {price * n} рублей"}


# ---------- 5-6 класс ----------

def _order5():
    a, b, c, d = random.randint(90, 160), random.randint(3, 8), random.randint(9, 18), random.randint(2, 9)
    return {"q": f"Вычислите: {a} − {b} · ({c} + {d})", "a": a - b * (c + d),
            "hints": ["Порядок действий: скобки, умножение, вычитание.",
                      f"В скобках {c} + {d} = {c + d}.",
                      f"{b} · {c + d} = {b * (c + d)}."],
            "steps": f"{c} + {d} = {c + d}; {b} · {c + d} = {b * (c + d)}; "
                     f"{a} − {b * (c + d)} = {a - b * (c + d)}"}


def _part():
    d = random.choice([4, 5, 6, 8])
    n = random.randint(1, d - 1)
    whole = d * random.randint(4, 12)
    return {"q": f"Найдите {n}/{d} от числа {whole}.", "a": whole // d * n,
            "hints": [f"Сначала найдите одну часть: разделите {whole} на {d}.",
                      f"Одна часть равна {whole // d}.",
                      f"Теперь возьмите {n} таких частей."],
            "steps": f"{whole} : {d} = {whole // d}; {whole // d} · {n} = {whole // d * n}"}


def _percent():
    p, whole = random.choice([10, 20, 25, 40, 50]), random.choice([120, 240, 360, 480, 600])
    return {"q": f"Найдите {p} процентов от {whole}.", "a": whole * p // 100,
            "hints": ["Один процент это сотая часть числа.",
                      f"{whole} : 100 = {whole / 100:g}.",
                      f"Умножьте {whole / 100:g} на {p}."],
            "steps": f"{whole} : 100 = {whole / 100:g}; {whole / 100:g} · {p} = {whole * p // 100}"}


def _speed():
    v, t = random.choice([12, 15, 18, 20, 24]), random.randint(2, 5)
    return {"q": f"Велосипедист едет со скоростью {v} км/ч. Какой путь он проедет за {t} часа?",
            "a": v * t,
            "hints": ["Путь равен скорости, умноженной на время.",
                      f"За один час {v} км.",
                      f"Значит за {t} часа {v} · {t}."],
            "steps": f"S = v · t = {v} · {t} = {v * t} км"}


def _two_parts():
    small = random.randint(6, 20)
    k = random.randint(2, 4)
    total = small + small * k
    return {"q": f"Два числа в сумме дают {total}, причём второе в {k} раза больше первого. "
                 f"Найдите меньшее число.", "a": small,
            "hints": ["Обозначьте меньшее число за одну часть.",
                      f"Тогда большее это {k} части, а вместе {k + 1} часть.",
                      f"Разделите {total} на {k + 1}."],
            "steps": f"Всего частей {k + 1}; {total} : {k + 1} = {small}; "
                     f"большее число {small * k}"}
