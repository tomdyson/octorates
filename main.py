import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
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
    cache_used = True
    if cache["data"] is None or cache["last_updated"] is None or datetime.now() - cache["last_updated"] > timedelta(minutes=10):
        cache["data"] = await fetch_octopus_data()
        cache["last_updated"] = datetime.now()
        cache_used = False
    return cache["data"], cache_used

@app.get("/api/all_slots")
async def all_slots(response: Response):
    data, cache_used = await get_cached_data()
    sorted_slots = sorted(data["results"], key=lambda x: x["valid_from"])
    response.headers["CACHE_STATUS"] = "HIT" if cache_used else "MISS"
    return [
        {k: v for k, v in slot.items() if k != "payment_method"}
        for slot in sorted_slots
    ]

def validate_count(count: int):
    if count < 1 or count > 48:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 48")

def get_cheapest_slots(slots, count: int):
    # Sort slots by price (value including VAT) in ascending order
    sorted_slots = sorted(slots, key=lambda x: x["value_inc_vat"])
    
    # Select the 'count' number of cheapest slots
    cheapest = sorted_slots[:count]
    
    # Sort the cheapest slots chronologically by their valid_from time
    chronological_cheapest = sorted(cheapest, key=lambda x: x["valid_from"])
    
    # Return a list of dictionaries, each representing a slot
    # Exclude the 'payment_method' key from each slot dictionary
    return [
        {k: v for k, v in slot.items() if k != "payment_method"}
        for slot in chronological_cheapest
    ]

@app.get("/api/cheapest_slots/{count}")
async def cheapest_slots(count: int, response: Response):
    validate_count(count)
    data, cache_used = await get_cached_data()
    response.headers["CACHE_STATUS"] = "HIT" if cache_used else "MISS"
    return get_cheapest_slots(data["results"], count)

@app.get("/api/cheapest_slots_tomorrow/{count}")
async def cheapest_slots_tomorrow(count: int, response: Response):
    validate_count(count)
    data, cache_used = await get_cached_data()
    response.headers["CACHE_STATUS"] = "HIT" if cache_used else "MISS"
    
    # Get tomorrow's date
    tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
    tomorrow_start = datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    # Filter slots for tomorrow
    tomorrow_slots = [
        slot for slot in data["results"]
        if tomorrow_start <= datetime.fromisoformat(slot["valid_from"]) < tomorrow_end
    ]

    return get_cheapest_slots(tomorrow_slots, count) if tomorrow_slots else []

@app.get("/")
async def root(request: Request):
    return FileResponse("static/index.html")