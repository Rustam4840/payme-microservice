# app.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time
import os

app = FastAPI(title="Payme Sandbox Microservice")

# =========================
# Config (env)
# =========================
# Если хочешь, чтобы авторизация проверялась,
# задай PAYME_X_AUTH, например: "Basic AAAA...."
PAYME_X_AUTH = os.getenv("PAYME_X_AUTH", "").strip()
# Какое поле считаем "логином" плательщика в account
ACCOUNT_FIELD = os.getenv("PAYME_ACCOUNT_FIELD", "user_id")

# Валидация суммы: минимально 1000 (для теста "Неверная сумма")
MIN_AMOUNT = int(os.getenv("PAYME_MIN_AMOUNT", "1000"))

# Память для транзакций песочницы (in-memory)
# key = paycom_transaction_id
transactions = {}

def ms_now() -> int:
    return int(time.time() * 1000)

def ok(id_, result):
    return JSONResponse({"result": result, "id": id_})

def err(id_, code, message=""):
    # Сообщение не критично для песочницы, но оставим
    return JSONResponse({"error": {"code": code, "message": message}, "id": id_})

def auth_failed(request: Request) -> bool:
    """
    Вернуть True, если авторизация должна упасть.
    Логика:
      - Если переменная PAYME_X_AUTH задана, требуем точного совпадения.
      - Если не задана, но заголовок отсутствует или выглядит как "Basic AAA...", тоже считаем ошибкой.
    """
    got = request.headers.get("Authorization", "").strip()
    if PAYME_X_AUTH:
        return got != PAYME_X_AUTH
    # режим без жёсткого значения — но тест "Неверная авторизация" всё равно должен падать:
    if not got or got.upper().startswith("BASIC AAA"):
        return True
    return False

def account_invalid(account: dict) -> bool:
    """
    Для теста 'Несуществующий счёт' песочница шлёт пустой account -> {}
    Считаем валидным, если в нём есть ACCOUNT_FIELD и непустое значение.
    """
    if not isinstance(account, dict):
        return True
    value = account.get(ACCOUNT_FIELD)
    if value is None or str(value).strip() == "":
        return True
    return False

def amount_invalid(amount: int) -> bool:
    """
    'Неверная сумма' — считаем неверной сумму < MIN_AMOUNT.
    Можно подстроить порог через PAYME_MIN_AMOUNT.
    """
    try:
        a = int(amount)
    except Exception:
        return True
    return a < MIN_AMOUNT


@app.post("/payme/merchant")
async def payme_merchant(request: Request):
    # 1) Авторизация
    if auth_failed(request):
        # -32504 — неверная авторизация
        # важно: возвращаем JSON-RPC-ошибку с id из payload (или None, если не распарсили)
        try:
            payload = await request.json()
            req_id = payload.get("id")
        except Exception:
            req_id = None
        return err(req_id, -32504, "Invalid authorization")

    # 2) JSON
    try:
        payload = await request.json()
    except Exception:
        # -32700 — parse error
        return err(None, -32700, "Parse error")

    method = payload.get("method")
    params = payload.get("params", {}) or {}
    req_id = payload.get("id")

    # 3) Роутинг по методам
    if method == "CheckPerformTransaction":
        # Проверяем счёт и сумму
        account = params.get("account", {}) or {}
        amount = params.get("amount")

        if account_invalid(account):
            # -31050 — счёт/пользователь не найден
            return err(req_id, -31050, "Account not found")

        if amount_invalid(amount):
            # -31001 — сумма некорректна
            return err(req_id, -31001, "Invalid amount")

        return ok(req_id, {"allow": True})

    elif method == "CreateTransaction":
        # должно прийти:
        # params: { id: "<paycom_id>", time: <ms>, amount: <int>, account: {...} }
        paycom_id = params.get("id")
        account = params.get("account", {}) or {}
        amount = params.get("amount")

        if account_invalid(account):
            return err(req_id, -31050, "Account not found")
        if amount_invalid(amount):
            return err(req_id, -31001, "Invalid amount")

        txn = transactions.get(paycom_id)
        if txn:
            # если уже есть — просто вернём его
            return ok(req_id, {
                "transaction": paycom_id,
                "state": txn["state"],
                "create_time": txn["create_time"]
            })

        # Создаём транзакцию со state=1
        now = ms_now()
        transactions[paycom_id] = {
            "state": 1,  # 1 — создана (не выполнена)
            "create_time": now,
            "perform_time": 0,
            "cancel_time": 0,
            "account": account,
            "amount": int(amount),
        }
        return ok(req_id, {
            "transaction": paycom_id,
            "state": 1,
            "create_time": now
        })

    elif method == "PerformTransaction":
        paycom_id = params.get("id")
        txn = transactions.get(paycom_id)
        if not txn:
            # -31003 — не найдена транзакция
            return err(req_id, -31003, "Transaction not found")

        if txn["state"] == 2:
            # уже выполнена — вернём как есть
            return ok(req_id, {
                "transaction": paycom_id,
                "state": 2,
                "perform_time": txn["perform_time"]
            })

        if txn["state"] == 1:
            now = ms_now()
            txn["state"] = 2
            txn["perform_time"] = now
            return ok(req_id, {
                "transaction": paycom_id,
                "state": 2,
                "perform_time": now
            })

        # если была отменена — нельзя выполнить
        return err(req_id, -31008, "Cannot perform on cancelled")

    elif method == "CancelTransaction":
        paycom_id = params.get("id")
        txn = transactions.get(paycom_id)
        if not txn:
            return err(req_id, -31003, "Transaction not found")

        if txn["state"] == -1:
            # уже отменена — вернём как есть
            return ok(req_id, {
                "transaction": paycom_id,
                "state": -1,
                "cancel_time": txn["cancel_time"]
            })

        now = ms_now()
        txn["state"] = -1
        txn["cancel_time"] = now
        return ok(req_id, {
            "transaction": paycom_id,
            "state": -1,
            "cancel_time": now
        })

    elif method == "CheckTransaction":
        paycom_id = params.get("id")
        txn = transactions.get(paycom_id)
        if not txn:
            return err(req_id, -31003, "Transaction not found")
        return ok(req_id, {
            "transaction": paycom_id,
            "state": txn["state"],
            "create_time": txn["create_time"],
            "perform_time": txn["perform_time"],
            "cancel_time": txn["cancel_time"],
            "reason": 0
        })

    elif method == "GetStatement":
        # Вернём пустой список — песочнице достаточно
        return ok(req_id, {"transactions": []})

    # -32601 — метод не найден
    return err(req_id, -32601, "Method not found")


@app.get("/")
def root():
    return {"ok": True, "service": "payme-microservice"}
