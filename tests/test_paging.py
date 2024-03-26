import pyalex
from pyalex import Authors
from pyalex.api import Paginator

pyalex.config.max_retries = 10


def test_cursor():
    query = Authors().search_filter(display_name="einstein")

    # store the results
    results = []

    next_cursor = "*"

    # loop till next_cursor is None
    while next_cursor is not None:
        # get the results
        r, m = query.get(return_meta=True, per_page=200, cursor=next_cursor)

        # results
        results.extend(r)

        # set the next cursor
        next_cursor = m["next_cursor"]

    assert len(results) > 200


def test_page():
    query = Authors().search_filter(display_name="einstein")

    # set the page
    page = 1

    # store the results
    results = []

    # loop till page is None
    while page is not None:
        # get the results
        r, m = query.get(return_meta=True, per_page=200, page=page)

        # results
        results.extend(r)
        page = None if len(r) == 0 else m["page"] + 1

    assert len(results) > 200


def test_paginate_counts():
    _, m = Authors().search_filter(display_name="einstein").get(return_meta=True)

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

    assert m["count"] == n_p_page >= n_p_default == n_p_cursor


def test_paginate_instance():
    p_default = Authors().search_filter(display_name="einstein").paginate(per_page=200)
    assert isinstance(p_default, Paginator)
    assert p_default.method == "cursor"


def test_paginate_cursor_n_max():
    p = (
        Authors()
        .search_filter(display_name="einstein")
        .paginate(per_page=200, n_max=400)
    )

    assert sum(len(page) for page in p) == 400


def test_cursor_paging_n_max_none():
    p = (
        Authors()
        .search_filter(display_name="einstein")
        .paginate(per_page=200, n_max=None)
    )

    sum(len(page) for page in p)
