import os
from functools import wraps
from unittest.mock import MagicMock

import pytest

import pyalex
from pyalex import Works
from pyalex.api import _extract_ratelimit

pyalex.config.max_retries = 10


def requires_api_key(reason="OpenAlex requires authentication for this operation"):
    """Decorator for API Key requirement.

    Decorator that skips test if OPENALEX_API_KEY is not set, and
    sets it for the test.
    """

    def decorator(func):
        @pytest.mark.skipif(
            not os.environ.get("OPENALEX_API_KEY"),
            reason=reason,
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            api_key = os.environ.get("OPENALEX_API_KEY")
            original_api_key = pyalex.config.api_key
            try:
                pyalex.config.api_key = api_key
                return func(*args, **kwargs)
            finally:
                pyalex.config.api_key = original_api_key

        return wrapper

    return decorator


def test_extract_ratelimit():
    """_extract_ratelimit parses headers to correct types."""
    res = MagicMock()
    res.headers = {
        "X-RateLimit-Credits-Used": "1",
        "X-RateLimit-Limit": "10000",
        "X-RateLimit-Remaining": "9999",
        "X-RateLimit-Reset": "3600",
        "X-RateLimit-Cost-USD": "0.0001",
        "X-RateLimit-Limit-USD": "1.0",
        "X-RateLimit-Remaining-USD": "0.9999",
    }

    rl = _extract_ratelimit(res)

    # int fields
    assert rl["credits_used"] == 1
    assert isinstance(rl["credits_used"], int)
    assert rl["credits_limit"] == 10000
    assert rl["credits_remaining"] == 9999
    assert rl["reset_seconds"] == 3600

    # float fields
    assert rl["cost_usd"] == pytest.approx(0.0001)
    assert isinstance(rl["cost_usd"], float)
    assert rl["limit_usd"] == 1.0
    assert rl["remaining_usd"] == pytest.approx(0.9999)

    # absent headers are omitted
    assert "credits_required" not in rl
    assert "onetime_remaining" not in rl
    assert "cost_required_usd" not in rl
    assert "prepaid_remaining_usd" not in rl


def test_extract_ratelimit_empty():
    """_extract_ratelimit returns empty dict when no headers present."""
    res = MagicMock()
    res.headers = {}
    assert _extract_ratelimit(res) == {}


@requires_api_key(reason="OpenAlex requires authentication for ratelimit headers")
def test_ratelimit_in_list_meta():
    """List results include ratelimit in meta."""
    r = Works().filter(publication_year=2020).get(per_page=1)

    assert "ratelimit" in r.meta
    rl = r.meta["ratelimit"]
    assert "credits_used" in rl
    assert "credits_remaining" in rl
    assert isinstance(rl["credits_used"], int)
    assert isinstance(rl["credits_remaining"], int)


@requires_api_key(reason="OpenAlex requires authentication for ratelimit headers")
def test_ratelimit_in_singleton_meta():
    """Singleton results include ratelimit in meta."""
    w = Works()["W2741809807"]

    assert hasattr(w, "meta")
    assert "ratelimit" in w.meta
    rl = w.meta["ratelimit"]
    assert "credits_remaining" in rl
    # Native OpenAlex ID lookup is free
    assert rl["credits_used"] == 0
