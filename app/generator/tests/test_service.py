import pytest
from sqlalchemy.exc import IntegrityError
import app.generator.service as service
from app.generator.service import (
    generate_url_token,
    retrieve_url,
    delete_url_token,
)


@pytest.mark.asyncio
async def test_generate_url_token_first_try_success(
    make_redis_client, make_db_session, monkeypatch
):
    cache_client = make_redis_client()
    db_client = make_db_session()

    original_url = "http://orig.com"
    monkeypatch.setattr(service.secrets, "choice", lambda _: "a")

    expected_token = "AAAAAA"
    expected_short_url = f"http://short/{expected_token}"

    short_url = await generate_url_token(original_url, db_client)

    assert short_url == expected_short_url
    assert len(db_client.added) == 1
    assert db_client.added[0].id == expected_token
    assert db_client.added[0].url == original_url
    assert db_client.commits == 1
    assert db_client.rollbacks == 0
    assert cache_client.get(expected_token) == original_url


@pytest.mark.asyncio
async def test_generate_url_token_retries_on_integrity_error(
    make_redis_client, make_db_session, monkeypatch
):
    cache_client = make_redis_client()
    db_client = make_db_session()

    seq = ["a"] * 6 + ["b"] * 6
    monkeypatch.setattr(service.secrets, "choice", lambda _: seq.pop(0))

    db_client._commit_side_effects = [IntegrityError(None, None, None), None]
    original_url = "http://orig2.com"

    expected_token = "BBBBBB"
    expected_short_url = f"http://short/{expected_token}"

    short_url = await generate_url_token(original_url, db_client)

    tokens_added = [entry.id for entry in db_client.added]
    assert short_url == expected_short_url
    assert tokens_added == ["AAAAAA", expected_token]
    assert db_client.commits == 2
    assert db_client.rollbacks == 1
    assert cache_client.get(expected_token) == original_url


@pytest.mark.asyncio
async def test_generate_url_token_raises_integrity_error_when_max_retries_exceeded(
    make_db_session, monkeypatch
):
    db_client = make_db_session()

    monkeypatch.setattr(service.secrets, "choice", lambda _: "x")

    db_client._commit_side_effects = [IntegrityError(None, None, None)] * 6
    original_url = "http://orig-max.com"

    expected_error = "Max retries exceeded while generating unique token."
    expected_commits = 5
    expected_rollbacks = 5

    with pytest.raises(Exception) as exc_info:
        await generate_url_token(original_url, db_client)

    assert expected_error in str(exc_info.value)
    assert db_client.commits == expected_commits
    assert db_client.rollbacks == expected_rollbacks


@pytest.mark.asyncio
async def test_retrieve_url_uses_cached_value_successfully(
    make_redis_client, make_db_session
):
    cache_client = make_redis_client()
    db_client = make_db_session()

    token = "TKN123"
    cached_url = "http://cache-url"
    cache_client.set(token, cached_url, ex=60)

    get_calls = []
    original_get = cache_client.get
    cache_client.get = lambda key: (get_calls.append(key), original_get(key))[1]

    expected_url = cached_url
    expected_get_calls = [token]
    expected_db_calls = 0

    result_url = await retrieve_url(token, db_client)

    assert result_url == expected_url
    assert get_calls == expected_get_calls
    assert len(db_client.exec_args) == expected_db_calls


@pytest.mark.asyncio
async def test_retrieve_url_when_token_not_in_cache_hits_db_and_fills_cache_successfully(
    make_redis_client, make_db_session
):
    cache_client = make_redis_client()
    db_client = make_db_session()

    token = "ABC123"
    db_url = "http://db-url"
    db_client._return_value = db_url

    expected_url = db_url

    result_url = await retrieve_url(token, db_client)

    assert result_url == expected_url
    assert len(db_client.exec_args) == 1
    assert cache_client.get(token) == expected_url


@pytest.mark.asyncio
async def test_retrieve_url_when_token_not_in_cache_and_db_returns_none(
    make_redis_client, make_db_session
):
    cache_client = make_redis_client()
    db_client = make_db_session()

    token = "XXXYYY"
    db_client._return_value = None

    expected = None

    result = await retrieve_url(token, db_client)

    assert result is expected
    assert cache_client.get(token) is None


@pytest.mark.asyncio
async def test_delete_url_token(make_redis_client, make_db_session):
    cache_client = make_redis_client()
    db_client = make_db_session()

    token = "XXXYYY"
    cache_client.set(token, "URL", ex=60)

    expected_execute_calls = 1

    await delete_url_token(token, db_client)

    assert cache_client.get(token) is None
    assert len(db_client.exec_args) == expected_execute_calls
    assert db_client.commits == 1
