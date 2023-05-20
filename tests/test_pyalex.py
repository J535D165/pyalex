import json
from pathlib import Path

import pytest
import requests
from requests import HTTPError

import pyalex
from pyalex import Authors
from pyalex import Concepts
from pyalex import Funders
from pyalex import Institutions
from pyalex import Publishers
from pyalex import Sources
from pyalex import Work
from pyalex import Works
from pyalex.api import QueryError


def test_config():
    pyalex.config.email = "pyalex_github_unittests@example.com"

    assert pyalex.config.email == "pyalex_github_unittests@example.com"
    assert pyalex.config.api_key is None
    pyalex.config.api_key = "my_api_key"
    assert pyalex.config.api_key == "my_api_key"
    pyalex.config.api_key = None


def test_meta_entities():

    _, m = Authors().get(return_meta=True)
    assert "count" in m
    _, m = Concepts().get(return_meta=True)
    assert "count" in m
    _, m = Institutions().get(return_meta=True)
    assert "count" in m
    _, m = Sources().get(return_meta=True)
    assert "count" in m
    _, m = Works().get(return_meta=True)
    assert "count" in m
    _, m = Funders().get(return_meta=True)
    assert "count" in m

def test_works_params():

    assert len(Works(params={"filter": {"publication_year": "2020"}}).get()) == 25


def test_works():

    assert len(Works().filter(publication_year=2020).get()) == 25


def test_per_page():

    assert len(Works().filter(publication_year=2020).get(per_page=200)) == 200


def test_W4238809453_works():

    assert isinstance(Works()["W4238809453"], Work)
    assert Works()["W4238809453"]["doi"] == "https://doi.org/10.1001/jama.264.8.944b"


def test_W4238809453_works_abstract():

    assert Works()["W4238809453"]["abstract"] is None


def test_W4238809453_works_no_abstract():

    assert "abstract" not in Works()["W4238809453"]


def test_W3128349626_works_abstract():

    w = Works()["W3128349626"]

    assert w["abstract"] is not None
    assert "abstract_inverted_index" in w


def test_W3128349626_works_no_abstract():

    w = Works()["W3128349626"]

    assert w["abstract_inverted_index"] is not None
    assert "abstract" not in w


def test_work_error():

    with pytest.raises(HTTPError):
        Works()["NotAWorkID"]


def test_random_works():

    assert isinstance(Works().random(), dict)


def test_multi_works():

    # the work to extract the referenced works of
    w = Works()["W2741809807"]

    assert len(Works()[w["referenced_works"]]) == 25


def test_works_multifilter():

    r = requests.get(
        "https://api.openalex.org/works?filter=publication_year:2020,is_oa:true"
    ).json()

    _, w1 = Works().filter(publication_year=2020, is_oa=True).get(return_meta=True)
    _, w2 = (
        Works().filter(publication_year=2020).filter(is_oa=True).get(return_meta=True)
    )

    # openalex bug
    # c, rc = (
    #     Works()
    #     .filter(publication_year=2020, open_access={"is_oa": True})
    #     .get(return_meta=True)
    # )

    assert r["meta"]["count"] == w1["count"]
    assert r["meta"]["count"] == w2["count"]
    # assert r["meta"]["count"] == c["count"]


def test_works_url():

    url = "https://api.openalex.org/works?filter=publication_year:2020,is_oa:true"

    assert url == Works().filter(publication_year=2020, is_oa=True).url
    assert url == Works().filter(publication_year=2020).filter(is_oa=True).url

    assert Works().url == "https://api.openalex.org/works"


def test_works_multifilter_meta():

    _, m1 = Works().filter(publication_year=2020, is_oa=True).get(return_meta=True)
    _, m2 = (
        Works().filter(publication_year=2020).filter(is_oa=True).get(return_meta=True)
    )

    assert m1["count"] == m2["count"]


def test_query_error():

    with pytest.raises(QueryError):
        Works().filter(publication_year_error=2020).get()


def test_data_publications():

    w, _ = (
        Works()
        .filter(authorships={"institutions": {"ror": "04pp8hn57"}})
        .filter(type="dataset")
        .group_by("publication_year")
        .get(return_meta=True)
    )

    assert len(w) > 20


def test_search():

    w = (
        Works()
        .search(
            "An open source machine learning framework for efficient"
            " and transparent systematic reviews"
        )
        .get()
    )

    assert w[0]["doi"] == "https://doi.org/10.1038/s42256-020-00287-7"


