"""Оплата на сайте через ЮKassa: карта, МИР, СБП по QR-коду. Чеки по 54-ФЗ формирует ЮKassa.

Переменные окружения:
  YOOKASSA_SHOP_ID     идентификатор магазина из личного кабинета ЮKassa
  YOOKASSA_SECRET      секретный ключ (Интеграция -> Ключи API)
  YOOKASSA_RECEIPT     1, если подключены «Чеки от ЮKassa»: тогда в платёж добавляется чек
  SITE_URL             адрес сайта, куда вернуть покупателя после оплаты

В личном кабинете ЮKassa в разделе «HTTP-уведомления» укажите адрес
https://<домен сервера>/pay/yookassa и отметьте событие payment.succeeded.
Подпись у уведомлений ЮKassa нет, поэтому сервер не верит телу уведомления,
а заново запрашивает платёж по его номеру. Так подделать оплату нельзя.
"""
import base64, json, logging, os, ssl, urllib.request, urllib.error, uuid

from common import PLANS

log = logging.getLogger("yookassa")
API = "https://api.yookassa.ru/v3"
SHOP = os.environ.get("YOOKASSA_SHOP_ID", "")
SECRET = os.environ.get("YOOKASSA_SECRET", "")
RECEIPT = os.environ.get("YOOKASSA_RECEIPT", "") == "1"
SITE = os.environ.get("SITE_URL", "https://smekairu.github.io/Smekai/")
CTX = ssl.create_default_context()


def available():
    return bool(SHOP and SECRET)


def _call(method, path, body=None, key=None):
    auth = base64.b64encode(f"{SHOP}:{SECRET}".encode()).decode()
    headers = {"Authorization": "Basic " + auth, "Content-Type": "application/json"}
    if key:
        headers["Idempotence-Key"] = key
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ЮKassa {e.code}: {e.read().decode()[:300]}")


def create(uid, plan, method="card", email=""):
    """Создаёт платёж. method: card (страница оплаты ЮKassa) или sbp (QR-код СБП).
    Возвращает {'id', 'url'} для карты или {'id', 'qr'} для СБП."""
    p = PLANS[plan]
    body = {
        "amount": {"value": f"{p['price']:.2f}", "currency": "RUB"},
        "capture": True,
        "description": f"Смекай, тариф «{p['title']}», 1 месяц",
        "metadata": {"uid": str(uid), "plan": plan},
    }
    if method == "sbp":
        body["payment_method_data"] = {"type": "sbp"}
        body["confirmation"] = {"type": "qr"}
    else:
        body["confirmation"] = {"type": "redirect", "return_url": SITE + "kabinet/#paid"}
    if RECEIPT:
        if not email:
            raise ValueError("Для чека нужна почта")
        body["receipt"] = {
            "customer": {"email": email},
            "items": [{
                "description": f"Доступ к сервису Смекай, тариф «{p['title']}», 1 месяц",
                "quantity": "1.00",
                "amount": {"value": f"{p['price']:.2f}", "currency": "RUB"},
                "vat_code": 1,
                "payment_mode": "full_payment",
                "payment_subject": "service",
            }],
        }
    res = _call("POST", "/payments", body, key=str(uuid.uuid4()))
    conf = res.get("confirmation") or {}
    out = {"id": res["id"], "status": res.get("status")}
    if conf.get("type") == "qr":
        out["qr"] = conf.get("confirmation_data")
    else:
        out["url"] = conf.get("confirmation_url")
    return out


def get(payment_id):
    return _call("GET", f"/payments/{payment_id}")
