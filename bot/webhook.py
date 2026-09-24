"""Сервер сайта: личный кабинет, оплата, поддержка, уведомления об оплате.

Запуск рядом с ботами: python webhook.py (порт PORT, по умолчанию 8080).
Снаружи сервер открывается через nginx с HTTPS, см. docs/server.md.

Адреса:
  /api/...          личный кабинет и поддержка для сайта (kabinet/, oplata.html)
  /pay/yookassa     уведомления ЮKassa об оплате на сайте
  /pay              уведомления Tribute (оплата в Telegram)
  /health           проверка, что сервер жив

Сообщения пользователям сервер не шлёт сам: кладёт их в общую очередь (outbox),
а доставляет бот той платформы, где живёт человек.
"""
import hashlib, hmac, json, logging, os, time, urllib.parse

from aiohttp import web

import db, ids, support
import pay_yookassa as yk
from common import PLANS, SITE_URL, CABINET_URL, BOOSTY_URL, SUB_DAYS, FREE_LIMIT, PAID_LIMIT, daily_limit, plan_line

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("server")

SECRET = os.environ.get("PAY_WEBHOOK_SECRET", "")
TG_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
CLOSED_CHANNEL = os.environ.get("TG_CHANNEL_CLOSED", "")
MAX_INVITE = os.environ.get("MAX_CHANNEL_INVITE", "")
TRIBUTE_PLAN = os.environ.get("TRIBUTE_PLAN", "myslik")
ORIGINS = {o.strip().rstrip("/") for o in os.environ.get(
    "SITE_ORIGINS", "https://smekairu.github.io,http://localhost:8765").split(",") if o.strip()}


# ---------------- общее ----------------

@web.middleware
async def cors(request, handler):
    if request.method == "OPTIONS":
        resp = web.Response(status=204)
    else:
        try:
            resp = await handler(request)
        except web.HTTPException as e:
            resp = web.json_response({"ok": False, "error": e.reason}, status=e.status)
    origin = request.headers.get("Origin", "").rstrip("/")
    if origin in ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Vary"] = "Origin"
    return resp


def ok(**kw):
    return web.json_response({"ok": True, **kw})


def fail(msg, status=400):
    return web.json_response({"ok": False, "error": msg}, status=status)


async def body(request):
    try:
        return await request.json()
    except Exception:
        return {}


def auth(request):
    h = request.headers.get("Authorization", "")
    uid = db.session_uid(h[7:].strip() if h.startswith("Bearer ") else "")
    if not uid:
        raise web.HTTPUnauthorized(reason="Нужно войти")
    return uid


# ---------------- вход ----------------

def check_telegram(init_data):
    """Проверка данных мини-приложения Telegram по подписи бота. Возвращает id или None."""
    if not TG_TOKEN or not init_data:
        return None
    pairs = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    got = pairs.pop("hash", "")
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", TG_TOKEN.encode(), hashlib.sha256).digest()
    want = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(want, got):
        return None
    if time.time() - int(pairs.get("auth_date", "0")) > 86400:
        return None
    try:
        return int(json.loads(pairs.get("user", "{}"))["id"])
    except Exception:
        return None


async def auth_telegram(request):
    d = await body(request)
    uid = check_telegram(d.get("init_data", ""))
    if not uid:
        return fail("Не удалось проверить вход из Telegram", 403)
    if not db.get_user(uid):
        db.save_user(uid, "", 0)
    return ok(session=db.new_session(uid))


async def auth_login(request):
    d = await body(request)
    uid = db.use_login(str(d.get("token", "")))
    if not uid:
        return fail("Ссылка для входа устарела. Попросите в боте новую: кнопка «Личный кабинет».", 403)
    return ok(session=db.new_session(uid))


async def auth_web(request):
    d = await body(request)
    name, grade = str(d.get("name", "")).strip()[:30], int(d.get("grade") or 0)
    if not 1 <= grade <= 11:
        return fail("Выберите класс от 1 до 11")
    uid, rec = db.new_web_user(name, grade)
    return ok(session=db.new_session(uid), recovery=rec)


async def auth_recover(request):
    d = await body(request)
    uid = db.by_recovery(str(d.get("code", "")))
    if not uid:
        return fail("Такого кода нет. Проверьте, что он введён полностью, вместе с дефисами.", 404)
    return ok(session=db.new_session(uid))


async def logout(request):
    h = request.headers.get("Authorization", "")
    db.end_session(h[7:].strip() if h.startswith("Bearer ") else "")
    return ok()


# ---------------- кабинет ----------------

