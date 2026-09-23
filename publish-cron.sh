#!/bin/bash
# Публикация постов с сервера. Запускается из cron каждые десять минут.
# Берёт свежие посты из GitHub, отправляет то, чему пришло время, возвращает отметки.
set -e
cd "$(dirname "$0")"
set -a; . ./bot/.env; set +a

git pull -q --rebase origin main || true
python3 scripts/build_posts.py --days 3 >/dev/null || true
python3 scripts/publish.py || true

if ! git diff --quiet -- state posts; then
  git add state posts
  git -c user.name="smekai-server" -c user.email="smekai-server@users.noreply.github.com" \
      commit -qm "Отметки об отправке с сервера" || true
  git push -q origin HEAD:main || echo "не удалось отправить отметки в GitHub"
fi
