from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import numpy as np
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Input model
class InputPayload(BaseModel):
    regions: List[str]
    threshold_ms: int

# Load telemetry data
BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE_DIR, "..", "q-vercel-latency.json")

with open(DATA_FILE, "r") as f:
    DATA = json.load(f)

def p95(values):
    if not values:
        return 0.0
    return float(np.percentile(values, 95))

@app.post("/api/analyze")
async def analyze(payload: InputPayload):

    result = {}

    for region in payload.regions:
        rows = [r for r in DATA if r["region"] == region]

        if not rows:
            result[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        breaches = sum(1 for x in latencies if x > payload.threshold_ms)

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": p95(latencies),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": breaches
        }

    return result