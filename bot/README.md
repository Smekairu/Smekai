# Мыслик: бот с подпиской и разбором заданий

Первый этап. Что умеет:

- задания по математике 1-6 класса, ответ проверяется вычислением, а не нейросетью;
- три подсказки вместо готового ответа, разбор по шагам только после попыток;
- бесплатно 3 задания в день, по подписке 30;
- оплата через Tribute или другую площадку, доступ открывается автоматически;
- одноразовая ссылка в закрытый канал после оплаты;
- прогресс ребёнка и данные для недельного отчёта родителю.

## Файлы

| Файл | Зачем |
|---|---|
| `main.py` | сам бот |
| `webhook.py` | приём уведомлений об оплате |
| `db.py` | база SQLite, создаётся сама |
| `tasks.py` | генератор заданий с подсказками |

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

## Что дальше

- разбор домашки по фото: распознавание через Yandex Vision, подсказки через GigaChat;
- недельный отчёт родителю, данные уже собираются в `db.week_report`;
- остальные предметы из общего банка заданий проекта;
- согласие родителя при регистрации и уведомление в Роскомнадзор до приёма первых платежей.
