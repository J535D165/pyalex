import requests

from openalex import Authors
from openalex import Concepts
from openalex import Institutions
from openalex import Venues
from openalex import Works


def test_meta_entities():

    m, r = Authors().get(return_meta=True)
    assert "count" in m
    m, r = Concepts().get(return_meta=True)
    assert "count" in m
    m, r = Institutions().get(return_meta=True)
    assert "count" in m
    m, r = Venues().get(return_meta=True)
    assert "count" in m
    m, r = Works().get(return_meta=True)
    assert "count" in m


def test_works_params():

    assert len(Works(params={"filter": {"publication_year": "2020"}}).get()) == 25

    assert Works().params == {}


def test_works():

    assert len(Works().filter(publication_year=2020).get()) == 25

    assert Works().params == {}


def test_per_page():

    assert len(Works().filter(publication_year=2020).get(per_page=200)) == 200


def test_W4238809453_works():

    assert isinstance(Works("W4238809453").get(), dict)


def test_W4238809453_works_abstract():

    assert "abstract" in Works("W4238809453").get()


def test_W4238809453_works_no_abstract():

    assert "abstract" not in Works("W4238809453", abstract=False).get()


def test_random_works():

    assert isinstance(Works().get_random(), dict)


def test_works_multifilter():

    r = requests.get(
        "https://api.openalex.org/works?filter=publication_year:2020,is_oa:true"
    ).json()

    a, ra = Works().filter(publication_year=2020, is_oa=True).get(return_meta=True)
    b, rb = (
        Works().filter(publication_year=2020).filter(is_oa=True).get(return_meta=True)
    )
    c, rc = (
        Works()
        .filter(publication_year=2020, open_access={"is_oa": True})
        .get(return_meta=True)
    )

    assert r["meta"]["count"] == a["count"]
    assert r["meta"]["count"] == b["count"]
    assert r["meta"]["count"] == c["count"]


def test_works_multifilter_meta():

    a, ra = Works().filter(publication_year=2020, is_oa=True).get(return_meta=True)
    b, rb = (
        Works().filter(publication_year=2020).filter(is_oa=True).get(return_meta=True)
    )

    assert a["count"] == b["count"]


def test_data_publications():

    m, r = (
        Works()
        .filter(authorships={"institutions": {"ror": "04pp8hn57"}})
        .filter(type="dataset")
        .group_by("publication_year")
        .get(return_meta=True)
    )

    assert len(r) > 20


def test_search():

    w = (
        Works()
        .search(
            "An open source machine learning framework for efficient and transparent systematic reviews"
        )
        .get()
    )

    assert w[0]["doi"] == "https://doi.org/10.1038/s42256-020-00287-7"

def test_search_filter():

    r = requests.get(
        "https://api.openalex.org/authors?filter=display_name.search:einstein"
    ).json()

    a, ra = Authors().search_filter(display_name="einstein").get(return_meta=True)

    assert r["meta"]["count"] == a["count"]



