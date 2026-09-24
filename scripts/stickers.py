"""Рисует стикеры Мыслика и Льва из assets/myslik.js: PNG и WEBP 512, эмодзи 100, small 128, social 256,
анимации 512 (WEBM с прозрачностью, MP4 и GIF 320 на фоне).

Запуск (Playwright, Pillow, ffmpeg; рядом запущен сервер: python -m http.server 8765):
  python scripts/stickers.py sleepy            одно настроение для трёх персонажей
  python scripts/stickers.py sleepy --anim     и анимации
  python scripts/stickers.py all               все настроения
"""
import asyncio, subprocess, sys, shutil, tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://localhost:8765/"
WHO = {"junior": 2, "myslik": 5, "lev": 10}
BG = {"junior": "#FFC933", "myslik": "#FFC933", "lev": "#1B1F3B"}
MOODS = ["idle", "think", "yay", "party", "sad", "angry", "surprised", "sleepy", "wave", "love", "shy"]
PAGE = """<!doctype html><html><head><meta charset="utf-8"><script src="{base}assets/myslik.js"></script>
<style>html,body{{margin:0;background:transparent}}myslik-face{{display:block;width:{s}px;height:{s}px;margin:{pad}px}}</style></head>
<body><myslik-face age="{age}" mood="{mood}"></myslik-face></body></html>"""
OUT = {k: ROOT / "assets" / "pack" / k for k in ("sticker", "emoji", "small", "social")}
ANIM = ROOT / "assets" / "anim"


PAD = 120      # запас вокруг персонажа, чтобы ничего не обрезалось
BOX = (18, 475)  # как в первом наборе: отступ сверху и высота персонажа на холсте 512


def fit(im, box=None):
    """Обрезает по содержимому и ставит персонажа на холст 512 по центру, высота BOX[1]."""
    x0, y0, x1, y1 = box or im.getbbox()
    im = im.crop((x0, y0, x1, y1))
    k = min(BOX[1] / im.height, (512 - 2 * BOX[0]) / im.width)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    out = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    out.alpha_composite(im, ((512 - im.width) // 2, BOX[0]))
    return out


async def page_for(b, who, mood, size):
    size_v = size + 2 * PAD
    pg = await b.new_page(viewport={"width": size_v, "height": size_v})
    tmp = ROOT / "state" / f"_stk_{who}_{mood}.html"
    tmp.write_text(PAGE.format(base=BASE, s=size, pad=PAD, age=WHO[who], mood=mood), encoding="utf-8")
    await pg.goto(BASE + f"state/{tmp.name}")
    await pg.wait_for_timeout(700)
    # моргание и случайные взгляды мешают кадрам: выключаем таймеры компонента
    await pg.evaluate("""() => { const f = document.querySelector('myslik-face'); for (const k in (f._timers||{})) { clearTimeout(f._timers[k]); clearInterval(f._timers[k]); }
        f._scheduleBlink = () => {}; }""")
    return pg, tmp


async def still(b, who, mood):
    pg, tmp = await page_for(b, who, mood, 512)
    anims = "document.getAnimations().forEach(a => { a.pause(); a.currentTime = 0; })"
    await pg.evaluate(anims)
    await pg.wait_for_timeout(100)
    png = OUT["sticker"] / f"{who}-{mood}.png"
    await pg.screenshot(path=str(png), omit_background=True)
    await pg.close(); tmp.unlink()
    im = fit(Image.open(png).convert("RGBA"))
    im.save(png)
    im.save(OUT["sticker"] / f"{who}-{mood}.webp", "WEBP", quality=90, method=6)
    for k, s in (("emoji", 100), ("small", 128), ("social", 256)):
        r = im.resize((s, s), Image.LANCZOS)
        r.save(OUT[k] / f"{who}-{mood}.png")
        if k == "emoji":
            r.save(OUT[k] / f"{who}-{mood}.webp", "WEBP", quality=90, method=6)
    print("стикер:", who, mood)


async def anim(b, who, mood, secs=2.4, fps=30):
    pg, tmp = await page_for(b, who, mood, 512)
    d = Path(tempfile.mkdtemp())
    await pg.evaluate("document.getAnimations().forEach(a => a.pause())")
    n = int(secs * fps)
    for i in range(n):
        t = i * 1000 / fps
        await pg.evaluate(f"document.getAnimations().forEach(a => a.currentTime = {t})")
        await pg.screenshot(path=str(d / f"f{i:03d}.png"), omit_background=True)
    await pg.close(); tmp.unlink()
    frames = sorted(d.glob("f*.png"))
    boxes = [Image.open(f).getbbox() for f in frames]
    box = (min(x[0] for x in boxes), min(x[1] for x in boxes), max(x[2] for x in boxes), max(x[3] for x in boxes))
    for f in frames:
        fit(Image.open(f).convert("RGBA"), box).save(f)
    ff = ["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", str(d / "f%03d.png")]
    subprocess.run(ff + ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "44", "-deadline", "good", "-row-mt", "1", "-an",
                         str(ANIM / f"{who}-{mood}.webm")], check=True)
    bg = BG[who]
    flat = f"color=c={bg}:s=512x512:r={fps}[bg];[bg][0:v]overlay=shortest=1"
    subprocess.run(ff + ["-filter_complex", flat + ",fps=25,format=yuv420p", "-c:v", "libx264", "-crf", "24",
                         "-movflags", "+faststart", "-an", str(ANIM / f"{who}-{mood}.mp4")], check=True)
    subprocess.run(ff + ["-filter_complex", flat + ",fps=20,scale=320:320:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                         "-loop", "0", str(ANIM / f"{who}-{mood}.gif")], check=True)
    shutil.rmtree(d)
    print("анимация:", who, mood)


async def main():
    args = sys.argv[1:]
    moods = MOODS if "all" in args else [a for a in args if a in MOODS]
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for who in WHO:
            for m in moods:
                await still(b, who, m)
                if "--anim" in args and (ANIM / f"{who}-{m}.webm").exists():
                    await anim(b, who, m)
        await b.close()

asyncio.run(main())
