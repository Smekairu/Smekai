"""Работа с российскими языковыми моделями и распознаванием текста.

Поддерживаются GigaChat (Сбер) и YandexGPT. Выбор через переменную AI_PROVIDER.
Если ключей нет, бот продолжает работать: разбор заданий по фото просто отключается,
а математика с подсказками работает как раньше, она не требует модели.

Переменные окружения:
  AI_PROVIDER      gigachat | yandex | none
  GIGACHAT_AUTH    ключ авторизации из личного кабинета (строка Base64)
  GIGACHAT_SCOPE   GIGACHAT_API_PERS для физлиц, GIGACHAT_API_B2B для компаний
  YANDEX_API_KEY   ключ сервисного аккаунта
  YANDEX_FOLDER    идентификатор каталога
"""
import json, logging, os, ssl, time, urllib.request, urllib.error, uuid

log = logging.getLogger("ai")

PROVIDER = os.environ.get("AI_PROVIDER", "none").lower()
GIGA_AUTH = os.environ.get("GIGACHAT_AUTH", "")
GIGA_SCOPE = os.environ.get("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
YA_KEY = os.environ.get("YANDEX_API_KEY", "")
YA_FOLDER = os.environ.get("YANDEX_FOLDER", "")

# Сертификаты НУЦ Минцифры ставятся на сервер один раз, см. README.
CTX = ssl.create_default_context()

SYSTEM = (
    "Ты Мыслик, помощник школьника {grade} класса. "
    "Твоя задача не решить задание, а довести ребёнка до решения самого. "
    "Отвечай коротко, простыми словами, без формул там, где можно объяснить словами. "
    "Никогда не называй окончательный ответ, пока тебя об этом прямо не попросят. "
    "Задавай по одному вопросу за раз."
)

STEPS = {
    1: "Задай один наводящий вопрос по условию. Ответ не называй.",
    2: "Дай первую подсказку: с чего начать. Ответ не называй.",
    3: "Дай вторую подсказку: следующий шаг решения. Ответ не называй.",
    4: "Дай третью подсказку, почти доведи до ответа, но сам ответ не пиши.",
    5: "Теперь разбери решение по шагам и назови ответ.",
}


def available():
    return PROVIDER in ("gigachat", "yandex")


def _post(url, data, headers, timeout=40):
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers={**headers, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return json.loads(r.read().decode())


# ---------- GigaChat ----------
_giga = {"token": "", "exp": 0}


def _giga_token():
    if _giga["token"] and _giga["exp"] > time.time() + 60:
        return _giga["token"]
    body = f"scope={GIGA_SCOPE}".encode()
    req = urllib.request.Request(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth", data=body,
        headers={"Authorization": f"Basic {GIGA_AUTH}", "RqUID": str(uuid.uuid4()),
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        d = json.loads(r.read().decode())
    _giga["token"] = d["access_token"]
    _giga["exp"] = d.get("expires_at", 0) / 1000 or time.time() + 1500
    return _giga["token"]


def _giga_chat(messages):
    d = _post("https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
              {"model": os.environ.get("GIGACHAT_MODEL", "GigaChat"), "messages": messages,
               "temperature": 0.3, "max_tokens": 400},
              {"Authorization": f"Bearer {_giga_token()}"})
    return d["choices"][0]["message"]["content"].strip()


# ---------- YandexGPT ----------
def _yandex_chat(messages):
    model = f"gpt://{YA_FOLDER}/{os.environ.get('YANDEX_MODEL', 'yandexgpt-lite')}/latest"
    d = _post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
              {"modelUri": model,
               "completionOptions": {"temperature": 0.3, "maxTokens": 400},
               "messages": [{"role": m["role"], "text": m["content"]} for m in messages]},
              {"Authorization": f"Api-Key {YA_KEY}"})
    return d["result"]["alternatives"][0]["message"]["text"].strip()


def ask(grade, task_text, history, step):
    """Возвращает следующую реплику Мыслика: вопрос, подсказку или разбор."""
    if not available():
        return None
    messages = [{"role": "system", "content": SYSTEM.format(grade=grade)},
                {"role": "user", "content": f"Задание: {task_text}"}]
    for role, text in history[-6:]:
        messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": STEPS.get(step, STEPS[5])})
    try:
        return _giga_chat(messages) if PROVIDER == "gigachat" else _yandex_chat(messages)
    except urllib.error.HTTPError as e:
        log.error("модель отказала: %s %s", e.code, e.read().decode()[:200])
    except Exception as e:
        log.error("модель недоступна: %s", e)
    return None


# ---------- распознавание текста с фотографии ----------
def ocr(image_bytes):
    """Возвращает текст задания с фотографии или None."""
    if not YA_KEY or not YA_FOLDER:
        return None
    import base64
    try:
        d = _post("https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText",
                  {"mimeType": "JPEG", "languageCodes": ["ru", "en"], "model": "page",
                   "content": base64.b64encode(image_bytes).decode()},
                  {"Authorization": f"Api-Key {YA_KEY}", "x-folder-id": YA_FOLDER,
                   "x-data-logging-enabled": "false"}, timeout=60)
        return (d.get("result", {}).get("textAnnotation", {}).get("fullText") or "").strip() or None
    except urllib.error.HTTPError as e:
        log.error("распознавание отказало: %s %s", e.code, e.read().decode()[:200])
    except Exception as e:
        log.error("распознавание недоступно: %s", e)
    return None
