import os
import json
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Requirement: Enable CORS for any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputPayload(BaseModel):
    regions: List[str]
    threshold_ms: int

# Robust pathing for Vercel's environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "..", "q-vercel-latency.json")

def get_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

DATA = get_data()

@app.post("/api/analyze")
async def analyze(payload: InputPayload):
    result = {}
    
    for region in payload.regions:
        # Filter data for the specific region
        rows = [r for r in DATA if r["region"] == region]
        
        if not rows:
            result[region] = {"avg_latency": 0, "p95_latency": 0, "avg_uptime": 0, "breaches": 0}
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]
        
        # Calculate breaches based on the threshold provided in the POST body
        breaches = sum(1 for x in latencies if x > payload.threshold_ms)

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": breaches
        }

    return result
