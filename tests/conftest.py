"""Pytest configuration and fixtures for the FastAPI tests."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a TestClient for FastAPI endpoints.
    
    Returns:
        TestClient: A test client for making requests to the FastAPI app.
    """
    return TestClient(app)
