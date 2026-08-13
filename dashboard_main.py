from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import random, time, asyncio

app = FastAPI(title="SETA Intelligence Dashboard + Data Center Simulation")

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------
# In-memory simulation state
# ---------------------------------------------------------------------
PRICING = {
    "standard_gpu": 0.10,
    "water_gpu": 1.00,
    "exascale_node": 10000.00,
    "zettaflops": 1000000.00,
    "quantum_100": 100.00,
    "storage_gb": 0.0001,
    "bandwidth_tb": 0.01,
    "llm_inference_1k": 0.0001,
    "seta_query": 0.01,
    "dream_session": 10.00
}

transactions = []          # log of compute purchases
total_energy_mw = 10000    # baseline energy production
total_storage_pb = 8000000 # baseline storage capacity

# ---------------------------------------------------------------------
# Core simulation functions (shared)
# ---------------------------------------------------------------------
def get_sim_status():
    return {
        "phi": round(random.uniform(0.9, 0.99), 3),
        "energy_mw": total_energy_mw,
        "quantum_qubits": 1000,
        "storage_pb": total_storage_pb,
        "peace_status": "ACTIVE",
        "war_probability": 0.0,
        "timestamp": time.time()
    }

def buy_compute(compute_type: str, hours: float = 1.0):
    if compute_type not in PRICING:
        raise ValueError("Invalid compute type")
    cost = PRICING[compute_type] * hours
    transactions.append({
        "type": compute_type,
        "hours": hours,
        "cost": cost,
        "timestamp": time.time()
    })
    return {"cost": cost, "status": "success"}

# ---------------------------------------------------------------------
# Dashboard endpoints (used by the frontend)
# ---------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.get("/api/status")
async def dashboard_status():
    return get_sim_status()

@app.get("/api/pricing")
async def dashboard_pricing():
    return PRICING

@app.post("/api/compute/buy")
async def dashboard_buy(payload: dict):
    try:
        result = buy_compute(payload.get("type"), float(payload.get("hours", 1)))
        return result
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/api/transactions")
async def dashboard_transactions():
    return transactions[-10:]

@app.websocket("/ws/sim")
async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = get_sim_status()
            data["fps"] = 120
            data["resolution"] = "8K"
            await websocket.send_json(data)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

@app.get("/api/llm/query")
async def llm_query(q: str):
    # Replace with real AGI integration later
    return {"answer": f"OmniAGI response to: {q}"}

# ---------------------------------------------------------------------
# Optional: raw simulation API under /api/v1/ (for external use)
# ---------------------------------------------------------------------
@app.get("/api/v1/status")
async def sim_status_v1():
    return get_sim_status()

@app.get("/api/v1/pricing")
async def sim_pricing_v1():
    return PRICING

@app.post("/api/v1/compute/buy")
async def sim_buy_v1(payload: dict):
    try:
        result = buy_compute(payload.get("type"), float(payload.get("hours", 1)))
        return result
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/api/v1/transactions")
async def sim_transactions_v1():
    return transactions[-10:]

@app.websocket("/ws/v1/sim")
async def sim_ws_v1(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = get_sim_status()
            data["fps"] = 120
            data["resolution"] = "8K"
            await websocket.send_json(data)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
