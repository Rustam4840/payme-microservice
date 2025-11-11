from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time

app = FastAPI(title="Payme Sandbox Microservice")

@app.get("/")
async def health():
    return {"ok": True, "service": "payme-microservice"}

def ms_now() -> int:
    return int(time.time() * 1000)

@app.post("/payme/merchant")
async def payme_entry(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": {"code": -32700, "message": "Parse error"}})

    method = payload.get("method")
    _id = payload.get("id")

    if method == "CheckPerformTransaction":
        return JSONResponse({"result": {"allow": True}, "id": _id})
    elif method == "CreateTransaction":
        return JSONResponse({"result": {"transaction": f"trx-{ms_now()}", "state": 1}, "id": _id})
    elif method == "PerformTransaction":
        return JSONResponse({"result": {"state": 2, "perform_time": ms_now()}, "id": _id})
    elif method == "CancelTransaction":
        return JSONResponse({"result": {"state": -1, "cancel_time": ms_now()}, "id": _id})
    else:
        return JSONResponse({"error": {"code": -32601, "message": "Method not found"}, "id": _id})
