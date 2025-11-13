from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
import time

app = FastAPI(title="Payme Sandbox Microservice")


def ms_now() -> int:
    """Текущее время в миллисекундах."""
    return int(time.time() * 1000)


@app.post("/")
async def payme_entry(payload: dict = Body(...)):
    """
    Универсальная точка входа для песочницы Payme.
    Принимает JSON вида:
    {
      "id": 1,
      "method": "CheckPerformTransaction",
      "params": {...}
    }
    """
    try:
        method = payload.get("method")
        params = payload.get("params", {})
        id_ = payload.get("id")
    except Exception:
        # Ошибка парсинга JSON
        return JSONResponse(
            {"error": {"code": -32700, "message": "Parse error"}, "id": None}
        )

    # ===== Эмуляция методов Payme =====

    if method == "CheckPerformTransaction":
        # Всегда разрешаем платеж
        return JSONResponse({"result": {"allow": True}, "id": id_})

    elif method == "CreateTransaction":
        # Создали транзакцию
        return JSONResponse(
            {
                "result": {
                    "transaction": f"trx-{ms_now()}",
                    "state": 1,
                    "create_time": ms_now(),
                },
                "id": id_,
            }
        )

    elif method == "PerformTransaction":
        # Провели транзакцию
        return JSONResponse(
            {
                "result": {
                    "state": 2,
                    "perform_time": ms_now(),
                },
                "id": id_,
            }
        )

    elif method == "CancelTransaction":
        # Отмена
        return JSONResponse(
            {
                "result": {
                    "state": -1,
                    "cancel_time": ms_now(),
                },
                "id": id_,
            }
        )

    # Неизвестный метод
    return JSONResponse(
        {"error": {"code": -32601, "message": "Method not found"}, "id": id_}
    )
