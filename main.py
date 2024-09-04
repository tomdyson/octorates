import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from circuitbreaker import circuit
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from tenacity import retry, stop_after_attempt, wait_exponential


class CacheControlMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, cache_time: int = 3600):
        super().__init__(app)
        self.cache_time = cache_time

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = f"public, max-age={self.cache_time}"
        return response


app = FastAPI()

# Add the CacheControlMiddleware
app.add_middleware(CacheControlMiddleware, cache_time=3600)  # Cache for 1 hour

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache for storing API data
cache = {"data": None, "last_updated": None}

OCTOPUS_API_URL = "https://api.octopus.energy/v1/products/AGILE-FLEX-22-11-25/electricity-tariffs/E-1R-AGILE-FLEX-22-11-25-C/standard-unit-rates/"


# Circuit breaker pattern: Stops calling the function after 5 consecutive failures,
# and waits for 30 seconds before allowing retries
@circuit(failure_threshold=5, recovery_timeout=30)
# Retry mechanism: Attempts the function up to 3 times with exponential backoff
# starting at 1 second, with a minimum of 4 seconds and maximum of 10 seconds between retries
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_octopus_data():
    current_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    params = {"period_from": current_time}
    url = f"{OCTOPUS_API_URL}?{urllib.parse.urlencode(params)}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to fetch data from Octopus API: {str(e)}",
            )


async def get_cached_data():
    cache_used = True
    if (
        cache["data"] is None
        or cache["last_updated"] is None
        or datetime.now() - cache["last_updated"] > timedelta(minutes=10)
    ):
        try:
            new_data = await fetch_octopus_data()
            cache["data"] = new_data
            cache["last_updated"] = datetime.now()
            cache_used = False
        except HTTPException:
            if cache["data"] is None:
                raise  # Re-raise the exception if we don't have any cached data
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
    try:
        data, cache_used = await get_cached_data()
        response.headers["CACHE_STATUS"] = "HIT" if cache_used else "MISS"
        return get_cheapest_slots(data["results"], count)
    except HTTPException:
        response.headers["CACHE_STATUS"] = "ERROR"
        return [{"error": "Unable to fetch data, please try again later"}]


@app.get("/api/cheapest_slots_tomorrow/{count}")
async def cheapest_slots_tomorrow(count: int, response: Response):
    validate_count(count)
    data, cache_used = await get_cached_data()
    response.headers["CACHE_STATUS"] = "HIT" if cache_used else "MISS"

    # Get tomorrow's date
    tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
    tomorrow_start = datetime.combine(tomorrow, datetime.min.time()).replace(
        tzinfo=timezone.utc
    )
    tomorrow_end = tomorrow_start + timedelta(days=1)

    # Filter slots for tomorrow
    tomorrow_slots = [
        slot
        for slot in data["results"]
        if tomorrow_start <= datetime.fromisoformat(slot["valid_from"]) < tomorrow_end
    ]

    return get_cheapest_slots(tomorrow_slots, count) if tomorrow_slots else []


@app.get("/")
async def root(request: Request):
    return FileResponse("static/index.html")
