# Смекай

Сайт с викториной и автопубликация постов в Telegram и MAX.

## Что где лежит
- `index.html`: викторина. Адрес после включения Pages: https://smekairu.github.io/Smekai/
- `assets/`: логотипы и аватары Мыслика.
- `posts/`: посты. Один файл = один пост.
- `state/published.json`: список уже отправленных постов, ведётся автоматически.
- `scripts/publish.py` и `.github/workflows/publish.yml`: автопубликация, запускается каждые 10 минут.

## Как добавить пост
1. Откройте папку `posts` → Add file → Create new file.
2. Имя файла: `2026-09-30-1900-tema.md` (дата, время, тема латиницей).
3. Вверху блок настроек:

```
---
time: 2026-09-30 19:00
channels: telegram, max
button: Пройти викторину
link: quiz
image: assets/myslik-navy.png
---
Текст поста. <b>Жирный</b>, <i>курсив</i>, <tg-spoiler>спойлер</tg-spoiler>.
```

`button`, `link`, `image` необязательны. `link`: quiz, boosty или полный адрес. Время московское.

4. Commit changes. Пост уйдёт в канал в указанное время (с задержкой до 10–20 минут).

Отправить сразу: вкладка Actions → «Публикация постов» → Run workflow.
