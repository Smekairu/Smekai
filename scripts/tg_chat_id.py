"""Показывает id каналов и чатов, куда добавлен бот Telegram.

Запуск: GitHub -> Actions -> Узнать канал Telegram -> Run workflow.
Перед запуском добавьте бота администратором в нужный канал и напишите там любое сообщение.
"""
import json, os, urllib.request, urllib.error

def get(path):
    url = f"https://api.telegram.org/bot{os.environ['TG_BOT_TOKEN']}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode() or "{}"), None
    except urllib.error.HTTPError as e:
        return None, f"код {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return None, str(e)

def main():
    if not os.environ.get("TG_BOT_TOKEN"):
        print("Нет секрета TG_BOT_TOKEN"); return
    me, err = get("getMe")
    if err:
        print("Токен не принят:", err); return
    print("Бот: @" + me["result"]["username"])

    data, err = get("getUpdates?limit=100&allowed_updates=[\"my_chat_member\",\"channel_post\",\"message\"]")
    if err:
        print("Не удалось получить события:", err); return
    seen = {}
    for u in data.get("result", []):
        for key in ("my_chat_member", "channel_post", "message", "edited_channel_post"):
            chat = (u.get(key) or {}).get("chat")
            if chat:
                seen[chat["id"]] = (chat.get("title") or chat.get("username") or "", chat.get("type"))
    if not seen:
        print("Событий нет. Добавьте бота администратором в канал, напишите там сообщение и запустите снова.")
        print("Telegram хранит события 24 часа, поэтому проверку делайте в тот же день.")
        return
    print("Найдено:")
    for cid, (title, ctype) in seen.items():
        print("  chat_id =", cid, "|", title, "|", ctype)
    print("Id закрытого канала положите в переменную TG_CHANNEL_CLOSED.")

if __name__ == "__main__":
    main()
