"""Создаёт наборы стикеров и эмодзи Смекай в Telegram через Bot API.

Что создаётся (владелец набора: ADMIN_ID, то есть вы):
  smekai_myslik_by_<бот>        обычные стикеры, 11 настроений Мыслика (WEBP 512)
  smekai_lev_by_<бот>           обычные стикеры Льва
  smekai_anim_by_<бот>          видеостикеры, 10 анимаций Мыслика (WEBM)
  smekai_emoji_by_<бот>         набор эмодзи, 22 штуки (100x100)

Запуск на сервере или с компьютера, где есть Python:
  set -a; . ./.env; set +a
  python stickerpack.py            создать все наборы
  python stickerpack.py --only emoji   только эмодзи
  python stickerpack.py --delete   удалить наборы

Ограничения Telegram, о которых стоит знать:
  - набор эмодзи создаётся ботом, а пользоваться им в сообщениях могут подписчики Premium;
    каналы могут ставить эти эмодзи в реакции и посты после первых уровней буста;
  - названия наборов должны заканчиваться на _by_<имя бота>, это правило Telegram;
  - видеостикер: WEBM VP9, 512x512, до 3 секунд, до 256 КБ.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error, uuid
from pathlib import Path

TOKEN = os.environ["TG_BOT_TOKEN"]
OWNER = int(os.environ["ADMIN_ID"])
ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "assets" / "pack"
ANIM = ROOT / "assets" / "anim"
API = f"https://api.telegram.org/bot{TOKEN}"

# настроение -> эмодзи, которым стикер отзывается на поиск
EMOJI = {"idle": "🙂", "think": "🤔", "yay": "😄", "party": "🥳", "sad": "😢", "angry": "😠",
         "surprised": "😮", "sleepy": "😴", "wave": "👋", "love": "😍", "shy": "😊"}


def call(method, data=None, files=None):
    if files:
        boundary = uuid.uuid4().hex
        body = b""
        for k, v in (data or {}).items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        for k, (fname, content) in files.items():
            body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\n"
                     f"Content-Type: application/octet-stream\r\n\r\n").encode() + content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(f"{API}/{method}", data=body,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    else:
        req = urllib.request.Request(f"{API}/{method}", data=json.dumps(data or {}).encode(),
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"ok": False, "description": e.read().decode()[:300]}


def bot_name():
    return call("getMe")["result"]["username"]


def upload(path):
    """Загружает файл заранее, возвращает file_id для набора."""
    fmt = "video" if path.suffix == ".webm" else "static"
    r = call("uploadStickerFile", {"user_id": OWNER, "sticker_format": fmt},
             files={"sticker": (path.name, path.read_bytes())})
    if not r.get("ok"):
        print("  не загрузился", path.name, r.get("description")); return None
    return r["result"]["file_id"]


def create_set(name, title, items, sticker_type="regular"):
    """items: список (путь, эмодзи). Первый стикер создаёт набор, остальные добавляются."""
    print(f"Набор {name}: {title}")
    first = True
    for path, emoji in items:
        if not path.exists():
            print("  нет файла", path.name); continue
        fid = upload(path)
        if not fid:
            continue
        fmt = "video" if path.suffix == ".webm" else "static"
        sticker = {"sticker": fid, "format": fmt, "emoji_list": [emoji]}
        if first:
            r = call("createNewStickerSet", {"user_id": OWNER, "name": name, "title": title,
                                             "stickers": [sticker], "sticker_type": sticker_type})
            first = False
        else:
            r = call("addStickerToSet", {"user_id": OWNER, "name": name, "sticker": sticker})
        print("  ", path.name, "ок" if r.get("ok") else r.get("description"))
        time.sleep(0.4)
    print("  ссылка: https://t.me/addstickers/" + name if sticker_type == "regular" else "  ссылка: https://t.me/addemoji/" + name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["myslik", "lev", "anim", "emoji"])
    ap.add_argument("--delete", action="store_true")
    a = ap.parse_args()
    bot = bot_name()
    sets = {
        "myslik": (f"smekai_myslik_by_{bot}", "Мыслик · Смекай",
                   [(PACK / "sticker" / f"myslik-{m}.webp", e) for m, e in EMOJI.items()], "regular"),
        "lev": (f"smekai_lev_by_{bot}", "Лев · Смекай",
                [(PACK / "sticker" / f"lev-{m}.webp", e) for m, e in EMOJI.items()], "regular"),
        "anim": (f"smekai_anim_by_{bot}", "Мыслик живой · Смекай",
                 [(ANIM / f"myslik-{m}.webm", e) for m, e in EMOJI.items() if m != "shy"], "regular"),
        "emoji": (f"smekai_emoji_by_{bot}", "Эмодзи Смекай",
                  [(PACK / "emoji" / f"{who}-{m}.webp", e) for who in ("myslik", "lev") for m, e in EMOJI.items()], "custom_emoji"),
    }
    for key, (name, title, items, kind) in sets.items():
        if a.only and a.only != key:
            continue
        if a.delete:
            print(name, call("deleteStickerSet", {"name": name}).get("ok"))
            continue
        create_set(name, title, items, kind)


if __name__ == "__main__":
    main()
