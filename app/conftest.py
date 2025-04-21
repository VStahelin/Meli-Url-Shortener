import pytest
import fakeredis
import app.generator.service as _service
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_db


class FakeSession:
    def __init__(self, commit_side_effects=None, return_value=None):
        self._commit_side_effects = commit_side_effects or [None]
        self._return_value = return_value
        self.added = []
        self.exec_args = []
        self.commits = 0
        self.rollbacks = 0

    async def commit(self):
        effect = self._commit_side_effects.pop(0)
        self.commits += 1
        if effect:
            raise effect

    async def rollback(self):
        self.rollbacks += 1

    def add(self, entry):
        self.added.append(entry)

    async def execute(self, stmt):
        self.exec_args.append(stmt)

        class Result:
            def __init__(self, val):
                self._val = val

            def scalar_one_or_none(self):
                return self._val

        return Result(self._return_value)


@pytest.fixture
def make_redis_client(monkeypatch):
    def _make():
        fake = fakeredis.FakeRedis(decode_responses=True)
        monkeypatch.setattr(_service, "redis_client", fake)
        return fake

    return _make


@pytest.fixture
def make_db_session():
    def _make(commit_side_effects=None, return_value=None):
        return FakeSession(commit_side_effects, return_value)

    return _make


@pytest.fixture
def db_session(make_db_session):
    return make_db_session()


@pytest.fixture(autouse=True)
def override_get_db(monkeypatch, db_session):
    """
    Override the get_db dependency to use a fake session.
    """

    async def _fake_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _fake_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def patch_service_settings(monkeypatch):
    monkeypatch.setattr(_service, "BASE_URL", "http://short")
    monkeypatch.setattr(_service, "CACHE_DEFAULT_TIMEOUT", 60)


@pytest.fixture
def make_client():
    def _make(follow_redirects: bool = False):
        tc = TestClient(app)
        if not follow_redirects:
            original_get = tc.get

            def get_no_redirect(path: str, **kwargs):
                kwargs.setdefault("follow_redirects", False)
                return original_get(path, **kwargs)

            tc.get = get_no_redirect
        return tc

    return _make
