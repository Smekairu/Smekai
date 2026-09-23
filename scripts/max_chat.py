"""Диагностика бота МАКС: проверяет токен и ищет chat_id канала.

Запуск: GitHub -> Actions -> Проверить MAX -> Run workflow.
Скрипт никогда не падает, а печатает, что именно не получилось.
"""
import json, os, urllib.request, urllib.error

BASE = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")
TOKEN = os.environ.get("MAX_BOT_TOKEN", "").strip()

def call(path):
    """Возвращает (данные, описание ошибки)."""
    req = urllib.request.Request(BASE + path, headers={"Authorization": TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode() or "{}"), None
    except urllib.error.HTTPError as e:
        return None, f"код {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return None, str(e)

def main():
    print("Адрес API:", BASE)
    if not TOKEN:
        print("ОШИБКА: секрет MAX_BOT_TOKEN не задан или пустой.")
        print("GitHub -> Settings -> Secrets and variables -> Actions -> New repository secret.")
        return
    print("Токен получен, длина:", len(TOKEN))

    me, err = call("/me")
    if err:
        print("Токен не принят. Ответ MAX:", err)
        print("Проверьте, что скопирован весь токен, без пробелов и кавычек.")
        return
    print("Бот:", me.get("name"), "| username:", me.get("username"), "| user_id:", me.get("user_id"))

    chats, err = call("/chats?count=100")
    if err:
        print("Список чатов недоступен:", err)
    else:
        items = chats.get("chats", [])
        print("Чатов и каналов видно:", len(items))
        for c in items:
            print("  chat_id =", c.get("chat_id"), "|", c.get("title"),
                  "| тип:", c.get("type"), "| статус бота:", c.get("status"))
        if items:
            print("Нужный chat_id положите в секрет MAX_CHAT_ID.")
            return

    upd, err = call("/updates?limit=100&timeout=0")
    if err:
        print("События недоступны:", err)
    else:
        ids = []
        for u in upd.get("updates", []):
            cid = u.get("chat_id") or ((u.get("message") or {}).get("recipient") or {}).get("chat_id")
            print("  событие:", u.get("update_type"), "chat_id =", cid)
            if cid: ids.append(cid)
        canal = [i for i in ids if i < 0]
        if canal:
            print("Похоже, канал это chat_id =", canal[-1])
            print("Положите это число в MAX_CHAT_ID. Отрицательные id принадлежат каналам и группам,")
            print("положительные это личные диалоги с людьми.")
            return
        if not ids:
            print("Событий нет.")
    print("Итог: бот ещё не добавлен в канал. Сначала подписчиком, затем администратором")
    print("с правом публиковать сообщения, потом запустите проверку снова.")

if __name__ == "__main__":
    main()
