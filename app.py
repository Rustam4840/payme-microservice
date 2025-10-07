from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import time

app = FastAPI(title="Payme Sandbox Microservice")

# Разрешённый заголовок авторизации (для песочницы можно оставить пустым,
# тогда любой неправильный/пустой заголовок будет считаться невалидным)
PAYME_X_AUTH = os.getenv("PAYME_X_AUTH", "").strip()  # например: "Basic AAA...="

def ms_now() -> int:
    return int(time.time() * 1000)

def err(code: int, msg: str, id_: int | None = None):
    return JSONResponse({"error": {"code": code, "message": msg}, "id": id_})

@app.post("/payme/merchant")
async def payme_merchant(request: Request):
    # 1) Проверка авторизации — первый тест песочницы как раз на это
    auth = request.headers.get("Authorization", "")
    if not PAYME_X_AUTH or auth != PAYME_X_AUTH:
        # Код песочницы при неверном Authorization
        return err(-32504, "Неверная авторизация")

    # 2) Разбор JSON
    try:
        payload = await request.json()
    except Exception:
        return err(-32700, "Parse error")

    method = payload.get("method")
    params = payload.get("params", {})
    id_    = payload.get("id")

    # 3) Минимальные заглушки под основные методы
    if method == "CheckPerformTransaction":
        # В успешном кейсе должен быть result.allow = True/False
        return JSONResponse({"result": {"allow": True}, "id": id_})

    if method == "CreateTransaction":
        # Возвращаем фиктивный transaction и state=1
        return JSONResponse({"result": {"transaction": f"tr-{ms_now()}", "state": 1, "id": id_}})

    if method == "PerformTransaction":
        # Ставим state=2 и время
        return JSONResponse({"result": {"state": 2, "perform_time": ms_now(), "id": id_}})

    if method == "CancelTransaction":
        # Ставим state=-1 и cancel_time
        return JSONResponse({"result": {"state": -1, "cancel_time": ms_now(), "id": id_}})

    # Неизвестный метод
    return err(-32601, "Method not found", id_)
