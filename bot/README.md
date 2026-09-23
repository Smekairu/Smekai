# Мыслик: бот с подпиской и разбором заданий

Что умеет:

- задания по математике 1-6 класса, ответ проверяется вычислением, а не нейросетью;
- три подсказки вместо готового ответа, разбор по шагам только после попыток;
- разбор домашки по фотографии: распознаёт текст и ведёт к ответу вопросами;
- недельный отчёт родителю, привязка родителя к ребёнку по коду;
- бесплатно 3 задания в день, по подписке 30, фото только по подписке;
- оплата через Tribute или другую площадку, доступ открывается автоматически;
- одноразовая ссылка в закрытый канал после оплаты.

## Файлы

| Файл | Зачем |
|---|---|
| `main.py` | сам бот |
| `webhook.py` | приём уведомлений об оплате |
| `db.py` | база SQLite, создаётся сама |
| `tasks.py` | генератор заданий с подсказками |
| `ai.py` | GigaChat или YandexGPT и распознавание текста с фото |
| `report.py` | недельный отчёт родителю |

## Переменные окружения

| Имя | Обязательна | Что это |
|---|---|---|
| `TG_BOT_TOKEN` | да | токен бота |
| `ADMIN_ID` | да | ваш telegram id, для команды `/grant` |
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

Второй такой же для `webhook.py` с именем `myslik-pay.service` и `ExecStart=... webhook.py`.

```bash
sudo systemctl enable --now myslik myslik-pay
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

## Отчёт родителю

Родитель привязывается к ребёнку сам: ребёнок открывает «Родителю» и получает код из шести
знаков, родитель присылает этот код боту со своего телефона.

Отчёт уходит раз в неделю. Поставьте в cron на сервере:

```
0 19 * * 0 cd /root/Smekai/bot && set -a && . ./.env && set +a && .venv/bin/python report.py
```

Посмотреть тексты, ничего не отправляя: `python report.py --dry`.
Родитель может запросить отчёт в любой момент командой `/report`.

## Что дальше

- остальные предметы из общего банка заданий проекта;
- согласие родителя при регистрации и уведомление в Роскомнадзор до приёма первых платежей;
- перенос диалога в мини-приложение Telegram, чтобы был виден прогресс и уровни.
