import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache for storing API data
cache = {
    "data": None,
    "last_updated": None
}

OCTOPUS_API_URL = "https://api.octopus.energy/v1/products/AGILE-FLEX-22-11-25/electricity-tariffs/E-1R-AGILE-FLEX-22-11-25-C/standard-unit-rates/"

async def fetch_octopus_data():
    current_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    params = {
        "period_from": current_time
    }
    url = f"{OCTOPUS_API_URL}?{urllib.parse.urlencode(params)}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Octopus API")

async def get_cached_data():
    if cache["data"] is None or cache["last_updated"] is None or datetime.now() - cache["last_updated"] > timedelta(minutes=10):
        cache["data"] = await fetch_octopus_data()
        cache["last_updated"] = datetime.now()
    return cache["data"]

@app.get("/api/all_slots")
async def all_slots():
    data = await get_cached_data()
    sorted_slots = sorted(data["results"], key=lambda x: x["valid_from"])
    return [
        {k: v for k, v in slot.items() if k != "payment_method"}
        for slot in sorted_slots
    ]

@app.get("/api/cheapest_slots/{count}")
async def cheapest_slots(count: int):
    if count < 1 or count > 48:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 48")
    
    data = await get_cached_data()
    sorted_slots = sorted(data["results"], key=lambda x: x["value_inc_vat"])
    cheapest = sorted_slots[:count]
    chronological_cheapest = sorted(cheapest, key=lambda x: x["valid_from"])
    return [
        {k: v for k, v in slot.items() if k != "payment_method"}
        for slot in chronological_cheapest
    ]

@app.get("/api/cheapest_slots_tomorrow/{count}")
async def cheapest_slots_tomorrow(count: int):
    if count < 1 or count > 48:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 48")
    
    data = await get_cached_data()
    
    # Get tomorrow's date
    tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
    tomorrow_start = datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    # Filter slots for tomorrow
    tomorrow_slots = [
        slot for slot in data["results"]
        if tomorrow_start <= datetime.fromisoformat(slot["valid_from"]) < tomorrow_end
    ]

    if not tomorrow_slots:
        return []

    sorted_slots = sorted(tomorrow_slots, key=lambda x: x["value_inc_vat"])
    cheapest = sorted_slots[:count]
    chronological_cheapest = sorted(cheapest, key=lambda x: x["valid_from"])
    
    return [
        {k: v for k, v in slot.items() if k != "payment_method"}
        for slot in chronological_cheapest
    ]

@app.get("/")
async def root():
    return {"message": "Welcome to OctoRates - the Octopus Energy API viewer"}