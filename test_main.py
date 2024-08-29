from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app, fetch_octopus_data, get_cached_data

client = TestClient(app)

@pytest.fixture
def mock_octopus_data():
    return {
        "results": [
            {
                "value_exc_vat": 10,
                "value_inc_vat": 12,
                "valid_from": "2023-04-01T00:00:00Z",
                "valid_to": "2023-04-01T00:30:00Z"
            },
            {
                "value_exc_vat": 15,
                "value_inc_vat": 18,
                "valid_from": "2023-04-01T00:30:00Z",
                "valid_to": "2023-04-01T01:00:00Z"
            }
        ]
    }

@pytest.mark.asyncio
async def test_fetch_octopus_data(mock_octopus_data):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = AsyncMock(status_code=200, json=AsyncMock(return_value=mock_octopus_data))
        result = await fetch_octopus_data()
        assert result == mock_octopus_data

@pytest.mark.asyncio
async def test_get_cached_data(mock_octopus_data):
    with patch('main.fetch_octopus_data', return_value=mock_octopus_data):
        data, cache_used = await get_cached_data()
        assert data == mock_octopus_data
        assert cache_used == False

        # Test cache hit
        data, cache_used = await get_cached_data()
        assert data == mock_octopus_data
        assert cache_used == True

def test_all_slots(mock_octopus_data):
    with patch('main.get_cached_data', return_value=(mock_octopus_data, True)):
        response = client.get("/api/all_slots")
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert "payment_method" not in response.json()[0]
        assert response.headers["CACHE_STATUS"] == "HIT"

def test_cheapest_slots(mock_octopus_data):
    with patch('main.get_cached_data', return_value=(mock_octopus_data, False)):
        response = client.get("/api/cheapest_slots/1")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["value_inc_vat"] == 12
        assert response.headers["CACHE_STATUS"] == "MISS"

def test_cheapest_slots_invalid_count():
    response = client.get("/api/cheapest_slots/0")
    assert response.status_code == 400
    assert "Count must be between 1 and 48" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cheapest_slots_tomorrow(mock_octopus_data):
    tomorrow = datetime.now(timezone.utc).date().isoformat()
    mock_octopus_data["results"][0]["valid_from"] = f"{tomorrow}T00:00:00Z"
    mock_octopus_data["results"][1]["valid_from"] = f"{tomorrow}T00:30:00Z"

    with patch('main.get_cached_data', return_value=(mock_octopus_data, True)):
        response = client.get("/api/cheapest_slots_tomorrow/2")
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["valid_from"].startswith(tomorrow)
        assert response.headers["CACHE_STATUS"] == "HIT"