def me_data(uid):
    u = db.get_user(uid)
    helper = db.has_helper(uid)
    plan = db.plan_of(uid)
    limit = daily_limit(uid, helper)
    kids = []
    for k in db.children_of(uid):
        ch = db.get_user(k)
        if ch:
            kids.append({"name": ch["name"], "grade": ch["grade"], "week": db.week_report(k),
                         "stats": db.stats(k), "days": db.week_days(k)})
    return {
        "user": {"name": u["name"] or "", "grade": u["grade"] or 0, "voice": u["voice"] or "off",
                 "platform": ids.platform(uid), "plan": plan,
                 "plan_title": PLANS[plan]["title"] if plan in PLANS else "Знакомство",
                 "paid_until": u["paid_until"] if plan != "free" else None, "helper": helper,
                 "recovery": u["recovery"] if ids.platform(uid) == "web" else None},
        "plan_line": plan_line(plan, u["paid_until"]),
        "stats": db.stats(uid), "week": db.week_days(uid),
        "limit": limit, "left": max(0, limit - db.attempts_today(uid)),
        "kids": kids, "parents": len(db.parents_of(uid)),
        "plans": PLANS,
    }


async def api_me(request):
    uid = auth(request)
    if not db.get_user(uid):
        raise web.HTTPUnauthorized(reason="Нужно войти")
    return ok(**me_data(uid))


async def api_profile(request):
    uid = auth(request)
    d = await body(request)
    grade = d.get("grade")
    if grade is not None and not 1 <= int(grade) <= 11:
        return fail("Класс от 1 до 11")
    voice = d.get("voice")
    if voice is not None and voice not in ("off", "boy", "girl", "parent", "lev"):
        return fail("Нет такого голоса")
    db.update_profile(uid, d.get("name"), grade, voice)
    return ok(**me_data(uid))


async def api_log(request):
    uid = auth(request)
    d = await body(request)
    limit = daily_limit(uid, db.has_helper(uid))
    if db.attempts_today(uid) >= limit:
        return fail("На сегодня задания закончились", 429)
    db.log_attempt(uid, bool(d.get("solved")), int(d.get("hints") or 0), int(d.get("tries") or 0))
    if d.get("solved"):
        db.bump_streak(uid, True)
    return ok(stats=db.stats(uid), left=max(0, limit - db.attempts_today(uid)), week=db.week_days(uid))


async def api_parent_code(request):
    uid = auth(request)
    return ok(code=db.make_code(uid))


async def api_parent_link(request):
    uid = auth(request)
    d = await body(request)
    child = db.use_code(str(d.get("code", "")), uid)
    if not child:
        return fail("Такого кода нет или он уже использован", 404)
    ch = db.get_user(child)
    db.outbox_put(child, "Родитель подключил отчёты о твоих занятиях. Он будет видеть, сколько заданий решено и где было трудно.")
    return ok(child={"name": ch["name"], "grade": ch["grade"]}, **me_data(uid))


# ---------------- поддержка ----------------

async def api_support(request):
    d = await body(request)
    text, buttons, understood = support.answer(str(d.get("text", ""))[:500])
    return ok(text=text, buttons=buttons, understood=understood)


async def api_ticket(request):
    d = await body(request)
    kind = d.get("kind") if d.get("kind") in ("refund", "human") else "human"
    text, contact = str(d.get("text", "")).strip(), str(d.get("contact", "")).strip()
    if len(text) < 5:
        return fail("Опишите вопрос чуть подробнее")
    try:
        uid = auth(request)
    except web.HTTPUnauthorized:
        uid = 0
        if not contact:
            return fail("Оставьте почту или телефон, чтобы мы могли ответить")
    answer, tid = support.flow_done(kind, uid, text, contact)
    return ok(text=answer, n=tid)


# ---------------- оплата ----------------

async def after_payment(uid, plan, until, amount, extra_kids=()):
    """Сообщение об оплате и ссылка в закрытый канал, в мессенджер пользователя."""
    title = PLANS.get(plan, {}).get("title", plan)
    for who in [uid, *extra_kids]:
        text = [f"Оплата получена. Тариф «{title}» действует до {until}."]
        plat = ids.platform(who)
        if plat == "tg" and CLOSED_CHANNEL and TG_TOKEN:
            link = await tg_invite(who)
            if link:
                text += ["", "Ссылка в закрытый канал с заданиями, она одноразовая:", link]
        elif plat == "max" and MAX_INVITE:
            text += ["", "Закрытый канал с заданиями в MAX:", MAX_INVITE]
        if PLANS.get(plan, {}).get("helper"):
            text += ["", "Теперь доступно 30 заданий в день и разбор домашки по фото."]
        db.outbox_put(who, "\n".join(text), [[{"text": "Личный кабинет", "url": CABINET_URL}]])


async def tg_invite(uid):
    import aiohttp
    url = f"https://api.telegram.org/bot{TG_TOKEN}/createChatInviteLink"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json={"chat_id": CLOSED_CHANNEL, "member_limit": 1,
                                         "name": f"Подписка {uid}"[:32]}) as r:
                res = await r.json()
                return (res.get("result") or {}).get("invite_link")
    except Exception as e:
        log.error("приглашение не создано: %s", e)
        return None


