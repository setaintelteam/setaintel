from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import random
import time
import asyncio
import uuid
import hashlib
from typing import Any

from agi_service import agi_service

app = FastAPI(title="SETA Intelligence Dashboard + Data Center Simulation")

app.mount("/static", StaticFiles(directory="static"), name="static")

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

transactions = []
jobs = {}

def run_matmul(size: int):
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    start = time.time()
    result = np.matmul(a, b)
    elapsed = time.time() - start
    checksum = hashlib.sha3_512(result.tobytes()).hexdigest()
    return {
        "size": size,
        "elapsed_sec": elapsed,
        "checksum": checksum
    }

def run_quantum_bell():
    try:
        from qiskit import QuantumCircuit, Aer, execute
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0,1], [0,1])
        simulator = Aer.get_backend('qasm_simulator')
        result = execute(circuit, simulator, shots=1000).result()
        counts = result.get_counts(circuit)
        return counts
    except ImportError:
        return {"00": 500, "11": 500}

def add_job(job_type: str, params: dict) -> str:
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "id": job_id,
        "type": job_type,
        "params": params,
        "status": "queued",
        "result": None,
        "created": time.time(),
        "started": None,
        "finished": None
    }
    return job_id

def process_job(job_id: str):
    job = jobs[job_id]
    job["status"] = "running"
    job["started"] = time.time()
    if job["type"] == "matmul":
        size = int(job["params"].get("size", 1000))
        job["result"] = run_matmul(size)
    elif job["type"] == "quantum_bell":
        job["result"] = run_quantum_bell()
    else:
        job["result"] = {"error": "Unknown job type"}
    job["status"] = "completed"
    job["finished"] = time.time()

@app.on_event("startup")
async def startup_event():
    # Optionally load more knowledge if a repo directory exists
    # agi_service.load_knowledge_base("repo")
    pass

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.get("/api/status")
async def status():
    return {
        "phi": round(random.uniform(0.9, 0.99), 3),
        "energy_mw": 10000,
        "quantum_qubits": 1000,
        "storage_pb": 8000000,
        "peace_status": "ACTIVE",
        "war_probability": 0.0,
        "active_jobs": sum(1 for j in jobs.values() if j["status"] == "running"),
        "completed_jobs": sum(1 for j in jobs.values() if j["status"] == "completed"),
        "timestamp": time.time()
    }

@app.get("/api/pricing")
async def pricing():
    return PRICING

@app.post("/api/compute/matmul")
async def submit_matmul(payload: dict):
    size = int(payload.get("size", 1000))
    job_id = add_job("matmul", {"size": size})
    process_job(job_id)
    return {"job_id": job_id, "status": jobs[job_id]["status"]}

@app.post("/api/compute/quantum/bell")
async def submit_quantum_bell():
    job_id = add_job("quantum_bell", {})
    process_job(job_id)
    return {"job_id": job_id, "status": jobs[job_id]["status"]}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in jobs:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return jobs[job_id]

@app.get("/api/transactions")
async def get_transactions():
    return transactions[-10:]

@app.websocket("/ws/sim")
async def websocket_sim(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = {
                "phi": round(random.uniform(0.9, 0.99), 3),
                "energy_mw": 10000,
                "fps": 120,
                "resolution": "8K",
                "ts": time.time()
            }
            await websocket.send_json(data)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

@app.get("/api/agi/query")
async def agi_query(q: str):
    return agi_service.generate_answer(q)

@app.get("/api/llm/query")
async def llm_query_alias(q: str):
    return agi_service.generate_answer(q)

# Optional raw simulation API v1
@app.get("/api/v1/status")
async def sim_status_v1():
    return await status()

@app.get("/api/v1/pricing")
async def sim_pricing_v1():
    return PRICING

@app.post("/api/v1/compute/buy")
async def sim_buy_v1(payload: dict):
    compute_type = payload.get("type")
    hours = float(payload.get("hours", 1))
    if compute_type not in PRICING:
        return JSONResponse({"error": "Invalid compute type"}, status_code=400)
    cost = PRICING[compute_type] * hours
    transactions.append({"type": compute_type, "hours": hours, "cost": cost, "timestamp": time.time()})
    return {"cost": cost, "status": "success"}

@app.get("/api/v1/transactions")
async def sim_transactions_v1():
    return transactions[-10:]
