"""Показывает chat_id каналов, где бот МАКС уже администратор.

Запуск: GitHub -> Actions -> Проверить MAX -> Run workflow.
Полученное число нужно положить в секрет MAX_CHAT_ID.
"""
import json, os, sys, urllib.request, urllib.error

BASE = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")

def get(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": os.environ["MAX_BOT_TOKEN"]})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")

def main():
    if not os.environ.get("MAX_BOT_TOKEN"):
        print("Нет секрета MAX_BOT_TOKEN"); sys.exit(1)
    try:
        me = get("/me")
        print("Бот:", me.get("name"), "@" + str(me.get("username")))
    except urllib.error.HTTPError as e:
        print("Токен не принят:", e.read().decode()); sys.exit(1)

    found = []
    try:
        for c in get("/chats?count=100").get("chats", []):
            found.append((c.get("chat_id"), c.get("title"), c.get("type"), c.get("status")))
    except Exception as e:
        print("Список чатов недоступен:", getattr(e, "code", e))
    if not found:
        try:
            for u in get("/updates?limit=100&timeout=1").get("updates", []):
                cid = u.get("chat_id") or (u.get("message") or {}).get("recipient", {}).get("chat_id")
                if cid and cid not in [f[0] for f in found]:
                    found.append((cid, u.get("update_type"), "", ""))
        except Exception as e:
            print("События недоступны:", getattr(e, "code", e))

    if not found:
        print("Чатов не видно. Добавьте бота в канал администратором с правом публикации,")
        print("напишите в канале любое сообщение и запустите проверку снова.")
        sys.exit(1)
    print("Найдено:")
    for f in found:
        print("  chat_id =", f[0], "|", " | ".join(str(x) for x in f[1:] if x))
    print("Положите нужный chat_id в секрет MAX_CHAT_ID.")

if __name__ == "__main__":
    main()