async def api_pay(request):
    d = await body(request)
    plan, method = d.get("plan"), d.get("method", "card")
    if plan not in PLANS:
        return fail("Нет такого тарифа")
    if not yk.available():
        return ok(fallback=BOOSTY_URL)
    uid = auth(request)
    try:
        res = yk.create(uid, plan, "sbp" if method == "sbp" else "card", str(d.get("email", "")).strip())
    except ValueError as e:
        return fail(str(e))
    except Exception as e:
        log.error("платёж не создан: %s", e)
        return fail("Платёж не создался. Попробуйте ещё раз или оплатите на Boosty.", 502)
    db.order_put(res["id"], uid, plan, PLANS[plan]["price"], res.get("status", "pending"))
    return ok(**res)


async def api_pay_status(request):
    uid = auth(request)
    oid = request.query.get("id", "")
    o = db.order_get(oid)
    if not o or o["uid"] != uid:
        return fail("Платёж не найден", 404)
    if o["status"] != "succeeded" and yk.available():
        try:
            await process_payment(oid)
            o = db.order_get(oid)
        except Exception as e:
            log.warning("статус платежа %s: %s", oid, e)
    return ok(status=o["status"], **(me_data(uid) if o["status"] == "succeeded" else {}))


async def process_payment(oid):
    """Проверяет платёж в ЮKassa и, если он прошёл, открывает тариф. Повторный вызов безопасен."""
    p = yk.get(oid)
    status = p.get("status")
    o = db.order_get(oid)
    if o and o["status"] == "succeeded":
        return
    meta = p.get("metadata") or {}
    uid, plan = int(meta.get("uid", "0") or 0), meta.get("plan")
    if not o and uid and plan:
        db.order_put(oid, uid, plan, float(p["amount"]["value"]), status)
        o = db.order_get(oid)
    if not o:
        return
    db.order_status(oid, status)
    if status == "succeeded":
        until, kids = db.grant_plan(o["uid"], o["plan"], SUB_DAYS, float(p["amount"]["value"]), "yookassa")
        await after_payment(o["uid"], o["plan"], until, o["amount"], kids)
        log.info("оплата %s: тариф %s для %s до %s", oid, o["plan"], o["uid"], until)


async def yookassa_hook(request):
    d = await body(request)
    obj = d.get("object") or {}
    oid = obj.get("id")
    if not oid:
        return fail("нет номера платежа")
    try:
        await process_payment(oid)
    except Exception as e:
        log.error("уведомление ЮKassa %s: %s", oid, e)
        return fail("ошибка", 500)
    return ok()


def find_user_id(data):
    for key in ("telegram_user_id", "user_id", "telegram_id", "subscriber_id"):
        v = data.get(key)
        if v:
            try:
                return int(v)
            except (TypeError, ValueError):
                pass
    payload = data.get("payload") or data.get("data") or {}
    if isinstance(payload, dict):
        return find_user_id(payload)
    return None


async def tribute_hook(request):
    if SECRET:
        got = request.headers.get("X-Api-Key") or request.query.get("secret") or ""
        if got != SECRET:
            return fail("неверный ключ", 403)
    d = await body(request)
    log.info("Tribute: %s", json.dumps(d, ensure_ascii=False)[:500])
    uid = find_user_id(d)
    if not uid:
        return ok(note="нет telegram id")
    amount = float(d.get("amount") or 0)
    until, kids = db.grant_plan(uid, TRIBUTE_PLAN, SUB_DAYS, amount, "tribute")
    await after_payment(uid, TRIBUTE_PLAN, until, amount, kids)
    return ok()


async def health(request):
    return ok(yookassa=yk.available())


def app():
    db.init()
    a = web.Application(middlewares=[cors])
    r = a.router
    r.add_post("/api/auth/telegram", auth_telegram)
    r.add_post("/api/auth/login", auth_login)
    r.add_post("/api/auth/web", auth_web)
    r.add_post("/api/auth/recover", auth_recover)
    r.add_post("/api/logout", logout)
    r.add_get("/api/me", api_me)
    r.add_post("/api/profile", api_profile)
    r.add_post("/api/log", api_log)
    r.add_post("/api/parent/code", api_parent_code)
    r.add_post("/api/parent/link", api_parent_link)
    r.add_post("/api/support", api_support)
    r.add_post("/api/ticket", api_ticket)
    r.add_post("/api/pay", api_pay)
    r.add_get("/api/pay/status", api_pay_status)
    r.add_post("/pay/yookassa", yookassa_hook)
    r.add_post("/pay", tribute_hook)
    r.add_get("/health", health)
    return a


if __name__ == "__main__":
    web.run_app(app(), port=int(os.environ.get("PORT", "8080")))
