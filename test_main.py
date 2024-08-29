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