"""Голос Мыслика: синтез речи через Yandex SpeechKit, отправка голосовым сообщением.

Три манеры на одного персонажа, ребёнок выбирает при знакомстве:
  boy     мальчику: молодой, бодрый
  girl    девочке: тёплый, живой
  parent  родителю: спокойный, взрослый
  off     без голоса

Переменные окружения:
  YANDEX_API_KEY, YANDEX_FOLDER   те же, что для распознавания фото
  VOICE_BOY, VOICE_GIRL, VOICE_PARENT   имена голосов, по умолчанию anton, masha, alexander
  VOICE_EMOTION                   оттенок для голосов, где он есть: good, neutral

Живость даёт не только голос: ударения ставим знаком плюс перед гласной (Мы+слик),
паузы меткой sil<[400]>, фразы короткие. Смотри функцию prep().
"""
import logging, os, re, ssl, urllib.parse, urllib.request, urllib.error

log = logging.getLogger("voice")

YA_KEY = os.environ.get("YANDEX_API_KEY", "")
YA_FOLDER = os.environ.get("YANDEX_FOLDER", "")
VOICES = {
    "boy": os.environ.get("VOICE_BOY", "anton"),
    "girl": os.environ.get("VOICE_GIRL", "masha"),
    "parent": os.environ.get("VOICE_PARENT", "alexander"),
}
SPEED = {"boy": "1.05", "girl": "1.0", "parent": "0.95"}
EMOTION = os.environ.get("VOICE_EMOTION", "")
CTX = ssl.create_default_context()

# слова, где синтез ошибается в ударении
STRESS = {
    "мыслик": "мы+слик", "мыслика": "мы+слика", "мыслику": "мы+слику",
    "звонит": "звон+ит", "каталог": "катал+ог", "договор": "догов+ор", "красивее": "крас+ивее",
    "шарф": "ш+арф", "торты": "т+орты", "банты": "б+анты",
}


def available():
    return bool(YA_KEY and YA_FOLDER)


def prep(text):
    """Готовит текст к озвучке: убирает разметку и эмодзи, ставит ударения и паузы."""
    t = re.sub(r"<[^>]+>", "", str(text))
    t = re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", t)
    for w, s in STRESS.items():
        def keep_case(m, s=s):
            return s[0].upper() + s[1:] if m.group(0)[0].isupper() else s
        t = re.sub(rf"\b{w}\b", keep_case, t, flags=re.I)
    t = re.sub(r"([.!?])\s+", r"\1 sil<[350]> ", t)      # пауза между фразами
    t = re.sub(r"[:;]\s+", " sil<[250]> ", t)
    return re.sub(r"\s+", " ", t).strip()


def synth(text, profile="boy"):
    """Возвращает OGG Opus байты или None."""
    if not available() or profile not in VOICES:
        return None
    data = {"text": prep(text)[:4900], "lang": "ru-RU", "voice": VOICES[profile],
            "speed": SPEED.get(profile, "1.0"), "format": "oggopus", "folderId": YA_FOLDER}
    if EMOTION:
        data["emotion"] = EMOTION
    req = urllib.request.Request("https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize",
                                 data=urllib.parse.urlencode(data).encode(),
                                 headers={"Authorization": f"Api-Key {YA_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        log.error("синтез отказал: %s %s", e.code, e.read().decode()[:200])
    except Exception as e:
        log.error("синтез недоступен: %s", e)
    return None


async def send_voice(bot, chat_id, text, profile):
    """Отправляет голосовое сообщение. Молча пропускает, если голос выключен или недоступен."""
    if profile in (None, "", "off") or not available():
        return False
    audio = synth(text, profile)
    if not audio:
        return False
    from aiogram.types import BufferedInputFile
    try:
        await bot.send_voice(chat_id, BufferedInputFile(audio, filename="myslik.ogg"))
        return True
    except Exception as e:
        log.warning("голосовое не отправлено: %s", e)
        return False
