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
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputPayload(BaseModel):
    regions: List[str]
    threshold_ms: int

# Correct path logic for Vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Move up one level from /api to the root to find the JSON
DATA_PATH = os.path.join(BASE_DIR, "..", "q-vercel-latency.json")

def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

DATA = load_data()

@app.post("/api/analyze")
async def analyze(payload: InputPayload):
    result = {}
    for region in payload.regions:
        rows = [r for r in DATA if r["region"] == region]
        
        if not rows:
            result[region] = {"avg_latency": 0, "p95_latency": 0, "avg_uptime": 0, "breaches": 0}
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]
        breaches = sum(1 for x in latencies if x > payload.threshold_ms)

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 2),
            "breaches": breaches
        }
    return result
