# Мыслик: боты Telegram и MAX с подпиской и разбором заданий

Два бота из одной папки: `main.py` для Telegram и `max_bot.py` для MAX. Тексты и логика общие.
Короткая инструкция по настройке и запуску: `docs/boty.md`.

Что умеет:

- задания по математике 1-11 класса, ответ проверяется вычислением, а не нейросетью;
- три подсказки вместо готового ответа, разбор по шагам только после попыток;
- разбор домашки по фотографии: распознаёт текст и ведёт к ответу вопросами;
- недельный отчёт родителю, привязка родителя к ребёнку по коду;
- стикеры на события: приветствие, верно, ошибка, серия из трёх, думает, устал; персонаж по классу: младший Мыслик, Мыслик, Лев;
- голос: три манеры на выбор, ответы приходят голосовыми сообщениями;
- бесплатно 3 задания в день, по подписке 30, фото только по подписке;
- оплата через Tribute или другую площадку, доступ открывается автоматически;
- одноразовая ссылка в закрытый канал после оплаты.

## Файлы

| Файл | Зачем |
|---|---|
| `main.py` | бот Telegram |
| `max_bot.py` | бот MAX, та же логика через Bot API MAX |
| `common.py` | общие тексты, команды, персонаж по классу |
| `setup_bots.py` | имя, описание, команды и аватар обоим ботам (workflow «Настроить ботов») |
| `run_local.py`, `start-windows.bat` | запуск обоих ботов на своём компьютере, пока нет сервера |
| `webhook.py` | приём уведомлений об оплате |
| `db.py` | база SQLite, создаётся сама |
| `tasks.py` | генератор заданий с подсказками |
| `ai.py` | GigaChat или YandexGPT и распознавание текста с фото |
| `report.py` | недельный отчёт родителю |
| `stickers.py` | стикеры и анимации Мыслика из папки assets/anim |
| `voice.py` | голос через Yandex SpeechKit, ударения и паузы |

## Переменные окружения

| Имя | Обязательна | Что это |
|---|---|---|
| `TG_BOT_TOKEN` | да | токен бота Telegram |
| `ADMIN_ID` | да | ваш telegram id, для команды `/grant` |
| `MAX_BOT_TOKEN` | для MAX | токен бота MAX от @MasterBot |
| `MAX_ADMIN_ID` | для MAX | ваш user_id в MAX (бот покажет по `/id`) |
| `MAX_CHANNEL_INVITE` | нет | ссылка-приглашение в закрытый канал MAX, уходит после `/grant` |
| `MAX_DB_PATH` | нет | база бота MAX, по умолчанию myslik-max.db |
| `PAY_URL` | да | ссылка на оплату в Tribute или Boosty |
| `TG_CHANNEL_CLOSED` | нет | id закрытого канала, для выдачи приглашений |
| `PAY_WEBHOOK_SECRET` | нет | ключ, который площадка шлёт в заголовке `X-Api-Key` |
| `SUB_DAYS` | нет | на сколько дней открывать подписку, по умолчанию 30 |
| `FREE_LIMIT` | нет | бесплатных заданий в день, по умолчанию 3 |
| `PAID_LIMIT` | нет | заданий по подписке, по умолчанию 30 |
| `DB_PATH` | нет | путь к файлу базы |
| `AI_PROVIDER` | нет | gigachat, yandex или none. Без него работает всё, кроме фото |
| `GIGACHAT_AUTH` | для gigachat | ключ авторизации из личного кабинета |
| `GIGACHAT_SCOPE` | нет | GIGACHAT_API_PERS для физлиц |
| `YANDEX_API_KEY` | для yandex и для фото | ключ сервисного аккаунта |
| `YANDEX_FOLDER` | для yandex и для фото | идентификатор каталога |
| `VOICE_BOY`, `VOICE_GIRL`, `VOICE_PARENT` | нет | имена голосов Яндекса, по умолчанию anton, masha, alexander |
| `VOICE_EMOTION` | нет | оттенок речи, например good, если голос его поддерживает |
| `ANIM_DIR` | нет | папка со стикерами, по умолчанию ../assets/anim |

Распознавание текста с фотографии работает через Yandex Vision, поэтому для фото нужны
`YANDEX_API_KEY` и `YANDEX_FOLDER`, даже если сама модель выбрана GigaChat.

