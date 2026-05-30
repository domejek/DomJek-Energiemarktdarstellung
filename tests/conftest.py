import pytest
import numpy as np
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(autouse=True)
def seed_random():
    np.random.seed(42)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def date_range():
    end = datetime.now()
    start = end - timedelta(days=7)
    return {
        "start": start.strftime("%Y-%m-%d"),
        "end": end.strftime("%Y-%m-%d"),
    }
