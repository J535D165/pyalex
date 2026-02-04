import os
from functools import wraps

import pytest

import pyalex
from pyalex import Authors
from pyalex.api import Paginator

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


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
def test_cursor_no_filter():
    assert len(list(pyalex.Works().paginate(per_page=200, n_max=1000))) == 5


@requires_api_key(reason="OpenAlex requires authentication for search_filter queries")
def test_cursor():
    query = Authors().search_filter(display_name="einstein")

    # store the results
    results = []

    next_cursor = "*"

    # loop till next_cursor is None
    while next_cursor is not None:
        # get the results
        r = query.get(per_page=200, cursor=next_cursor)

        # results
        results.extend(r)

        # set the next cursor
        next_cursor = r.meta["next_cursor"]

    assert len(results) > 200


@requires_api_key(reason="OpenAlex requires authentication for search_filter queries")
def test_page():
    query = Authors().search_filter(display_name="einstein")

    # set the page
    page = 1

    # store the results
    results = []

    # loop till page is None
    while page is not None:
        # get the results
        r = query.get(per_page=200, page=page)

        # results
        results.extend(r)
        page = None if len(r) == 0 else r.meta["page"] + 1

    assert len(results) > 200


@requires_api_key(reason="OpenAlex requires authentication for search_filter queries")
def test_paginate_counts():
    r = Authors().search_filter(display_name="einstein").get()

    p_default = Authors().search_filter(display_name="einstein").paginate(per_page=200)
    n_p_default = sum(len(page) for page in p_default)

    p_cursor = (
        Authors()
        .search_filter(display_name="einstein")
        .paginate(method="cursor", per_page=200)
    )
    n_p_cursor = sum(len(page) for page in p_cursor)

    p_page = (
        Authors()
        .search_filter(display_name="einstein")
        .paginate(method="page", per_page=200)
    )
    n_p_page = sum(len(page) for page in p_page)

    assert r.meta["count"] == n_p_page >= n_p_default == n_p_cursor


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
def test_paginate_per_page():
    assert all(len(page) <= 10 for page in Authors().paginate(per_page=10, n_max=50))


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
def test_paginate_per_page_200():
    assert all(len(page) == 200 for page in Authors().paginate(per_page=200, n_max=400))


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
def test_paginate_per_page_none():
    assert all(len(page) == 25 for page in Authors().paginate(n_max=500))


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
def test_paginate_per_page_1000():
    with pytest.raises(ValueError):
        assert next(Authors().paginate(per_page=1000))


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
def test_paginate_per_page_str():
    with pytest.raises(ValueError):
        assert next(Authors().paginate(per_page="100"))


@requires_api_key(reason="OpenAlex requires authentication for search_filter queries")
def test_paginate_instance():
    p_default = Authors().search_filter(display_name="einstein").paginate(per_page=200)
    assert isinstance(p_default, Paginator)
    assert p_default.method == "cursor"


@requires_api_key(reason="OpenAlex requires authentication for search_filter queries")
def test_paginate_cursor_n_max():
    p = (
        Authors()
        .search_filter(display_name="einstein")
        .paginate(per_page=200, n_max=400)
    )

    assert sum(len(page) for page in p) == 400


@requires_api_key(reason="OpenAlex requires authentication for search_filter queries")
def test_cursor_paging_n_max_none():
    p = (
        Authors()
        .search_filter(display_name="einstein")
        .paginate(per_page=200, n_max=None)
    )

    sum(len(page) for page in p)


@requires_api_key(reason="OpenAlex requires authentication for sample queries")
def test_paging_with_sample():
    with pytest.raises(ValueError):
        Authors().sample(1).paginate(method="cursor")


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
def test_paging_next():
    next(Authors().paginate())
