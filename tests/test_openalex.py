from openalex import Works, Authors, Venues, Institutions, Concepts
import requests

def test_works_params():

    assert len(Works(params={"filter":{'publication_year':'2020'}}).get()) == 25

    assert Works().params == {}


def test_works():

    assert len(Works().filter(publication_year=2020).get()) == 25

    assert Works().params == {}


def test_W4238809453_works():

    assert isinstance(Works("W4238809453").get(), dict)


def test_random_works():

    assert isinstance(Works().get_random(), dict)


def test_works_multifilter():

    print("test", Works().params)

    r = requests.get("https://api.openalex.org/works?filter=publication_year:2020,is_oa:true").json()

    a, ra = Works().filter(publication_year=2020, is_oa=True).get(return_meta=True)
    b, rb = Works().filter(publication_year=2020).filter(is_oa=True).get(return_meta=True)
    c, rc = Works().filter(publication_year=2020, open_access={"is_oa":True}).get(return_meta=True)

    assert r["meta"]["count"] == a["count"]
    assert r["meta"]["count"] == b["count"]
    assert r["meta"]["count"] == c["count"]


def test_works_multifilter_meta():

    a, ra = Works().filter(publication_year=2020, is_oa=True).get(return_meta=True)
    b, rb = Works().filter(publication_year=2020).filter(is_oa=True).get(return_meta=True)

    assert a["count"] == b["count"]
