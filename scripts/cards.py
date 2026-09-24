"""Рисует картинки к постам: квадрат 1080x1080 со стикером Мыслика или Льва.

Запуск на компьютере, где есть Python и Playwright:
  pip install playwright && playwright install chromium
  python scripts/cards.py posts/cards.json

Файл описания: список карточек
  {"file": "assets/posts/2026-09-25-1830.jpg", "kicker": "Новое", "title": "Личный кабинет открыт",
   "sub": "Заниматься с Мысликом на планшете и компьютере", "theme": "sun",
   "stickers": ["myslik-wave"], "date": "25 сентября"}
Темы: sun, blue, mint, peach, navy, cream, white. Стикеры из assets/pack/sticker.
"""
import asyncio, html, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = {
    "sun":   ("radial-gradient(circle at 70% 30%,#FFE08A,#FFC933 70%)", "#1B1F3B", "#5C4300"),
    "blue":  ("radial-gradient(circle at 70% 30%,#EAF1FF,#CFE0FF 75%)", "#1B1F3B", "#2F63D6"),
    "mint":  ("radial-gradient(circle at 70% 30%,#EFFBF5,#CDEFE0 75%)", "#1B1F3B", "#17875E"),
    "peach": ("radial-gradient(circle at 70% 30%,#FFF1EA,#FFD9C7 75%)", "#1B1F3B", "#C0512B"),
    "navy":  ("radial-gradient(circle at 70% 30%,#2A3160,#1B1F3B 75%)", "#FFFFFF", "#FFC933"),
    "cream": ("radial-gradient(circle at 70% 30%,#FFFBF0,#FFF0C9 75%)", "#1B1F3B", "#B7791F"),
    "white": ("linear-gradient(180deg,#FFFFFF,#F2F4FA)", "#1B1F3B", "#3E7BFA"),
}

TPL = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{root}/assets/fonts.css">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;overflow:hidden;background:{bg};color:{ink};font-family:'Golos Text',sans-serif;position:relative}}
.brand{{position:absolute;left:72px;top:64px;display:flex;align-items:center;gap:16px;font:800 38px 'Unbounded';color:{ink}}}
.brand img{{width:60px;height:60px;border-radius:17px;box-shadow:0 4px 14px rgba(27,31,59,.18)}}
.date{{position:absolute;right:72px;top:78px;font:600 28px 'Golos Text';opacity:.7}}
.kicker{{position:absolute;left:72px;top:190px;font:700 30px 'Golos Text';color:{accent};letter-spacing:.02em;text-transform:uppercase}}
.title{{position:absolute;left:72px;top:246px;width:{tw}px;font:800 {ts}px/1.12 'Unbounded';letter-spacing:-.01em}}
.sub{{position:absolute;left:72px;bottom:86px;width:480px;font:500 34px/1.35 'Golos Text';opacity:.86}}
.st{{position:absolute;bottom:40px;filter:drop-shadow(0 18px 30px rgba(27,31,59,.22))}}
.s1{{right:20px;width:560px;bottom:20px}}
.s2a{{right:280px;width:350px;bottom:36px}} .s2b{{right:10px;width:340px;bottom:50px}}
.two .sub{{width:340px}}
.url{{position:absolute;right:72px;bottom:40px;font:600 22px 'Golos Text';opacity:.55}}
</style></head><body class="{cls}">
<div class="brand"><img src="{root}/assets/brand/mark.png" alt="">Смекай</div><div class="date">{date}</div>
<div class="kicker">{kicker}</div><div class="title">{title}</div>
<div class="sub">{sub}</div>{stickers}
</body></html>"""


def page(c):
    bg, ink, accent = THEMES.get(c.get("theme", "sun"), THEMES["sun"])
    st = c.get("stickers") or ["myslik-idle"]
    if len(st) == 1:
        imgs = f'<img class="st s1" src="{ROOT.as_uri()}/assets/pack/sticker/{st[0]}.png">'
    else:
        imgs = (f'<img class="st s2a" src="{ROOT.as_uri()}/assets/pack/sticker/{st[0]}.png">'
                f'<img class="st s2b" src="{ROOT.as_uri()}/assets/pack/sticker/{st[1]}.png">')
    title = c["title"]
    ts = 84 if len(title) <= 22 else 72 if len(title) <= 36 else 62
    logo, logo_ink = ("#1B1F3B", "#FFC933") if c.get("theme", "sun") == "sun" else ("#FFC933", "#5C4300")
    return TPL.format(root=ROOT.as_uri(), bg=bg, ink=ink, accent=accent, logo=logo, logo_ink=logo_ink, date=html.escape(c.get("date", "")),
                      kicker=html.escape(c.get("kicker", "")), title=html.escape(title), sub=html.escape(c.get("sub", "")),
                      stickers=imgs, ts=ts, tw=900, cls="two" if len(st) > 1 else "one")


async def render(cards):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1080})
        tmp = ROOT / "state" / "_card.html"
        for c in cards:
            tmp.write_text(page(c), encoding="utf-8")
            await pg.goto(tmp.as_uri())
            await pg.wait_for_timeout(250)
            out = ROOT / c["file"]
            out.parent.mkdir(parents=True, exist_ok=True)
            await pg.screenshot(path=str(out), type="jpeg", quality=86)
            print("готово:", c["file"])
        tmp.unlink(missing_ok=True)
        await b.close()


if __name__ == "__main__":
    asyncio.run(render(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))))
