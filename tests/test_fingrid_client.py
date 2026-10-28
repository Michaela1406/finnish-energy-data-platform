from datetime import datetime
from unittest.mock import Mock

import pytest
import requests
import responses

from src.ingestion.fingrid_client import (
    FingridAPIError,
    FingridClient,
)


@pytest.fixture
def client():
    """Create a client without making real API requests."""
    return FingridClient(api_key="test-api-key")


@pytest.fixture
def sample_response():
    """A minimal successful Fingrid API response."""
    return {
        "data": [
            {
                "startTime": "2026-10-20T10:00:00Z",
                "value": 1234.5,
            }
        ],
        "pagination": {
            "perPage": 10,
        },
    }


def test_get_dataset_returns_records(
    client, sample_response, monkeypatch
):
    # Arrange
    response = Mock()
    response.json.return_value = sample_response
    response.raise_for_status.return_value = None

    get_mock = Mock(return_value=response)
    monkeypatch.setattr(client.session, "get", get_mock)

    # Act
    result = client.get_dataset(
        dataset_id=193,
        start_time=datetime(2026, 10, 20, 10, 0),
        end_time=datetime(2026, 10, 20, 11, 0),
    )

    # Assert
    assert result == sample_response["data"]
    assert len(result) == 1

    get_mock.assert_called_once()
    assert get_mock.call_args.kwargs["params"]["page"] == 1
    assert get_mock.call_args.kwargs["headers"]["x-api-key"] == (
        "test-api-key"
    )


def test_get_dataset_fetches_multiple_pages(
    client, monkeypatch
):
    # Arrange: the first page is full; the second is partial.
    first_response = Mock()
    first_response.json.return_value = {
        "data": [{"value": 1}, {"value": 2}],
        "pagination": {"perPage": 2},
    }
    first_response.raise_for_status.return_value = None

    second_response = Mock()
    second_response.json.return_value = {
        "data": [{"value": 3}],
        "pagination": {"perPage": 2},
    }
    second_response.raise_for_status.return_value = None

    get_mock = Mock(side_effect=[first_response, second_response])
    monkeypatch.setattr(client.session, "get", get_mock)

    # Avoid waiting three seconds between pages.
    monkeypatch.setattr(
        "src.ingestion.fingrid_client.time.sleep",
        lambda _: None,
    )

    # Act
    result = client.get_dataset(
        dataset_id=193,
        start_time=datetime(2026, 10, 20, 10, 0),
        end_time=datetime(2026, 10, 20, 11, 0),
    )

    # Assert
    assert result == [
        {"value": 1},
        {"value": 2},
        {"value": 3},
    ]
    assert get_mock.call_count == 2
    assert get_mock.call_args_list[0].kwargs["params"]["page"] == 1
    assert get_mock.call_args_list[1].kwargs["params"]["page"] == 2

    
def test_get_dataset_handles_empty_data(client, monkeypatch):
    # Arrange
    response = Mock()
    response.json.return_value = {
        "data": [],
        "pagination": {"perPage": 2},
    }
    response.raise_for_status.return_value = None

    get_mock = Mock(return_value=response)
    monkeypatch.setattr(client.session, "get", get_mock)

    # Act
    result = client.get_dataset(
        dataset_id=193,
        start_time=datetime(2026, 10, 20, 10, 0),
        end_time=datetime(2026, 10, 20, 11, 0),
    )

    # Assert
    assert result == []
    get_mock.assert_called_once()
    assert get_mock.call_args.kwargs["params"]["page"] == 1


def test_get_dataset_pagination_termination(client, monkeypatch):
    # Arrange: the first page is full; the second is empty.
    first_response = Mock()
    first_response.json.return_value = {
        "data": [{"value": 1}, {"value": 2}],
        "pagination": {"perPage": 2},
    }
    first_response.raise_for_status.return_value = None

    second_response = Mock()
    second_response.json.return_value = {
        "data": [],
        "pagination": {"perPage": 2},
    }
    second_response.raise_for_status.return_value = None

    get_mock = Mock(side_effect=[first_response, second_response])
    monkeypatch.setattr(client.session, "get", get_mock)

    # Avoid waiting three seconds between pages.
    monkeypatch.setattr(
        "src.ingestion.fingrid_client.time.sleep",
        lambda _: None,
    )

    # Act
    result = client.get_dataset(
        dataset_id=193,
        start_time=datetime(2026, 10, 20, 10, 0),
        end_time=datetime(2026, 10, 20, 11, 0),
    )

    # Assert
    assert result == [{"value": 1}, {"value": 2}]
    assert get_mock.call_count == 2
    assert get_mock.call_args_list[0].kwargs["params"]["page"] == 1
    assert get_mock.call_args_list[1].kwargs["params"]["page"] == 2
    
    
