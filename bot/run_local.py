"""Запускает обоих ботов на обычном компьютере, пока нет сервера.

  python run_local.py

Читает .env из этой папки, запускает main.py (Telegram) и max_bot.py (MAX),
для которых есть токены, и перезапускает упавший процесс. Остановить: Ctrl+C.
Боты работают, пока включён компьютер и есть интернет. Для круглосуточной работы нужен сервер.
"""
import os, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_env():
    p = HERE / ".env"
    if not p.exists():
        print("Нет файла .env. Скопируйте .env.example в .env и впишите токены."); sys.exit(1)
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    load_env()
    procs = {}
    plan = [("Telegram", "main.py", "TG_BOT_TOKEN"), ("MAX", "max_bot.py", "MAX_BOT_TOKEN")]
    plan = [(n, f, k) for n, f, k in plan if os.environ.get(k)]
    if not plan:
        print("В .env нет ни TG_BOT_TOKEN, ни MAX_BOT_TOKEN."); sys.exit(1)
    print("Запускаю:", ", ".join(n for n, _, _ in plan), "(остановить: Ctrl+C)")
    try:
        while True:
            for name, file, _ in plan:
                p = procs.get(name)
                if p is None or p.poll() is not None:
                    if p is not None:
                        print(f"{name}: процесс завершился с кодом {p.returncode}, перезапуск через 5 с")
                        time.sleep(5)
                    procs[name] = subprocess.Popen([sys.executable, str(HERE / file)], cwd=str(HERE))
            time.sleep(2)
    except KeyboardInterrupt:
        for p in procs.values():
            p.terminate()
        print("Остановлено.")


if __name__ == "__main__":
    main()
