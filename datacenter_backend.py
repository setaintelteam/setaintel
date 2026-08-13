from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import random, time, asyncio

app = FastAPI(title="SETA Data Center Simulation")

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

# In-memory state
transactions = []
total_energy_mw = 10000
total_storage_pb = 8000000

@app.get("/api/v1/status")
async def status():
    return {
        "phi": round(random.uniform(0.9, 0.99), 3),
        "energy_mw": total_energy_mw,
        "quantum_qubits": 1000,
        "storage_pb": total_storage_pb,
        "peace_status": "ACTIVE",
        "war_probability": 0.0,
        "timestamp": time.time()
    }

@app.get("/api/v1/pricing")
async def pricing():
    return PRICING

@app.post("/api/v1/compute/buy")
async def buy_compute(payload: dict):
    compute_type = payload.get("type")
    hours = float(payload.get("hours", 1))
    if compute_type not in PRICING:
        return {"error": "Invalid compute type"}
    cost = PRICING[compute_type] * hours
    transactions.append({
        "type": compute_type,
        "hours": hours,
        "cost": cost,
        "timestamp": time.time()
    })
    return {"cost": cost, "status": "success"}

@app.get("/api/v1/transactions")
async def get_transactions():
    return transactions[-10:]

@app.websocket("/ws/v1/sim")
async def websocket_sim(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = {
                "phi": round(random.uniform(0.9, 0.99), 3),
                "energy_mw": total_energy_mw,
                "fps": 120,
                "resolution": "8K",
                "ts": time.time()
            }
            await websocket.send_json(data)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
