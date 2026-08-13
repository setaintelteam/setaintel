import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="SETA Intelligence Dashboard")

# Read data center API URL from environment; default to localhost
DATA_CENTER_API_URL = os.environ.get("DATACENTER_API_URL", "http://localhost:8001")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.get("/api/status")
async def status():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{DATA_CENTER_API_URL}/api/v1/status")
        resp.raise_for_status()
        return resp.json()

@app.websocket("/ws/sim")
async def websocket_sim(websocket: WebSocket):
    await websocket.accept()
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", f"{DATA_CENTER_API_URL}/ws/v1/sim") as r:
                async for line in r.aiter_lines():
                    if line:
                        await websocket.send_text(line)
    except Exception:
        await websocket.close()

@app.get("/api/llm/query")
async def llm_query(q: str):
    # This can be connected to the real LLM service later
    return {"answer": f"OmniAGI response to: {q}"}