def test_search_filter():

    r = requests.get(
        "https://api.openalex.org/authors?filter=display_name.search:einstein"
    ).json()

    a, m = Authors().search_filter(display_name="einstein").get(return_meta=True)

    assert r["meta"]["count"] == m["count"]


def test_cursor_by_hand():

    # example query
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


def test_basic_paging():

    # example query
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


def test_cursor_paging():

    # example query
    pager = Authors().search_filter(display_name="einstein").paginate(per_page=200)

    for page in pager:

        assert len(page) >= 1 and len(page) <= 200


def test_cursor_paging_n_max():

    # example query
    pager = (
        Authors()
        .search_filter(display_name="einstein")
        .paginate(per_page=200, n_max=400)
    )

    n = 0
    for page in pager:

        n = n + len(page)

    assert n == 400


def test_cursor_paging_n_max_none():

    # example query
    pager = (
        Authors()
        .search_filter(display_name="einstein")
        .paginate(per_page=200, n_max=None)
    )

    n = 0
    for page in pager:

        n = n + len(page)


def test_referenced_works():

    # the work to extract the referenced works of
    w = Works()["W2741809807"]

    _, m = (
        Works()
        .filter(openalex_id="|".join(w["referenced_works"]))
        .get(return_meta=True)
    )

    assert m["count"] == len(w["referenced_works"])


@pytest.mark.xfail()
def test_code_examples():

    # /works?filter=institutions.is_global_south:true,type:dataset&group-by=institutions.country_code  # noqa
    # /works?filter=institutions.is_global_south:true,type:dataset&group-by=institutions.country_code&sort=count:desc  # noqa

    r_original = requests.get(
        "https://api.openalex.org/works?filter=institutions.is_global_south:true"
        + ",type:dataset&group-by=institutions.country_code"
    ).json()

    # the work to extract the referenced works of
    r, meta = (
        Works()
        .filter(institutions={"is_global_south": True})
        .filter(type="dataset")
        .group_by("institutions.country_code")
        .sort(count="desc")
        .get(return_meta=True)
    )

    assert r_original["group_by"][0]["count"] == r[0]["count"]


def test_serializable(tmpdir):

    with open(Path(tmpdir, "test.json"), "w") as f:
        json.dump(Works()["W4238809453"], f)

    with open(Path(tmpdir, "test.json")) as f:
        assert "W4238809453" in json.load(f)["id"]


def test_ngrams_without_metadata():

    r = Works()["W2023271753"].ngrams(return_meta=False)

    assert len(r) == 1068


def test_ngrams_with_metadata():

    r, meta = Works()["W2023271753"].ngrams(return_meta=True)

    assert meta["count"] == 1068


def test_random_publishers():

    assert isinstance(Publishers().random(), dict)


def test_and_operator():

    # https://github.com/J535D165/pyalex/issues/11
    url = "https://api.openalex.org/works?filter=institutions.country_code:tw,institutions.country_code:hk,institutions.country_code:us,publication_year:2022"  # noqa

    assert (
        url
        == Works()
        .filter(
            institutions={"country_code": ["tw", "hk", "us"]}, publication_year=2022
        )
        .url
    )
    assert (
        url
        == Works()
        .filter(institutions={"country_code": "tw"})
        .filter(institutions={"country_code": "hk"})
        .filter(institutions={"country_code": "us"})
        .filter(publication_year=2022)
        .url
    )
    assert (
        url
        == Works()
        .filter(institutions={"country_code": ["tw", "hk"]})
        .filter(institutions={"country_code": "us"})
        .filter(publication_year=2022)
        .url
    )


def test_sample():

    url = "https://api.openalex.org/works?filter=publication_year:2020,is_oa:true&sample=50"
    assert url == Works().filter(publication_year=2020, is_oa=True).sample(50).url


def test_sample_seed():

    url = "https://api.openalex.org/works?filter=publication_year:2020,is_oa:true&sample=50&seed=535"  # noqa
    assert (
        url
        == Works().filter(publication_year=2020, is_oa=True).sample(50, seed=535).url
    )


def test_subset():

    url = "https://api.openalex.org/works?select=id,doi,display_name"
    assert url == Works().select(["id", "doi", "display_name"]).url
