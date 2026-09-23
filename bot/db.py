"""Хранилище бота. SQLite, ничего настраивать не нужно, файл создаётся сам."""
import json, os, sqlite3
from datetime import date, datetime, timedelta

PATH = os.environ.get("DB_PATH", "myslik.db")
_conn = None


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def init():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY, name TEXT, grade INTEGER,
      created TEXT DEFAULT CURRENT_TIMESTAMP, paid_until TEXT);
    CREATE TABLE IF NOT EXISTS current(
      id INTEGER PRIMARY KEY, q TEXT, a TEXT, hints TEXT, steps TEXT,
      hint_used INTEGER DEFAULT 0, tries INTEGER DEFAULT 0, started TEXT);
    CREATE TABLE IF NOT EXISTS log(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, day TEXT,
      solved INTEGER, hints INTEGER, tries INTEGER, ts TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS payments(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL,
      days INTEGER, source TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    c.commit()


def get_user(uid):
    return conn().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()


def save_user(uid, name, grade):
    c = conn()
    c.execute("INSERT INTO users(id,name,grade) VALUES(?,?,?) "
              "ON CONFLICT(id) DO UPDATE SET name=excluded.name, grade=excluded.grade",
              (uid, name, grade))
    c.commit()


# ---------- подписка ----------

def is_paid(uid):
    u = get_user(uid)
    return bool(u and u["paid_until"] and u["paid_until"] >= date.today().isoformat())


def paid_until(uid):
    u = get_user(uid)
    return u["paid_until"] if u else None


def grant(uid, days, amount=0, source="manual"):
    c = conn()
    c.execute("INSERT OR IGNORE INTO users(id,name,grade) VALUES(?,?,?)", (uid, "", 0))
    u = get_user(uid)
    base = date.today()
    if u and u["paid_until"] and u["paid_until"] > base.isoformat():
        base = date.fromisoformat(u["paid_until"])
    until = (base + timedelta(days=days)).isoformat()
    c.execute("UPDATE users SET paid_until=? WHERE id=?", (until, uid))
    c.execute("INSERT INTO payments(user_id,amount,days,source) VALUES(?,?,?,?)",
              (uid, amount, days, source))
    c.commit()
    return until


# ---------- лимиты и текущее задание ----------

def attempts_today(uid):
    row = conn().execute("SELECT COUNT(*) n FROM log WHERE user_id=? AND day=?",
                         (uid, date.today().isoformat())).fetchone()
    return row["n"]


def attempts_left(uid, free_limit, paid_limit):
    limit = paid_limit if is_paid(uid) else free_limit
    return limit - attempts_today(uid)


def set_current(uid, t):
    c = conn()
    c.execute("INSERT INTO current(id,q,a,hints,steps,hint_used,tries,started) "
              "VALUES(?,?,?,?,?,0,0,?) ON CONFLICT(id) DO UPDATE SET "
              "q=excluded.q,a=excluded.a,hints=excluded.hints,steps=excluded.steps,"
              "hint_used=0,tries=0,started=excluded.started",
              (uid, t["q"], str(t["a"]), json.dumps(t["hints"], ensure_ascii=False),
               t["steps"], datetime.now().isoformat()))
    c.commit()


def get_current(uid):
    r = conn().execute("SELECT * FROM current WHERE id=?", (uid,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["hints"] = json.loads(d["hints"])
    return d


def bump_hint(uid):
    c = conn(); c.execute("UPDATE current SET hint_used=hint_used+1 WHERE id=?", (uid,)); c.commit()


def bump_try(uid):
    c = conn(); c.execute("UPDATE current SET tries=tries+1 WHERE id=?", (uid,)); c.commit()


def close_current(uid, solved):
    cur = get_current(uid)
    if not cur:
        return
    c = conn()
    c.execute("INSERT INTO log(user_id,day,solved,hints,tries) VALUES(?,?,?,?,?)",
              (uid, date.today().isoformat(), 1 if solved else 0, cur["hint_used"], cur["tries"]))
    c.execute("DELETE FROM current WHERE id=?", (uid,))
    c.commit()


def stats(uid):
    c = conn()
    today = c.execute("SELECT COUNT(*) n FROM log WHERE user_id=? AND day=? AND solved=1",
                      (uid, date.today().isoformat())).fetchone()["n"]
    total = c.execute("SELECT COUNT(*) n FROM log WHERE user_id=? AND solved=1", (uid,)).fetchone()["n"]
    clean = c.execute("SELECT COUNT(*) n FROM log WHERE user_id=? AND solved=1 AND hints=0",
                      (uid,)).fetchone()["n"]
    days = [r["day"] for r in c.execute(
        "SELECT DISTINCT day FROM log WHERE user_id=? ORDER BY day DESC", (uid,)).fetchall()]
    streak, d = 0, date.today()
    while d.isoformat() in days:
        streak += 1
        d -= timedelta(days=1)
    return {"today": today, "total": total, "clean": clean, "streak": streak}


def week_report(uid):
    """Данные для недельного отчёта родителю."""
    since = (date.today() - timedelta(days=7)).isoformat()
    c = conn()
    r = c.execute("SELECT COUNT(*) n, SUM(solved) s, SUM(hints) h FROM log "
                  "WHERE user_id=? AND day>=?", (uid, since)).fetchone()
    return {"tasks": r["n"] or 0, "solved": r["s"] or 0, "hints": r["h"] or 0}
