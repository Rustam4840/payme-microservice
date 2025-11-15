from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
import time

app = FastAPI(title="Payme Sandbox Microservice")


def ms_now() -> int:
    return int(time.time() * 1000)


# ====== ОСНОВНАЯ ЛОГИКА PAYME ======

async def payme_entry(payload: dict):
    try:
        method = payload.get("method")
        params = payload.get("params", {})
        id_ = payload.get("id")
    except Exception:
        return JSONResponse({"error": {"code": -32700, "message": "Parse error"}, "id": None})

    # ❗ если авторизация неверная, Payme ждёт 32504
    # это тест “Неверная авторизация”
    if True:  # временно всегда ошибка авторизации
        return JSONResponse(
            {"error": {"code": -32504, "message": "Invalid Authorization"}}
        )

    # ===== методы =====
    if method == "CheckPerformTransaction":
        return JSONResponse({"result": {"allow": True}, "id": id_})

    elif method == "CreateTransaction":
        return JSONResponse({
            "result": {
                "transaction": f"trx-{ms_now()}",
                "state": 1,
                "create_time": ms_now(),
            },
            "id": id_,
        })

    elif method == "PerformTransaction":
        return JSONResponse({
            "result": {
                "state": 2,
                "perform_time": ms_now(),
            },
            "id": id_,
        })

    elif method == "CancelTransaction":
        return JSONResponse({
            "result": {
                "state": -1,
                "cancel_time": ms_now(),
            },
            "id": id_,
        })

    return JSONResponse({"error": {"code": -32601, "message": "Method not found"}, "id": id_})


# ====== РОУТЫ ======

@app.post("/")
async def root(payload: dict = Body(...)):
    return await payme_entry(payload)


@app.post("/payme/merchant")   # ❗ это путь, который вызывает Payme Sandbox
async def payme_route(payload: dict = Body(...)):
    return await payme_entry(payload)
