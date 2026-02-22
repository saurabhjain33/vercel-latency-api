import os
import json
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Requirement: Enable CORS for any origin
# This works in tandem with your vercel.json headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model based on assignment requirements
class InputPayload(BaseModel):
    regions: List[str]
    threshold_ms: int

# Robust pathing for Vercel's environment to find the JSON in the root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "..", "q-vercel-latency.json")

def get_data():
    """Loads the telemetry data from the local JSON file."""
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback for local testing if file is missing
        return []

# Load data once at startup to improve response speed
DATA = get_data()

@app.post("/api/analyze")
async def analyze(payload: InputPayload):
    result = {}
    
    for region in payload.regions:
        # Filter the global dataset for the requested region
        rows = [r for r in DATA if r.get("region") == region]
        
        if not rows:
            # Return zeros if a region has no data
            result[region] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            }
            continue

        # Extract values for calculations
        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]
        
        # Calculate breaches: count of records STRICTLY ABOVE threshold
        breaches = sum(1 for x in latencies if x > payload.threshold_ms)

        # Standard Python floats for JSON serialization
        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": breaches
        }

    return result

# Simple root route for health checks
@app.get("/")
async def root():
    return {"status": "API is running. Use POST /api/analyze for telemetry data."}
