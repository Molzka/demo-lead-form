import csv
import html
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text


def test_clean_start_ignores_environment(client_factory, tmp_path, monkeypatch):
    unwanted = tmp_path / "must-not-exist"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{unwanted / 'live.db'}")
    monkeypatch.setenv("LEADS_CSV_PATH", str(unwanted / "live.csv"))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "must-not-be-used")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "must-not-be-used")
    with client_factory() as client:
        assert client.get("/").status_code == 200
        assert "Заявок пока нет" in client.get(
            "/leads", auth=("test-admin", "test-password")
        ).text
    assert not unwanted.exists()


def test_submission_persists_in_db_and_csv_after_redirect(
    client, settings, admin_auth, valid_lead
):
    response = client.post("/lead", data=valid_lead, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/success"
    for _ in range(2):
        result = client.get(response.headers["location"])
        assert result.status_code == 200
        assert "Заявка принята" in result.text
        assert "передали уведомление" not in result.text
        assert "/leads" not in result.text
        assert valid_lead["name"] not in result.text
    leads = client.get("/leads?format=json", auth=admin_auth).json()
    assert len(leads) == 1
    assert leads[0]["name"] == "Иван"
    assert leads[0]["phone"] == "+79990000000"
    assert leads[0]["utm_campaign"] == "demo"
    assert leads[0]["comment"] == "Хочу узнать стоимость"
    assert "Иван" in client.get("/leads", auth=admin_auth).text
    with Path(settings.leads_csv_path).open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 1
    assert rows[0]["phone"] == "+79990000000"


@pytest.mark.parametrize("url", ["/leads", "/leads?format=json"])
@pytest.mark.parametrize("auth", [None, ("test-admin", "wrong"), ("wrong", "test-password")])
def test_private_leads_require_auth(client, valid_lead, url, auth):
    client.post("/lead", data=valid_lead)
    response = client.get(url, auth=auth)
    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic")
    assert "Иван" not in response.text
    assert "999" not in response.text


@pytest.mark.parametrize("field", ["admin_username", "admin_password"])
@pytest.mark.parametrize("url", ["/leads", "/leads?format=json"])
def test_missing_admin_config_fails_closed(client_factory, field, url):
    with client_factory(**{field: ""}) as client:
        assert client.get(url, auth=("test-admin", "test-password")).status_code == 503


@pytest.mark.parametrize("url", ["/leads", "/leads?format=json"])
def test_private_responses_are_not_cached(client, admin_auth, url):
    response = client.get(url, auth=admin_auth)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("field,value,error", [
    ("name", "   ", "Укажите имя"),
    ("phone", "", "Укажите телефон"),
    ("phone", "не телефон", "Телефон"),
    ("phone", "123", "Телефон"),
    ("phone", "1234567890123456", "Телефон"),
    ("phone", "+79990000000 ext 123", "Телефон"),
    ("phone", "++79990000000", "Телефон"),
    ("name", "я" * 121, "Имя"),
    ("phone", "7" * 61, "Телефон"),
    ("service", "я" * 161, "Услуга"),
    ("comment", "я" * 2001, "Комментарий"),
    ("utm_source", "x" * 121, "Источник"),
    ("utm_campaign", "x" * 161, "Кампания"),
])
def test_invalid_input_preserves_values_and_does_not_save(
    client, admin_auth, settings, valid_lead, field, value, error
):
    data = {**valid_lead, field: value}
    response = client.post("/lead", data=data)
    assert response.status_code == 422
    assert error in response.text
    assert 'role="alert"' in response.text
    for submitted in data.values():
        assert html.escape(submitted, quote=True) in response.text
    assert client.get("/leads?format=json", auth=admin_auth).json() == []
    assert not Path(settings.leads_csv_path).exists()


def test_maximum_lengths_are_accepted(client, admin_auth):
    data = dict(name="я" * 120, phone="+123456789012345", service="я" * 160,
                comment="я" * 2000, utm_source="x" * 120, utm_campaign="x" * 160)
    response = client.post("/lead", data=data, follow_redirects=False)
    assert response.status_code == 303
    lead = client.get("/leads?format=json", auth=admin_auth).json()[0]
    for key, value in data.items():
        assert lead[key] == value


def test_csv_failure_does_not_lose_accepted_lead(client_factory, tmp_path, admin_auth, valid_lead, caplog):
    # A directory cannot be opened as a CSV file; exercise a real filesystem failure.
    with client_factory(leads_csv_path=str(tmp_path)) as client:
        response = client.post("/lead", data=valid_lead, follow_redirects=False)
        assert response.status_code == 303
        assert len(client.get("/leads?format=json", auth=admin_auth).json()) == 1
    assert "CSV" in caplog.text


@pytest.mark.parametrize("failure", ["timeout", "http", "rejected", "invalid-json"])
def test_telegram_failure_still_accepts_lead(
    client_factory, admin_auth, valid_lead, monkeypatch, caplog, failure
):
    async def send(self, request, **kwargs):
        if failure == "timeout":
            raise httpx.ReadTimeout("secret-token", request=request)
        if failure == "http":
            return httpx.Response(502, request=request)
        if failure == "invalid-json":
            return httpx.Response(200, text="not JSON", request=request)
        return httpx.Response(200, json={"ok": False, "description": "secret-token"}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    with client_factory(telegram_bot_token="secret-token", telegram_chat_id="test-chat") as client:
        response = client.post("/lead", data=valid_lead, follow_redirects=False)
        assert response.status_code == 303
        assert "передали уведомление" not in client.get("/success").text
        assert len(client.get("/leads?format=json", auth=admin_auth).json()) == 1
    assert "Telegram" in caplog.text
    assert "secret-token" not in caplog.text
    assert "Иван" not in caplog.text


def test_telegram_receives_escaped_content(client_factory, valid_lead, monkeypatch):
    import json

    requests = []

    async def send(self, request, **kwargs):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    with client_factory(telegram_bot_token="test-token", telegram_chat_id="test-chat") as client:
        response = client.post("/lead", data={**valid_lead, "comment": "<script>&"})
        assert response.status_code == 200
    assert len(requests) == 1
    assert "&lt;script&gt;&amp;" in requests[0]["text"]
    assert requests[0]["chat_id"] == "test-chat"


def test_database_failure_is_honest_and_form_can_be_retried(client, settings, admin_auth, valid_lead):
    with client.app.state.session_factory() as db:
        db.execute(text("CREATE TRIGGER fail_insert BEFORE INSERT ON leads BEGIN SELECT RAISE(ABORT, 'test failure'); END"))
        db.commit()
    response = client.post("/lead", data=valid_lead)
    assert response.status_code == 503
    assert "Не удалось сохранить" in response.text
    assert valid_lead["name"] in response.text
    assert "test failure" not in response.text
    assert not Path(settings.leads_csv_path).exists()
    assert client.get("/leads?format=json", auth=admin_auth).json() == []
    with client.app.state.session_factory() as db:
        db.execute(text("DROP TRIGGER fail_insert"))
        db.commit()
    assert client.post("/lead", data=valid_lead, follow_redirects=False).status_code == 303


def test_invalid_tracking_value_can_be_corrected(client, valid_lead):
    from html.parser import HTMLParser

    inputs = []

    class Inputs(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == "input":
                inputs.append(dict(attrs))

    response = client.post("/lead", data={**valid_lead, "utm_source": "x" * 121})
    Inputs().feed(response.text)
    field = next(field for field in inputs if field.get("name") == "utm_source")
    assert field["type"] == "text"
    assert field["value"] == "x" * 121


def test_restart_preserves_leads_and_another_app_is_isolated(client_factory, tmp_path, valid_lead, admin_auth):
    with client_factory() as first:
        assert first.post("/lead", data=valid_lead, follow_redirects=False).status_code == 303
    with client_factory() as restarted:
        assert len(restarted.get("/leads?format=json", auth=admin_auth).json()) == 1
        with client_factory(database_url=f"sqlite:///{(tmp_path / 'other.db').as_posix()}") as other:
            assert other.get("/leads?format=json", auth=admin_auth).json() == []


def test_csv_failure_does_not_skip_telegram(client_factory, valid_lead, tmp_path, monkeypatch):
    sent = []

    async def send(self, request, **kwargs):
        sent.append(request.url.path)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    with client_factory(leads_csv_path=str(tmp_path), telegram_bot_token="test-token", telegram_chat_id="test-chat") as client:
        assert client.post("/lead", data=valid_lead, follow_redirects=False).status_code == 303
    assert sent == ["/bottest-token/sendMessage"]


def test_submitted_html_is_escaped_in_error_and_admin_views(client, valid_lead, admin_auth):
    payload = '<script>alert("test")</script>'
    response = client.post("/lead", data={**valid_lead, "name": payload, "phone": "bad"})
    assert response.status_code == 422
    assert payload not in response.text
    assert "&lt;script&gt;" in response.text
    assert client.post("/lead", data={**valid_lead, "comment": payload}, follow_redirects=False).status_code == 303
    result = client.get("/leads", auth=admin_auth)
    assert payload not in result.text
    assert "&lt;script&gt;" in result.text
