import httpx
import pytest
import time

BASE_URL = "http://127.0.0.1:8000"
timeout_duration = 300


def test_existing_package():
    package_name = "react-hot-toast"
    with httpx.Client(timeout=timeout_duration) as client:
        response = client.get(f"{BASE_URL}/{package_name}")
    assert response.status_code == 200
    assert "data" in response.json()


def test_non_existing_package():
    package_name = "non-existing-package-123"
    response = httpx.get(f"{BASE_URL}/{package_name}")
    assert response.status_code == 404
    assert "error" in response.json()


def test_invalid_request():
    package_name = ""
    response = httpx.get(f"{BASE_URL}/{package_name}")
    assert response.status_code == 404


def test_caching():
    package_name = "webpack"  # A package with lots of dependencies

    with httpx.Client(timeout=timeout_duration) as client:
        # Measure response time for the first request
        start_time = time.time()
        response1 = client.get(f"{BASE_URL}/{package_name}")
        first_request_duration = time.time() - start_time
        assert response1.status_code == 200

        # Measure response time for the second request
        start_time = time.time()
        response2 = client.get(f"{BASE_URL}/{package_name}")
        second_request_duration = time.time() - start_time
        assert response2.status_code == 200

    # The second request should be faster due to caching
    assert second_request_duration < 3
    assert second_request_duration < first_request_duration


if __name__ == "__main__":
    pytest.main()
