from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

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

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

# We'll add tests here one by one

@pytest.mark.asyncio
async def test_fetch_octopus_data(mock_octopus_data):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_octopus_data
        mock_get.return_value = mock_response
        result = await fetch_octopus_data()
        assert await result == mock_octopus_data

    # Verify that the mock was called with the correct URL
    expected_url = "https://api.octopus.energy/v1/products/AGILE-FLEX-22-11-25/electricity-tariffs/E-1R-AGILE-FLEX-22-11-25-C/standard-unit-rates/"
    mock_get.assert_called_once()
    actual_url = mock_get.call_args[0][0]
    assert actual_url.startswith(expected_url)

@pytest.mark.asyncio
async def test_get_cached_data(mock_octopus_data):
    with patch('main.fetch_octopus_data', return_value=mock_octopus_data) as mock_fetch:
        # First call should fetch new data
        data, cache_used = await get_cached_data()
        assert data == mock_octopus_data
        assert cache_used == False
        mock_fetch.assert_called_once()

        # Second call within 10 minutes should use cached data
        data, cache_used = await get_cached_data()
        assert data == mock_octopus_data
        assert cache_used == True
        mock_fetch.assert_called_once()  # Should still be called only once

    # Test cache expiration
    with patch('main.fetch_octopus_data', return_value=mock_octopus_data) as mock_fetch:
        with patch('main.datetime') as mock_datetime:
            # Set current time to 11 minutes after the last update
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=11)
            data, cache_used = await get_cached_data()
            assert data == mock_octopus_data
            assert cache_used == False
            mock_fetch.assert_called_once()

@pytest.mark.asyncio
async def test_all_slots(mock_octopus_data):
    async def mock_get_cached_data():
        return mock_octopus_data, True

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch('main.get_cached_data', new=mock_get_cached_data):
            response = await ac.get("/api/all_slots")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert "payment_method" not in data[0]
            assert response.headers["CACHE_STATUS"] == "HIT"

            # Verify that the slots are sorted by valid_from
            assert data[0]["valid_from"] < data[1]["valid_from"]

        # Test with cache miss
        async def mock_get_cached_data_miss():
            return mock_octopus_data, False

        with patch('main.get_cached_data', new=mock_get_cached_data_miss):
            response = await ac.get("/api/all_slots")
            assert response.status_code == 200
            assert response.headers["CACHE_STATUS"] == "MISS"

@pytest.mark.asyncio
async def test_cheapest_slots(mock_octopus_data):
    async def mock_get_cached_data():
        return mock_octopus_data, True

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch('main.get_cached_data', new=mock_get_cached_data):
            response = await ac.get("/api/cheapest_slots/1")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["value_inc_vat"] == 12  # The cheapest slot
            assert "payment_method" not in data[0]
            assert response.headers["CACHE_STATUS"] == "HIT"

            # Test with a different count
            response = await ac.get("/api/cheapest_slots/2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["value_inc_vat"] == 12
            assert data[1]["value_inc_vat"] == 18

        # Test invalid count
        response = await ac.get("/api/cheapest_slots/0")
        assert response.status_code == 400
        assert response.json()["detail"] == "Count must be between 1 and 48"

        response = await ac.get("/api/cheapest_slots/49")
        assert response.status_code == 400
        assert response.json()["detail"] == "Count must be between 1 and 48"

@pytest.mark.asyncio
async def test_cheapest_slots_tomorrow(mock_octopus_data):
    async def mock_get_cached_data():
        return mock_octopus_data, True

    tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
    tomorrow_start = datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc)

    # Modify mock data to include tomorrow's slots
    mock_octopus_data_tomorrow = mock_octopus_data.copy()
    mock_octopus_data_tomorrow["results"] = [
        {
            "value_exc_vat": 8,
            "value_inc_vat": 9.6,
            "valid_from": (tomorrow_start + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            "valid_to": (tomorrow_start + timedelta(hours=1, minutes=30)).isoformat().replace("+00:00", "Z")
        },
        {
            "value_exc_vat": 12,
            "value_inc_vat": 14.4,
            "valid_from": (tomorrow_start + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
            "valid_to": (tomorrow_start + timedelta(hours=2, minutes=30)).isoformat().replace("+00:00", "Z")
        }
    ]

    async def mock_get_cached_data_tomorrow():
        return mock_octopus_data_tomorrow, True

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch('main.get_cached_data', new=mock_get_cached_data_tomorrow):
            response = await ac.get("/api/cheapest_slots_tomorrow/1")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["value_inc_vat"] == 9.6  # The cheapest slot for tomorrow
            assert "payment_method" not in data[0]
            assert response.headers["CACHE_STATUS"] == "HIT"

            # Test with a different count
            response = await ac.get("/api/cheapest_slots_tomorrow/2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["value_inc_vat"] == 9.6
            assert data[1]["value_inc_vat"] == 14.4

        # Test with no slots for tomorrow
        async def mock_get_cached_data_no_tomorrow():
            return mock_octopus_data, True

        with patch('main.get_cached_data', new=mock_get_cached_data_no_tomorrow):
            response = await ac.get("/api/cheapest_slots_tomorrow/1")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0

        # Test invalid count
        response = await ac.get("/api/cheapest_slots_tomorrow/0")
        assert response.status_code == 400
        assert response.json()["detail"] == "Count must be between 1 and 48"

        response = await ac.get("/api/cheapest_slots_tomorrow/49")
        assert response.status_code == 400
        assert response.json()["detail"] == "Count must be between 1 and 48"