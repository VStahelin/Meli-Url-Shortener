import pytest
from fastapi import status
from httpx import InvalidURL
import app.generator.service as service


def test_get_url_shortened_url_redirects_success(make_client, monkeypatch, db_session):
    client = make_client()
    token = "ABC123"
    expected_destination = "https://original.example/"

    async def fake_retrieve(token_arg, db_arg):
        assert token_arg == token
        assert db_arg is db_session
        return expected_destination

    monkeypatch.setattr("app.generator.routes.url.retrieve_url", fake_retrieve)

    response = client.get(f"/{token}")

    assert response.status_code == status.HTTP_302_FOUND
    assert response.headers["location"] == expected_destination


def test_get_url_with_invalid_token_returns_400_bad_request(make_client, monkeypatch):
    client = make_client()
    invalid_token = "BAD-TOKEN"

    monkeypatch.setattr("app.generator.routes.url.is_safe_url_path", lambda path: False)

    response = client.get(f"/{invalid_token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Bad token"}


def test_get_url_when_token_is_registered_will_return_404_not_found(
    make_client, monkeypatch, db_session
):
    client = make_client()
    token = "XXXYYY"

    monkeypatch.setattr("app.generator.routes.url.is_safe_url_path", lambda path: True)

    async def fake_retrieve(token_arg, db_arg):
        return None

    monkeypatch.setattr("app.generator.routes.url.retrieve_url", fake_retrieve)

    response = client.get(f"/{token}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "URL not found"}


def test_generate_shortened_url_success(make_client, monkeypatch, db_session):
    client = make_client()
    original = "https://google.com/"
    expected_short = "http://short/GOOGL1"

    monkeypatch.setattr("app.generator.routes.url.validate_url_scheme", lambda url: url)

    async def fake_generate(url_arg, db_arg):
        assert url_arg == original
        assert db_arg is db_session
        return expected_short

    monkeypatch.setattr("app.generator.routes.url.generate_url_token", fake_generate)

    payload = {"url": original}

    response = client.post("/", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "success": True,
        "data": {"url": expected_short},
        "message": None,
    }


@pytest.mark.parametrize(
    "bad",
    [
        "javascript:evil()",
        "ftp://malicious.com",
        "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        "vbscript:alert('XSS')",
        "http://example.com/<script>alert(1)</script>",
    ],
)
def test_generate_shortened_url_with_bad_scheme_returns_400_bad_request(
    make_client, monkeypatch, bad
):
    client = make_client()
    monkeypatch.setattr(
        "app.generator.routes.url.validate_url_scheme",
        lambda url: (_ for _ in ()).throw(ValueError("bad")),
    )

    response = client.post("/", json={"url": bad})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "success": False,
        "message": "Invalid URL",
        "data": None,
    }


def test_delete_shortened_url_success(make_client, monkeypatch, db_session):
    client = make_client()
    token = "DEL123"
    monkeypatch.setattr("app.generator.routes.url.is_safe_url_path", lambda p: True)
    called = []

    async def fake_delete(tok, db):
        assert tok == token
        assert db is db_session
        called.append(True)

    monkeypatch.setattr("app.generator.routes.url.delete_url_token", fake_delete)

    response = client.delete(f"/{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "success": True,
        "data": {"message": "URL deleted successfully"},
        "message": None,
    }
    assert called == [True]


@pytest.mark.parametrize(
    "malicious_token",
    [
        "1 OR 1=1",
        "'; DROP TABLE urls;--",
        "%27%20OR%20%271%27%3D%271",
        "abc\\def",
        "\nabc",
        "\x00abc",
    ],
)
def test_delete_shortened_url_with_malicious_token_returns_400_bad_request(
    make_client, monkeypatch, malicious_token
):
    from app.generator.routes import url as route_module

    client = make_client()

    monkeypatch.setattr(route_module, "is_safe_url_path", lambda path: False)

    try:
        response = client.delete(f"/{malicious_token}")
    except (InvalidURL, ValueError):
        return

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"data": None, "message": "Bad token", "success": False}


@pytest.mark.asyncio
async def test_delete_url_token_raises_shorten_url_deletion_failed(
    make_client, make_db_session, monkeypatch
):
    client = make_client()
    token = "FAILME"

    from app.generator.routes import url as route_module

    async def broken_delete(tok, db):
        raise service.ShortenUrlDeletionFailed("DB failure")

    monkeypatch.setattr(route_module, "delete_url_token", broken_delete)

    response = client.delete(f"/{token}")

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "data": None,
        "message": "Could not delete the Token",
    }
