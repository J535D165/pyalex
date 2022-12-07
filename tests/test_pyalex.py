import json
from pathlib import Path

import pytest
import requests

import pyalex
from pyalex import Authors
from pyalex import Concepts
from pyalex import Institutions
from pyalex import Venues
from pyalex import Work
from pyalex import Works


def test_config():

    pyalex.config.email = "myemail@example.com"

    assert pyalex.config.email == "myemail@example.com"


def test_meta_entities():

    _, m = Authors().get(return_meta=True)
    assert "count" in m
    _, m = Concepts().get(return_meta=True)
    assert "count" in m
    _, m = Institutions().get(return_meta=True)
    assert "count" in m
    _, m = Venues().get(return_meta=True)
    assert "count" in m
    _, m = Works().get(return_meta=True)
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


def test_random_works():

    assert isinstance(Works().random(), dict)


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


def test_works_multifilter_meta():

    _, m1 = Works().filter(publication_year=2020, is_oa=True).get(return_meta=True)
    _, m2 = (
        Works().filter(publication_year=2020).filter(is_oa=True).get(return_meta=True)
    )

    assert m1["count"] == m2["count"]


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


def test_cursor_paging():

    # example query
    query = Authors().search_filter(display_name="einstein")

    # store the results
    results = []

    next_cursor = "*"

    # loop till next_cursor is None
    while next_cursor is not None:

        print(next_cursor)

        # get the results
        r, m = query.get(return_meta=True, per_page=200, cursor=next_cursor)

        # results
        results.extend(r)

        # set the next cursor
        next_cursor = m["next_cursor"]

    assert len(results) > 200


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

    # /works?filter=institutions.is_global_south:true,type:dataset&group-by=institutions.country_code
    # /works?filter=institutions.is_global_south:true,type:dataset&group-by=institutions.country_code&sort=count:desc

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
