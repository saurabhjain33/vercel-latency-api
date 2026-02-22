import os
import json
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputPayload(BaseModel):
    regions: List[str]
    threshold_ms: int

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "..", "q-vercel-latency.json")

# Load data once
with open(DATA_FILE, "r") as f:
    DATA = json.load(f)

@app.post("/api/analyze")
async def analyze(payload: InputPayload):
    result = {}
    for region in payload.regions:
        rows = [r for r in DATA if r.get("region") == region]
        if not rows:
            result[region] = {"avg_latency": 0, "p95_latency": 0, "avg_uptime": 0, "breaches": 0}
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]
        
        # EXACT LOGIC: Strictly greater than threshold
        breaches = sum(1 for x in latencies if x > payload.threshold_ms)

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": breaches
        }
    return result