## Установка на сервер

Подойдёт самый простой тариф в Timeweb или Selectel, Ubuntu 24.04, около 500 рублей в месяц.
Сервер должен быть в России: там будут данные детей, это требование 152-ФЗ.

```bash
sudo apt update && sudo apt install -y python3-venv git
git clone https://github.com/Smekairu/Smekai.git
cd Smekai/bot
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # впишите токены
```

Проверка запуска:

```bash
set -a && . ./.env && set +a
python main.py
```

## Автозапуск

Два сервиса systemd, `/etc/systemd/system/myslik.service`:

```ini
[Unit]
Description=Myslik bot
After=network.target

[Service]
WorkingDirectory=/root/Smekai/bot
EnvironmentFile=/root/Smekai/bot/.env
ExecStart=/root/Smekai/bot/.venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Второй такой же для `webhook.py` с именем `myslik-pay.service` и `ExecStart=... webhook.py`,
третий для `max_bot.py` с именем `myslik-max.service`.

```bash
sudo systemctl enable --now myslik myslik-max myslik-pay
sudo journalctl -u myslik -f     # смотреть логи
```

## Оплата

1. В Tribute создайте подписку на 390 рублей в месяц, ссылку на неё положите в `PAY_URL`.
2. В настройках Tribute укажите адрес уведомлений: `https://ваш-домен/pay`.
3. Ключ из настроек положите в `PAY_WEBHOOK_SECRET`.
4. Проведите тестовую оплату и посмотрите логи: в них печатается тело уведомления.
   Если telegram id приходит в другом поле, добавьте его имя в список в `webhook.py`.

Пока домена нет, подписку можно открывать вручную: `/grant 123456789 30`.

## Сертификаты для российских сервисов

GigaChat и Yandex Cloud работают на сертификатах НУЦ Минцифры. На сервере их надо поставить
один раз, иначе соединение оборвётся:

```bash
curl -fsSL -o root.cer https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer
curl -fsSL -o sub.cer  https://gu-st.ru/content/Other/doc/russian_trusted_sub_ca.cer
for f in root sub; do openssl x509 -in $f.cer -out $f.pem 2>/dev/null || openssl x509 -inform DER -in $f.cer -out $f.pem; done
sudo cp root.pem /usr/local/share/ca-certificates/russian_trusted_root_ca.crt
sudo cp sub.pem  /usr/local/share/ca-certificates/russian_trusted_sub_ca.crt
sudo update-ca-certificates
```

## Голос и стикеры

Голосовые сообщения работают через Yandex SpeechKit на тех же ключах, что и распознавание фото.
Без ключей бот отвечает текстом, а выбор голоса просто запоминается на будущее.
Профиль меняется командой `/voice`. Ударения для трудных слов лежат в словаре в `voice.py`.

Стикеры берутся из `assets/anim`: `<персонаж>-<настроение>.webm` для Telegram, в MAX уходят картинки
из `assets/pack/sticker`. После первой отправки
file_id запоминается в базе, и файл больше не грузится. Настроения: wave, yay, party, think, sad,
angry, surprised, sleepy, love, idle.

Откуда пришёл человек, видно по ссылке вида `t.me/smekai_ru_bot?start=chat5a`: метка сохраняется
в поле source и позволяет посчитать, какой чат или канал приводит людей.

## Отчёт родителю

Родитель привязывается к ребёнку сам: ребёнок открывает «Родителю» и получает код из шести
знаков, родитель присылает этот код боту со своего телефона.

Отчёт уходит раз в неделю. Поставьте в cron на сервере:

```
0 19 * * 0 cd /root/Smekai/bot && set -a && . ./.env && set +a && .venv/bin/python report.py
5 19 * * 0 cd /root/Smekai/bot && set -a && . ./.env && set +a && .venv/bin/python report.py --max
```

Посмотреть тексты, ничего не отправляя: `python report.py --dry`.
Родитель может запросить отчёт в любой момент командой `/report`.

## Что дальше

- остальные предметы из общего банка заданий проекта;
- согласие родителя при регистрации и уведомление в Роскомнадзор до приёма первых платежей;
- перенос диалога в мини-приложение Telegram, чтобы был виден прогресс и уровни.
