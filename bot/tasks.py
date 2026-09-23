"""Задания для бота: математика 1-11 класса с подсказками и разбором по шагам.

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
    if grade <= 6:
        return random.choice([_order5, _part, _percent, _speed, _two_parts])()
    if grade <= 8:
        return random.choice([_linear, _raise, _pythagoras, _mean])()
    return random.choice([_quadratic, _progression, _power, _discount])()


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


# ---------- 7-8 класс ----------

def _linear():
    x, a, b = random.randint(2, 12), random.randint(2, 9), random.randint(3, 20)
    return {"q": f"Решите уравнение: {a}x + {b} = {a * x + b}", "a": x,
            "hints": ["Перенесите свободный член вправо, знак поменяется.",
                      f"{a}x = {a * x + b} − {b} = {a * x}.",
                      f"Разделите обе части на {a}."],
            "steps": f"{a}x = {a * x}; x = {a * x} : {a} = {x}"}


def _raise():
    p, w = random.choice([15, 18, 24, 35]), random.choice([200, 400, 800, 1200])
    return {"q": f"Товар стоил {w} рублей и подорожал на {p} процентов. Какой стала цена?",
            "a": w + w * p // 100,
            "hints": ["Сначала найдите, сколько рублей составляют проценты.",
                      f"{w} · {p} : 100 = {w * p // 100}.",
                      "Прибавьте к старой цене."],
            "steps": f"{w} · {p} : 100 = {w * p // 100}; {w} + {w * p // 100} = {w + w * p // 100}"}


def _pythagoras():
    a, b = random.choice([(3, 4), (6, 8), (5, 12), (9, 12), (8, 15)])
    c = round((a * a + b * b) ** .5)
    return {"q": f"Катеты прямоугольного треугольника {a} и {b}. Найдите гипотенузу.", "a": c,
            "hints": ["Теорема Пифагора: квадрат гипотенузы равен сумме квадратов катетов.",
                      f"{a}² + {b}² = {a * a + b * b}.",
                      f"Извлеките корень из {a * a + b * b}."],
            "steps": f"{a}² + {b}² = {a * a + b * b}; √{a * a + b * b} = {c}"}


def _mean():
    n = random.randint(3, 5)
    m = random.randint(4, 9)
    nums = [m + d for d in random.sample([-3, -2, -1, 0, 1, 2, 3], n)]
    nums[-1] += m * n - sum(nums)      # подгоняем, чтобы среднее было целым
    return {"q": f"Найдите среднее арифметическое чисел: {', '.join(map(str, nums))}.", "a": m,
            "hints": ["Среднее это сумма всех чисел, делённая на их количество.",
                      f"Сумма равна {sum(nums)}.",
                      f"Разделите {sum(nums)} на {n}."],
            "steps": f"{' + '.join(map(str, nums))} = {sum(nums)}; {sum(nums)} : {n} = {m}"}


# ---------- 9-11 класс ----------

def _quadratic():
    r1, r2 = random.randint(-6, 6), random.randint(-6, 6)
    if r1 == r2:
        r2 += 1
    b, c = -(r1 + r2), r1 * r2
    sb = f"+ {b}" if b >= 0 else f"− {-b}"
    sc = f"+ {c}" if c >= 0 else f"− {-c}"
    return {"q": f"Решите уравнение и введите больший корень: x² {sb}x {sc} = 0", "a": max(r1, r2),
            "hints": ["Теорема Виета: сумма корней равна второму коэффициенту с обратным знаком, "
                      "произведение равно свободному члену.",
                      f"Сумма корней {r1 + r2}, произведение {c}.",
                      f"Подберите два числа: {min(r1, r2)} и {max(r1, r2)}."],
            "steps": f"x₁ = {r1}, x₂ = {r2}; больший корень {max(r1, r2)}"}


def _progression():
    a1, d, n = random.randint(2, 9), random.randint(2, 7), random.randint(8, 20)
    return {"q": f"Арифметическая прогрессия: первый член {a1}, разность {d}. Найдите {n}-й член.",
            "a": a1 + d * (n - 1),
            "hints": ["Формула: aₙ = a₁ + d(n − 1).",
                      f"d(n − 1) = {d} · {n - 1} = {d * (n - 1)}.",
                      "Прибавьте первый член."],
            "steps": f"a{n} = {a1} + {d} · {n - 1} = {a1 + d * (n - 1)}"}


def _power():
    base, e = random.choice([2, 3, 5]), random.randint(2, 5)
    return {"q": f"Решите уравнение: {base}ˣ = {base ** e}", "a": e,
            "hints": [f"Представьте правую часть как степень числа {base}.",
                      f"{base} · {base} · … сколько раз даст {base ** e}?",
                      "Если основания равны, равны и показатели."],
            "steps": f"{base ** e} = {base}^{e}, значит x = {e}"}


def _discount():
    w, p = random.choice([1500, 2400, 3200, 4800]), random.choice([10, 15, 20, 25])
    return {"q": f"Куртка стоила {w} рублей, на распродаже скидка {p} процентов. "
                 f"Сколько рублей стоит куртка со скидкой?", "a": w - w * p // 100,
            "hints": ["Скидка это часть цены. Найдите её в рублях.",
                      f"{w} · {p} : 100 = {w * p // 100}.",
                      "Вычтите скидку из цены."],
            "steps": f"{w} · {p} : 100 = {w * p // 100}; {w} − {w * p // 100} = {w - w * p // 100}"}
