"""Хранилище Смекай. Одна база SQLite на всех: бот Telegram, бот MAX и сервер сайта.

Файл создаётся сам. Кто есть кто, видно по номеру (см. ids.py):
  Telegram  положительный id пользователя Telegram
  MAX       отрицательный: минус id пользователя MAX
  сайт      от 9 000 000 000 000 000, аккаунт без мессенджера
"""
import json, os, secrets, sqlite3, string
from datetime import date, datetime, timedelta

import ids

PATH = os.environ.get("DB_PATH", "myslik.db")
_conn = None
CODE_ABC = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(PATH, check_same_thread=False, timeout=10)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA busy_timeout=8000")
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
    CREATE TABLE IF NOT EXISTS parents(
      parent_id INTEGER, child_id INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(parent_id, child_id));
    CREATE TABLE IF NOT EXISTS codes(
      code TEXT PRIMARY KEY, child_id INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS photo(
      id INTEGER PRIMARY KEY, user_id INTEGER, task TEXT, step INTEGER DEFAULT 0,
      history TEXT DEFAULT '[]', started TEXT);
    CREATE TABLE IF NOT EXISTS files(key TEXT PRIMARY KEY, file_id TEXT);
    CREATE TABLE IF NOT EXISTS payments(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL,
      days INTEGER, source TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS sessions(
      token TEXT PRIMARY KEY, uid INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS logins(
      token TEXT PRIMARY KEY, uid INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS outbox(
      id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, text TEXT, buttons TEXT,
      created TEXT DEFAULT CURRENT_TIMESTAMP, sent INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS orders(
      id TEXT PRIMARY KEY, uid INTEGER, plan TEXT, amount REAL, status TEXT,
      created TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS tickets(
      id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, kind TEXT, text TEXT, contact TEXT,
      created TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'new');
    CREATE TABLE IF NOT EXISTS dialog(uid INTEGER PRIMARY KEY, state TEXT, data TEXT);
    """)
    c.commit()
    cols = [r["name"] for r in c.execute("PRAGMA table_info(users)").fetchall()]
    for col, ddl in (("voice", "TEXT DEFAULT 'boy'"), ("streak", "INTEGER DEFAULT 0"),
                     ("source", "TEXT"), ("plan", "TEXT"), ("recovery", "TEXT")):
        if col not in cols:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
    c.commit()


def _one(sql, args=()):
    return conn().execute(sql, args).fetchone()


def _run(sql, args=()):
    c = conn(); cur = c.execute(sql, args); c.commit(); return cur


# ---------- кеш file_id ----------

def file_id_get(key):
    r = _one("SELECT file_id FROM files WHERE key=?", (key,))
    return r["file_id"] if r else None


def file_id_set(key, fid):
    _run("INSERT OR REPLACE INTO files(key,file_id) VALUES(?,?)", (key, fid))


def file_id_del(key):
    _run("DELETE FROM files WHERE key=?", (key,))


# ---------- пользователи ----------

def set_source(uid, source):
    _run("INSERT OR IGNORE INTO users(id,name,grade) VALUES(?,?,?)", (uid, "", 0))
    _run("UPDATE users SET source=COALESCE(source,?) WHERE id=?", (source[:40], uid))


def set_voice(uid, profile):
    _run("UPDATE users SET voice=? WHERE id=?", (profile, uid))


def bump_streak(uid, ok):
    if ok:
        _run("UPDATE users SET streak=COALESCE(streak,0)+1 WHERE id=?", (uid,))
    else:
        _run("UPDATE users SET streak=0 WHERE id=?", (uid,))
    r = _one("SELECT streak FROM users WHERE id=?", (uid,))
    return r["streak"] if r else 0


def get_user(uid):
    return _one("SELECT * FROM users WHERE id=?", (uid,))


def save_user(uid, name, grade):
    _run("INSERT INTO users(id,name,grade) VALUES(?,?,?) "
         "ON CONFLICT(id) DO UPDATE SET name=excluded.name, grade=excluded.grade", (uid, name, grade))


def update_profile(uid, name=None, grade=None, voice=None):
    if name is not None:
        _run("UPDATE users SET name=? WHERE id=?", (str(name)[:30], uid))
    if grade is not None:
        _run("UPDATE users SET grade=? WHERE id=?", (int(grade), uid))
    if voice is not None:
        _run("UPDATE users SET voice=? WHERE id=?", (str(voice)[:10], uid))


def new_web_user(name, grade):
    """Аккаунт на сайте без мессенджера. Возвращает (id, код восстановления)."""
    r = _one("SELECT MAX(id) m FROM users WHERE id>=?", (ids.WEB_BASE,))
    uid = max(ids.WEB_BASE, (r["m"] or ids.WEB_BASE)) + 1
    rec = "-".join("".join(secrets.choice(CODE_ABC) for _ in range(4)) for _ in range(3))
    _run("INSERT INTO users(id,name,grade,source,recovery,voice) VALUES(?,?,?,?,?,?)",
         (uid, str(name)[:30], int(grade), "web", rec, "off"))
    return uid, rec


def by_recovery(code):
    code = (code or "").strip().upper().replace(" ", "")
    r = _one("SELECT id FROM users WHERE recovery=?", (code,))
    return r["id"] if r else None


# ---------- подписка ----------

HELPER_PLANS = ("myslik", "family")


def is_paid(uid):
    """Любой оплаченный тариф: доступ в закрытый канал."""
    u = get_user(uid)
    return bool(u and u["paid_until"] and u["paid_until"] >= date.today().isoformat())


def has_helper(uid):
    """Тариф с личным помощником: больше заданий в день и разбор по фото."""
    u = get_user(uid)
    return bool(is_paid(uid) and (u["plan"] or "myslik") in HELPER_PLANS)


def plan_of(uid):
    u = get_user(uid)
    return (u["plan"] or "myslik") if is_paid(uid) else "free"


def paid_until(uid):
    u = get_user(uid)
    return u["paid_until"] if u else None


def grant(uid, days, amount=0, source="manual", plan="myslik"):
    _run("INSERT OR IGNORE INTO users(id,name,grade) VALUES(?,?,?)", (uid, "", 0))
    u = get_user(uid)
    base = date.today()
    if u and u["paid_until"] and u["paid_until"] > base.isoformat():
        base = date.fromisoformat(u["paid_until"])
    until = (base + timedelta(days=days)).isoformat()
    _run("UPDATE users SET paid_until=?, plan=? WHERE id=?", (until, plan, uid))
    _run("INSERT INTO payments(user_id,amount,days,source) VALUES(?,?,?,?)", (uid, amount, days, source))
    return until


def grant_plan(uid, plan, days=30, amount=0, source="manual"):
    """Открывает тариф. Для «Семьи» доступ получают и привязанные дети, до двух."""
    until = grant(uid, days, amount, source, plan)
    extra = []
    if plan == "family":
        for kid in children_of(uid)[:2]:
            grant(kid, days, 0, source + ":family", plan)
            extra.append(kid)
    return until, extra


# ---------- лимиты и текущее задание ----------

def attempts_today(uid):
    return _one("SELECT COUNT(*) n FROM log WHERE user_id=? AND day=?", (uid, date.today().isoformat()))["n"]


def attempts_left(uid, free_limit, paid_limit):
    limit = paid_limit if has_helper(uid) else free_limit
    return limit - attempts_today(uid)


def set_current(uid, t):
    _run("INSERT INTO current(id,q,a,hints,steps,hint_used,tries,started) "
         "VALUES(?,?,?,?,?,0,0,?) ON CONFLICT(id) DO UPDATE SET "
         "q=excluded.q,a=excluded.a,hints=excluded.hints,steps=excluded.steps,"
         "hint_used=0,tries=0,started=excluded.started",
         (uid, t["q"], str(t["a"]), json.dumps(t["hints"], ensure_ascii=False), t["steps"], datetime.now().isoformat()))


def get_current(uid):
    r = _one("SELECT * FROM current WHERE id=?", (uid,))
    if not r:
        return None
    d = dict(r)
    d["hints"] = json.loads(d["hints"])
    return d


def bump_hint(uid):
    _run("UPDATE current SET hint_used=hint_used+1 WHERE id=?", (uid,))


def bump_try(uid):
    _run("UPDATE current SET tries=tries+1 WHERE id=?", (uid,))


def close_current(uid, solved):
    cur = get_current(uid)
    if not cur:
        return
    log_attempt(uid, solved, cur["hint_used"], cur["tries"])
    _run("DELETE FROM current WHERE id=?", (uid,))


def log_attempt(uid, solved, hints=0, tries=0):
    """Одна попытка: из бота или из занятия на сайте."""
    _run("INSERT INTO log(user_id,day,solved,hints,tries) VALUES(?,?,?,?,?)",
         (uid, date.today().isoformat(), 1 if solved else 0, int(hints), int(tries)))


def stats(uid):
    today = _one("SELECT COUNT(*) n FROM log WHERE user_id=? AND day=? AND solved=1",
                 (uid, date.today().isoformat()))["n"]
    total = _one("SELECT COUNT(*) n FROM log WHERE user_id=? AND solved=1", (uid,))["n"]
    clean = _one("SELECT COUNT(*) n FROM log WHERE user_id=? AND solved=1 AND hints=0", (uid,))["n"]
    days = {r["day"] for r in conn().execute("SELECT DISTINCT day FROM log WHERE user_id=?", (uid,)).fetchall()}
    streak, d = 0, date.today()
    if d.isoformat() not in days:
        d -= timedelta(days=1)          # серия не рвётся, пока сегодня ещё не занимались
    while d.isoformat() in days:
        streak += 1
        d -= timedelta(days=1)
    return {"today": today, "total": total, "clean": clean, "streak": streak}


def week_days(uid):
    """Семь последних дней: решено и всего попыток по дням, для графика в кабинете."""
    out = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        r = _one("SELECT COUNT(*) n, COALESCE(SUM(solved),0) s FROM log WHERE user_id=? AND day=?", (uid, d))
        out.append({"day": d, "tasks": r["n"], "solved": r["s"]})
    return out


def week_report(uid):
    """Данные для недельного отчёта родителю."""
    since = (date.today() - timedelta(days=7)).isoformat()
    r = _one("SELECT COUNT(*) n, SUM(solved) s, SUM(hints) h FROM log WHERE user_id=? AND day>=?", (uid, since))
    d = _one("SELECT COUNT(DISTINCT day) d FROM log WHERE user_id=? AND day>=?", (uid, since))["d"]
    wh = _one("SELECT COUNT(*) n FROM log WHERE user_id=? AND day>=? AND solved=1 AND hints>0", (uid, since))["n"]
    return {"tasks": r["n"] or 0, "solved": r["s"] or 0, "hints": r["h"] or 0, "days": d or 0, "with_hints": wh or 0}


# ---------- связь родителя и ребёнка ----------

def make_code(child_id):
    """Короткий код, который ребёнок показывает родителю."""
    code = "".join(secrets.choice(CODE_ABC) for _ in range(6))
    _run("DELETE FROM codes WHERE child_id=?", (child_id,))
    _run("INSERT INTO codes(code, child_id) VALUES(?,?)", (code, child_id))
    return code


def use_code(code, parent_id):
    """Привязывает родителя к ребёнку. Возвращает id ребёнка или None."""
    code = (code or "").strip().upper()
    r = _one("SELECT child_id FROM codes WHERE code=?", (code,))
    if not r or r["child_id"] == parent_id:
        return None
    _run("INSERT OR IGNORE INTO parents(parent_id, child_id) VALUES(?,?)", (parent_id, r["child_id"]))
    _run("DELETE FROM codes WHERE code=?", (code,))
    return r["child_id"]


def parent_links():
    return [(r["parent_id"], r["child_id"]) for r in conn().execute("SELECT parent_id, child_id FROM parents").fetchall()]


def children_of(parent_id):
    return [r["child_id"] for r in conn().execute("SELECT child_id FROM parents WHERE parent_id=?", (parent_id,)).fetchall()]


def parents_of(child_id):
    return [r["parent_id"] for r in conn().execute("SELECT parent_id FROM parents WHERE child_id=?", (child_id,)).fetchall()]


# ---------- разбор задания с фотографии ----------

def photo_start(uid, task):
    _run("INSERT INTO photo(id,user_id,task,step,history,started) VALUES(?,?,?,0,'[]',?) "
         "ON CONFLICT(id) DO UPDATE SET task=excluded.task, step=0, history='[]', started=excluded.started",
         (uid, uid, task, datetime.now().isoformat()))


def photo_get(uid):
    r = _one("SELECT * FROM photo WHERE id=?", (uid,))
    if not r:
        return None
    d = dict(r)
    d["history"] = json.loads(d["history"])
    return d


def photo_step(uid, history):
    _run("UPDATE photo SET step=step+1, history=? WHERE id=?", (json.dumps(history, ensure_ascii=False), uid))


def photo_close(uid):
    _run("DELETE FROM photo WHERE id=?", (uid,))


# ---------- вход в личный кабинет ----------

def login_token(uid):
    """Одноразовая ссылка из бота в кабинет, живёт 30 минут."""
    tok = secrets.token_urlsafe(18)
    _run("DELETE FROM logins WHERE created < datetime('now','-1 day')")
    _run("INSERT INTO logins(token, uid) VALUES(?,?)", (tok, uid))
    return tok


def use_login(token):
    r = _one("SELECT uid FROM logins WHERE token=? AND created >= datetime('now','-30 minutes')", (token,))
    _run("DELETE FROM logins WHERE token=?", (token,))
    return r["uid"] if r else None


def new_session(uid):
    tok = secrets.token_urlsafe(24)
    _run("INSERT INTO sessions(token, uid) VALUES(?,?)", (tok, uid))
    return tok


def session_uid(token):
    if not token:
        return None
    r = _one("SELECT uid FROM sessions WHERE token=? AND created >= datetime('now','-180 days')", (token,))
    return r["uid"] if r else None


def end_session(token):
    _run("DELETE FROM sessions WHERE token=?", (token,))


# ---------- исходящие сообщения ----------
# Любой процесс кладёт сообщение сюда, а доставляет бот той платформы, где живёт получатель.

def outbox_put(uid, text, buttons=None):
    _run("INSERT INTO outbox(uid, text, buttons) VALUES(?,?,?)",
         (uid, text, json.dumps(buttons, ensure_ascii=False) if buttons else None))


def outbox_take(platform, limit=20):
    rows = conn().execute("SELECT * FROM outbox WHERE sent=0 ORDER BY id LIMIT 200").fetchall()
    out = [dict(r) for r in rows if ids.platform(r["uid"]) == platform][:limit]
    for r in out:
        r["buttons"] = json.loads(r["buttons"]) if r["buttons"] else None
    return out


def outbox_done(msg_id, ok=True):
    _run("UPDATE outbox SET sent=? WHERE id=?", (1 if ok else 2, msg_id))


# ---------- заказы и обращения ----------

def order_put(oid, uid, plan, amount, status):
    _run("INSERT OR REPLACE INTO orders(id, uid, plan, amount, status) VALUES(?,?,?,?,?)", (oid, uid, plan, amount, status))


def order_get(oid):
    r = _one("SELECT * FROM orders WHERE id=?", (oid,))
    return dict(r) if r else None


def order_status(oid, status):
    _run("UPDATE orders SET status=? WHERE id=?", (status, oid))


def ticket_new(uid, kind, text, contact=""):
    cur = _run("INSERT INTO tickets(uid, kind, text, contact) VALUES(?,?,?,?)", (uid, kind, str(text)[:3000], str(contact)[:200]))
    return cur.lastrowid


def ticket_get(tid):
    r = _one("SELECT * FROM tickets WHERE id=?", (tid,))
    return dict(r) if r else None


def ticket_close(tid):
    _run("UPDATE tickets SET status='done' WHERE id=?", (tid,))


# ---------- состояние диалога (поддержка, возврат) ----------

def dialog_set(uid, state, data=None):
    _run("INSERT OR REPLACE INTO dialog(uid, state, data) VALUES(?,?,?)",
         (uid, state, json.dumps(data or {}, ensure_ascii=False)))


def dialog_get(uid):
    r = _one("SELECT state, data FROM dialog WHERE uid=?", (uid,))
    return (r["state"], json.loads(r["data"] or "{}")) if r else (None, {})


def dialog_clear(uid):
    _run("DELETE FROM dialog WHERE uid=?", (uid,))
