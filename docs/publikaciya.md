# Надёжная публикация постов

Публикатор (`.github/workflows/publish.yml`) запускается по расписанию GitHub. GitHub запускает такие задания
когда получится: в сентябре 2026 года из 39 запусков в день проходило 2–4, посты выходили с опозданием
на несколько часов. Чтобы посты выходили вовремя, публикатор нужно будить снаружи. Бесплатно это делает
сервис cron-job.org. Настройка один раз, минут десять.

## 1. Токен GitHub для запуска

1. github.com → аватар → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token.
2. Name: `smekai-cron`. Expiration: 1 год. Resource owner: Smekairu. Repository access: Only select repositories → Smekai.
3. Permissions → Repository permissions → Actions: **Read and write**. Остальное не трогать.
4. Generate token, скопировать (показывается один раз).

## 2. Задание на cron-job.org

1. Зарегистрироваться на https://cron-job.org (бесплатно).
2. Create cronjob:
   - Title: `Смекай публикация`
   - URL: `https://api.github.com/repos/Smekairu/Smekai/actions/workflows/publish.yml/dispatches`
   - Schedule: часовой пояс Europe/Moscow, каждый день в 09:01 и 18:31 (утренние и вечерние посты).
     Для страховки заведите копию этого задания на 09:20 и 18:50.
3. Вкладка Advanced:
   - Request method: POST
   - Headers:
     - `Authorization: Bearer <токен из шага 1>`
     - `Accept: application/vnd.github+json`
     - `X-GitHub-Api-Version: 2022-11-28`
   - Request body: `{"ref":"main"}`
4. Save, затем Test run. Ответ 204 значит, что всё работает: в GitHub во вкладке Actions появится запуск
   «Публикация постов» с пометкой workflow_dispatch.

Повторный запуск ничего не сломает: публикатор отправляет только то, что ещё не отправлено, и помечает
отправленное в `state/published.json`.

## Если будет свой сервер

Тогда проще публиковать с сервера: `publish-cron.sh` из корня репозитория в crontab каждые 10 минут
(см. docs/server.md). Задания на cron-job.org после этого можно выключить.
