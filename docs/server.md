# Сервер Смекай: что на нём крутится

Один сервер в России, Ubuntu 24.04, самый простой тариф. На нём живут три вещи:
бот Мыслик, приём оплаты и публикация постов. GitHub остаётся хранилищем кода
и запасным публикатором.

## 1. Подготовка

```bash
sudo apt update && sudo apt install -y python3-venv git curl
git clone https://github.com/Smekairu/Smekai.git
cd Smekai/bot
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env      # вписать токены
```

Сертификаты Минцифры, без них не работают MAX, GigaChat и Yandex Cloud:

```bash
curl -fsSL -o root.cer https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer
curl -fsSL -o sub.cer  https://gu-st.ru/content/Other/doc/russian_trusted_sub_ca.cer
for f in root sub; do openssl x509 -in $f.cer -out $f.pem 2>/dev/null || openssl x509 -inform DER -in $f.cer -out $f.pem; done
sudo cp root.pem /usr/local/share/ca-certificates/russian_trusted_root_ca.crt
sudo cp sub.pem  /usr/local/share/ca-certificates/russian_trusted_sub_ca.crt
sudo update-ca-certificates
```

## 2. Бот и приём оплаты

Два сервиса systemd, файлы `/etc/systemd/system/myslik.service` и `myslik-pay.service`:

```ini
[Unit]
Description=Myslik bot
After=network.target

[Service]
WorkingDirectory=/root/Smekai/bot
EnvironmentFile=/root/Smekai/bot/.env
ExecStart=/root/Smekai/bot/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Во втором файле меняется только `Description` и `ExecStart=... webhook.py`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now myslik myslik-pay
sudo journalctl -u myslik -f
```

## 3. Публикация постов с сервера

GitHub запускает расписание с задержками в часы, а иногда пропускает совсем.
На сервере это решается одной строкой в cron: каждые десять минут проверять очередь.
Задание уходит минута в минуту, GitHub остаётся запасным вариантом.

Переменные для публикатора кладём в тот же `.env`:

```
TG_CHANNEL=@smekai_ru
TG_CHANNEL_CLOSED=-1004434463581
MAX_BOT_TOKEN=...
MAX_CHAT_ID=-79299919362772
MAX_CHAT_ID_CLOSED=
```

Скрипт `publish-cron.sh` в корне репозитория делает всё сам: подтягивает свежие посты
из GitHub, собирает задания на три дня вперёд, отправляет то, чему пришло время, и
возвращает отметки об отправке обратно в GitHub, чтобы оба публикатора не дублировали друг друга.

```bash
chmod +x /root/Smekai/publish-cron.sh
crontab -e
```

Строки в crontab:

```
*/10 6-18 * * *  /root/Smekai/publish-cron.sh >> /root/publish.log 2>&1
0 19 * * 0       cd /root/Smekai/bot && set -a && . ./.env && set +a && .venv/bin/python report.py >> /root/report.log 2>&1
```

Первая строка это публикация каждые десять минут с 9 до 21 по Москве, если на сервере
московское время. Проверить: `timedatectl`, поставить: `sudo timedatectl set-timezone Europe/Moscow`.
Вторая строка это отчёт родителям по воскресеньям в 19:00.

Чтобы сервер мог возвращать отметки в GitHub, ему нужен токен с правом Contents: Read and write.
Кладётся в файл `/root/.git-credentials` командой:

```bash
git config --global credential.helper store
cd /root/Smekai && git pull      # спросит логин и токен один раз
```

После этого расписание в GitHub можно оставить как есть или отключить в `.github/workflows/publish.yml`,
убрав блок `schedule`. Ручной запуск кнопкой при этом сохраняется.

## 4. Проверка после установки

```bash
systemctl status myslik myslik-pay --no-pager
tail -20 /root/publish.log
curl -s http://127.0.0.1:8080/health
```

В боте: `/start`, взять задание, ответить, получить стикер. Затем `/grant свой_id 30`
и проверить, что пришла ссылка в закрытый канал.
