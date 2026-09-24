# Сервер Смекай: что на нём крутится

Один сервер в России, Ubuntu 24.04, самый простой тариф. На нём живут четыре вещи:
бот Мыслик в Telegram, бот Мыслик в MAX, приём оплаты и публикация постов. GitHub остаётся хранилищем кода
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

## 2. Боты и приём оплаты

Три сервиса systemd: `/etc/systemd/system/myslik.service` (Telegram), `myslik-max.service` (MAX)
и `myslik-pay.service` (оплата):

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

В остальных файлах меняются только `Description` и `ExecStart`: `... max_bot.py` и `... webhook.py`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now myslik myslik-max myslik-pay
sudo journalctl -u myslik -f
sudo journalctl -u myslik-max -f
```

Настройка ботов (имя, описание, команды, аватар) делается из GitHub: Actions → «Настроить ботов».
Подробности и что делается руками: `docs/boty.md`.

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
5 19 * * 0       cd /root/Smekai/bot && set -a && . ./.env && set +a && .venv/bin/python report.py --max >> /root/report.log 2>&1
```

Первая строка это публикация каждые десять минут с 9 до 21 по Москве, если на сервере
московское время. Проверить: `timedatectl`, поставить: `sudo timedatectl set-timezone Europe/Moscow`.
Вторая и третья строки это отчёт родителям по воскресеньям в 19:00, в Telegram и в MAX.

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
systemctl status myslik myslik-max myslik-pay --no-pager
tail -20 /root/publish.log
curl -s http://127.0.0.1:8080/health
```

В боте: `/start`, взять задание, ответить, получить стикер. Затем `/grant свой_id 30`
и проверить, что пришла ссылка в закрытый канал.

## 5. Личный кабинет и оплата на сайте

Сайт лежит на GitHub Pages, а данные кабинета и оплата живут на этом сервере. Сайту нужен адрес
сервера с HTTPS, поэтому понадобится домен или поддомен, например `api.smekai.ru`, направленный на IP сервера.

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo tee /etc/nginx/sites-available/smekai-api >/dev/null <<'NGINX'
server {
    server_name api.smekai.ru;
    location / { proxy_pass http://127.0.0.1:8080; proxy_set_header Host $host; proxy_set_header X-Forwarded-For $remote_addr; }
}
NGINX
sudo ln -s /etc/nginx/sites-available/smekai-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d api.smekai.ru      # бесплатный сертификат, продлевается сам
```

Дальше три правки:

1. В `bot/.env`: `API_PUBLIC=https://api.smekai.ru` и `SITE_ORIGINS=https://smekairu.github.io`.
2. В `assets/site.js` в самом верху: `API: 'https://api.smekai.ru'`. Закоммитить и отправить в GitHub.
3. `sudo systemctl restart myslik myslik-max myslik-pay`, затем в GitHub запустить «Настроить ботов»:
   в Telegram появится кнопка «Кабинет», которая открывает кабинет прямо внутри Telegram.

Проверка: `curl https://api.smekai.ru/health` отвечает `{"ok": true, ...}`. На сайте в кабинете
появляется вход через Telegram, MAX или без мессенджера.

Как это устроено: все три процесса работают с одной базой `bot/myslik.db`. Люди из Telegram хранятся
под своим id, из MAX со знаком минус, аккаунты сайта от 9 000 000 000 000 000. Сообщения пользователям
(оплата прошла, ответ поддержки, отчёт родителю) кладутся в общую очередь, и их доставляет бот той платформы,
где живёт человек. Поэтому код родителя работает между платформами.

Оплата через ЮKassa описана в `docs/oplata.md`. Адрес для уведомлений ЮKassa: `https://api.smekai.ru/pay/yookassa`.

## 6. Поддержка

Мыслик отвечает на частые вопросы сам: тексты в `assets/support.json`, их читают и сайт, и боты.
Заявки на возврат и вопросы «написать человеку» приходят администратору в Telegram и MAX с номером.
Ответить: `/reply номер текст`, ответ уйдёт человеку в его мессенджер.
