"""Рисует логотип Смекай с Мысликом: квадрат для аватарок каналов, тёмный вариант, значок сайта.

Запуск (нужен Playwright и запущенный рядом сервер с сайтом):
  python -m http.server 8765 &
  python scripts/logo.py
Файлы: assets/brand/logo-smekai.png (1024, жёлтый), logo-smekai-dark.png (1024, тёмный),
assets/brand/mark.png (128, значок для шапки), assets/favicon.png (64).
"""
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://localhost:8765/"

PAGE = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{base}assets/fonts.css">
<script src="{base}assets/myslik.js"></script><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{w}px;overflow:hidden;background:{bg};position:relative}}
myslik-face{{position:absolute;left:50%;top:{top}px;width:{face}px;height:{face}px;transform:translateX(-50%)}}
.word{{position:absolute;left:0;right:0;top:{wy}px;text-align:center;font:800 {ws}px/1 'Unbounded';color:{ink};letter-spacing:-.01em}}
</style></head><body><myslik-face age="6" mood="{mood}"></myslik-face>{word}</body></html>"""

VARIANTS = [
    ("assets/brand/logo-smekai.png", 1024, "radial-gradient(circle at 50% 38%,#FFE391,#FFC933 72%)", "#1B1F3B", 610, 44, "idle", True),
    ("assets/brand/logo-smekai-dark.png", 1024, "radial-gradient(circle at 50% 38%,#2E3668,#1B1F3B 72%)", "#FFFFFF", 610, 44, "idle", True),
    ("assets/brand/mark.png", 128, "radial-gradient(circle at 50% 38%,#FFE391,#FFC933 72%)", "#1B1F3B", 132, -6, "idle", False),
    ("assets/favicon.png", 64, "radial-gradient(circle at 50% 38%,#FFE391,#FFC933 72%)", "#1B1F3B", 68, -4, "idle", False),
]


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for out, w, bg, ink, face, top, mood, word in VARIANTS:
            pg = await b.new_page(viewport={"width": w, "height": w})
            await pg.emulate_media(reduced_motion="reduce")
            html = PAGE.format(base=BASE, w=w, bg=bg, ink=ink, face=face, top=top, mood=mood,
                               wy=int(w * .735), ws=int(w * .122),
                               word='<div class="word">Смекай</div>' if word else "")
            tmp = ROOT / "state" / "_logo.html"
            tmp.write_text(html, encoding="utf-8")
            await pg.goto(BASE + "state/_logo.html")
            await pg.wait_for_timeout(900)
            await pg.screenshot(path=str(ROOT / out))
            tmp.unlink()
            await pg.close()
            print("готово:", out)
        await b.close()

asyncio.run(main())
