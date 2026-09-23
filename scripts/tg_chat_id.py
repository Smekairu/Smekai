"""Показывает id каналов и чатов, куда добавлен бот Telegram.

Запуск: GitHub -> Actions -> Узнать канал Telegram -> Run workflow.
Перед запуском добавьте бота администратором в канал и напишите там любое сообщение.
"""
import json, os, urllib.request, urllib.error

def get(path):
    url = f"https://api.telegram.org/bot{os.environ['TG_BOT_TOKEN']}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=35) as r:
            return json.loads(r.read().decode() or "{}"), None
    except urllib.error.HTTPError as e:
        return None, f"код {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return None, str(e)

def collect(data, seen):
    for u in data.get("result", []):
        for key in ("my_chat_member", "channel_post", "edited_channel_post", "message", "edited_message"):
            obj = u.get(key) or {}
            chat = obj.get("chat")
            if chat:
                seen[chat["id"]] = (chat.get("title") or chat.get("username") or chat.get("first_name") or "", chat.get("type"))
            fwd = (obj.get("forward_origin") or {}).get("chat") or obj.get("forward_from_chat")
            if fwd:
                seen[fwd["id"]] = (fwd.get("title") or "", fwd.get("type") + ", пересланное")

def main():
    if not os.environ.get("TG_BOT_TOKEN"):
        print("Нет секрета TG_BOT_TOKEN"); return
    me, err = get("getMe")
    if err:
        print("Токен не принят:", err); return
    print("Бот: @" + me["result"]["username"])

    hook, err = get("getWebhookInfo")
    if not err:
        url = (hook.get("result") or {}).get("url") or ""
        if url:
            print("ВНИМАНИЕ: у бота включён webhook:", url)
            print("Пока он включён, события сюда не приходят. Отключается вызовом deleteWebhook.")
            return
        print("Webhook не включён, это правильно.")

    seen = {}
    data, err = get("getUpdates?limit=100&timeout=0")
    if err:
        print("Не удалось получить события:", err); return
    print("Событий получено:", len(data.get("result", [])))
    collect(data, seen)

    if not seen:
        print("Ни одного чата не видно. По шагам:")
        print("1. Добавьте бота в канал администратором с правом публиковать сообщения.")
        print("2. Напишите в канале любое сообщение.")
        print("3. Если канал уже создан давно, перешлите любой его пост боту в личные сообщения.")
        print("4. Запустите проверку снова в тот же день, Telegram хранит события 24 часа.")
        return
    print("Найдено:")
    for cid, (title, ctype) in seen.items():
        print("  chat_id =", cid, "|", title, "|", ctype)
    print("Id закрытого канала положите в переменную TG_CHANNEL_CLOSED.")

if __name__ == "__main__":
    main()
