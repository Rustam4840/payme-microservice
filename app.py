
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time

app = FastAPI(title="Payme Sandbox Microservice")

def ms_now():
    return int(time.time() * 1000)

@app.post("/")
async def payme_entry(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": {"code": -32700, "message": "Parse error"}})

    method = payload.get("method")
    params = payload.get("params", {})
    id_ = payload.get("id")

    if method == "CheckPerformTransaction":
        return JSONResponse({"result": {"allow": True}, "id": id_})
    elif method == "CreateTransaction":
        return JSONResponse({"result": {"transaction": f"trx-{ms_now()}", "state": 1}, "id": id_})
    elif method == "PerformTransaction":
        return JSONResponse({"result": {"state": 2, "perform_time": ms_now()}, "id": id_})
    elif method == "CancelTransaction":
        return JSONResponse({"result": {"state": -1, "cancel_time": ms_now()}, "id": id_})
    else:
        return JSONResponse({"error": {"code": -32601, "message": "Method not found"}, "id": id_})
