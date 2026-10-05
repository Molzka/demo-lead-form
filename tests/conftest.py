from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture(autouse=True)
def block_external_notifications(monkeypatch):
    async def blocked(*args, **kwargs):
        pytest.fail("Tests must never send real Telegram requests")

    monkeypatch.setattr(httpx.AsyncClient, "send", blocked)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        database_url=f"sqlite:///{(tmp_path / 'db' / 'leads.db').as_posix()}",
        leads_csv_path=str(tmp_path / "export" / "leads.csv"),
        admin_username="test-admin",
        admin_password="test-password",
    )


@pytest.fixture
def client_factory(settings):
    def factory(**overrides):
        return TestClient(create_app(replace(settings, **overrides)))

    return factory


@pytest.fixture
def client(client_factory):
    with client_factory() as client:
        yield client


@pytest.fixture
def admin_auth(settings):
    return settings.admin_username, settings.admin_password


@pytest.fixture
def valid_lead():
    return {
        "name": "Иван",
        "phone": "+7 (999) 000-00-00",
        "service": "Консультация",
        "comment": "Хочу узнать стоимость",
        "utm_source": "site",
        "utm_campaign": "demo",
    }
