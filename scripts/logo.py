"""Рисует логотип Смекай: Мыслик и подпись «С в рамке + Смекай» (аватарки каналов), тёмный вариант, значок С для шапки сайта и favicon.

Запуск (нужен Playwright и запущенный рядом сервер с сайтом):
  python -m http.server 8765 &
  python scripts/logo.py
Файлы: assets/brand/logo-smekai.png (1024, жёлтый), logo-smekai-dark.png (1024, тёмный),
assets/brand/mark.png (128, буква С на жёлтом, в шапке сайта скругляется CSS), assets/favicon.png (64).
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
.word{{position:absolute;left:0;right:0;top:{wy}px;display:flex;align-items:center;justify-content:center;gap:{gap}px;font:800 {ws}px/1 'Unbounded';color:{ink};letter-spacing:-.01em}}
.word i{{width:{fs}px;height:{fs}px;border-radius:{fr}px;background:{fbg};color:{fink};display:grid;place-items:center;font-style:normal;font-size:{fz}px;line-height:1}}
.big{{position:absolute;inset:0;display:grid;place-items:center;font:800 {cz}px/1 'Unbounded';color:{cink}}}
</style></head><body>{face_html}{word}</body></html>"""

VARIANTS = [
    # файл, размер, фон, цвет слова, лицо, отступ сверху, рамка С (фон, буква), только буква С (цвет) или None
    ("assets/brand/logo-smekai.png", 1024, "radial-gradient(circle at 50% 38%,#FFE391,#FFC933 72%)", "#1B1F3B", 590, 40, ("#1B1F3B", "#FFC933"), None),
    ("assets/brand/logo-smekai-dark.png", 1024, "radial-gradient(circle at 50% 38%,#2E3668,#1B1F3B 72%)", "#FFFFFF", 590, 40, ("#FFC933", "#1B1F3B"), None),
    ("assets/brand/mark.png", 128, "#FFC933", "#5C4300", 0, 0, None, "#5C4300"),
    ("assets/favicon.png", 64, "#FFC933", "#5C4300", 0, 0, None, "#5C4300"),
]


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for out, w, bg, ink, face, top, frame, letter in VARIANTS:
            pg = await b.new_page(viewport={"width": w, "height": w})
            await pg.emulate_media(reduced_motion="reduce")
            ws = int(w * .10)
            if letter:
                face_html, word = "", f'<div class="big">С</div>'
            else:
                face_html = f'<myslik-face age="6" mood="idle"></myslik-face>'
                word = f'<div class="word"><i>С</i>Смекай</div>'
            fs = int(ws * 1.32)
            html = PAGE.format(base=BASE, w=w, bg=bg, ink=ink, face=face, top=top, face_html=face_html,
                               wy=int(w * .70), ws=ws, gap=int(ws * .32), fs=fs, fr=int(fs * .28), fz=int(ws * .86),
                               fbg=(frame or ("", ""))[0], fink=(frame or ("", ""))[1], cz=int(w * .68), cink=letter or "",
                               word=word)
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
