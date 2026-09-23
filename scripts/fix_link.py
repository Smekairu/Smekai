"""Меняет ссылку на кнопке у уже опубликованного поста в Telegram.

Запускается вручную из GitHub: Actions -> Исправить ссылку в посте -> Run workflow.
Номер поста берётся из ссылки на пост: t.me/smekai_ru/5 -> 5
"""
import json, os, sys, urllib.request, urllib.parse

QUIZ = "https://smekairu.github.io/Smekai/"

def http(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")

def main():
    token = os.environ.get("TG_BOT_TOKEN")
    chat = os.environ.get("TG_CHANNEL") or "@smekai_ru"
    mid = os.environ.get("MSG_ID", "").strip()
    text = os.environ.get("BTN_TEXT") or "Пройти викторину"
    url = os.environ.get("BTN_URL") or QUIZ
    if not token:
        print("Нет секрета TG_BOT_TOKEN"); sys.exit(1)
    if not mid.isdigit():
        print("Укажите номер поста числом"); sys.exit(1)
    data = {"chat_id": chat, "message_id": int(mid),
            "reply_markup": {"inline_keyboard": [[{"text": text, "url": url}]]}}
    try:
        r = http(f"https://api.telegram.org/bot{token}/editMessageReplyMarkup", data)
    except urllib.error.HTTPError as e:
        print("Telegram отказал:", e.read().decode()); sys.exit(1)
    print("Готово:", r.get("ok"), "->", url)

if __name__ == "__main__":
    main()