def test_get_dataset_wraps_timeout_in_api_error(
    client, monkeypatch
):
    # Arrange
    get_mock = Mock(
        side_effect=requests.Timeout("Connection timed out")
    )
    monkeypatch.setattr(client.session, "get", get_mock)

    # Act / Assert
    with pytest.raises(FingridAPIError) as exc_info:
        client.get_dataset(
            dataset_id=193,
            start_time=datetime(2026, 10, 20, 10, 0),
            end_time=datetime(2026, 10, 20, 11, 0),
        )

    assert "dataset 193" in str(exc_info.value)
    assert "page 1" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, requests.Timeout)


def test_get_dataset_wraps_too_many_requests(client, monkeypatch):
    # Arrange
    get_mock = Mock(
        side_effect=requests.HTTPError("429 Too Many Requests")
    )
    monkeypatch.setattr(client.session, "get", get_mock)

    # Act / Assert
    with pytest.raises(FingridAPIError) as exc_info:
        client.get_dataset(
            dataset_id=193,
            start_time=datetime(2026, 10, 20, 10, 0),
            end_time=datetime(2026, 10, 20, 11, 0),
        )

    assert "dataset 193" in str(exc_info.value)
    assert "page 1" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, requests.HTTPError)


def test_get_dataset_wraps_http_error(
    client, monkeypatch
):
    # Arrange
    response = Mock()
    response.raise_for_status.side_effect = (
        requests.HTTPError("404 Client Error")
    )

    get_mock = Mock(return_value=response)
    monkeypatch.setattr(client.session, "get", get_mock)

    # Act / Assert
    with pytest.raises(FingridAPIError, match="Failed to retrieve dataset"):
        client.get_dataset(
            dataset_id=193,
            start_time=datetime(2026, 10, 20, 10, 0),
            end_time=datetime(2026, 10, 20, 11, 0),
        )


@responses.activate
def test_get_dataset_retries_503_then_succeeds():
    
    # Arrange: return 503 first, then a successful response.
    url = "https://data.fingrid.fi/api/datasets/193/data"

    responses.add(
        responses.GET,
        url,
        status=503,
        json={"message": "Service temporarily unavailable"},
    )

    responses.add(
        responses.GET,
        url,
        status=200,
        json={
            "data": [
                {
                    "startTime": "2026-10-20T10:00:00Z",
                    "value": 1234.5,
                }
            ],
            "pagination": {"perPage": 10},
        },
    )

    client = FingridClient(api_key="test-api-key")

    # Act
    result = client.get_dataset(
        dataset_id=193,
        start_time=datetime(2026, 10, 20, 10, 0),
        end_time=datetime(2026, 10, 20, 11, 0),
    )

    # Assert
    assert len(result) == 1
    assert result[0]["value"] == 1234.5

    # The same URL was requested twice: 503, then 200.
    assert len(responses.calls) == 2
    assert responses.calls[0].response.status_code == 503
    assert responses.calls[1].response.status_code == 200


@responses.activate
def test_get_dataset_retries_503_then_fails():
    # Arrange: always return 503.
    url = "https://data.fingrid.fi/api/datasets/193/data"

    responses.add(
        responses.GET,
        url,
        status=503,
        json={"message": "Service temporarily unavailable"},
    )

    client = FingridClient(api_key="test-api-key")

    # Act / Assert
    with pytest.raises(FingridAPIError, match="Failed to retrieve dataset"):
        client.get_dataset(
            dataset_id=193,
            start_time=datetime(2026, 10, 20, 10, 0),
            end_time=datetime(2026, 10, 20, 11, 0),
        )


@responses.activate
def test_get_dataset_401_doesnt_retry():
    # Arrange: return 401 Unauthorized.
    url = "https://data.fingrid.fi/api/datasets/193/data"

    responses.add(
        responses.GET,
        url,
        status=401,
        json={"message": "Unauthorized"},
    )

    client = FingridClient(api_key="test-api-key")

    # Act / Assert
    with pytest.raises(FingridAPIError, match="Failed to retrieve dataset"):
        client.get_dataset(
            dataset_id=193,
            start_time=datetime(2026, 10, 20, 10, 0),
            end_time=datetime(2026, 10, 20, 11, 0),
        )


@responses.activate
def test_get_dataset_invalid_json(client):
    url = "https://data.fingrid.fi/api/datasets/193/data"

    responses.add(
        responses.GET,
        url,
        body="Invalid JSON",
        status=200,
        content_type="application/json",
    )

    # Confirm the mock is registered.
    assert len(responses.mock._registry.registered) == 1

    with pytest.raises(FingridAPIError) as exc_info:
        client.get_dataset(
            dataset_id=193,
            start_time=datetime(2026, 10, 20, 10, 0),
            end_time=datetime(2026, 10, 20, 11, 0),
        )

    print("Exception:", exc_info.value)
    print("Mock calls:", len(responses.calls))
    print("Calls:", responses.calls)

    assert len(responses.calls) >= 1
    assert responses.calls[0].response.status_code == 200
    assert "Failed to decode JSON" in str(exc_info.value)

