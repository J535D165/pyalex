import json
from pathlib import Path

import pytest
import requests
from requests import HTTPError

import pyalex
from pyalex import Authors
from pyalex import Concepts
from pyalex import Domains
from pyalex import Fields
from pyalex import Funders
from pyalex import Institutions
from pyalex import Publishers
from pyalex import Sources
from pyalex import Subfields
from pyalex import Topics
from pyalex import Work
from pyalex import Works
from pyalex import autocomplete
from pyalex.api import QueryError

pyalex.config.max_retries = 10


OPEN_ALEX_ENTITIES = [
    Authors,
    Domains,
    Fields,
    Funders,
    Institutions,
    Publishers,
    Sources,
    Subfields,
    Topics,
    Works,
]


def test_config():
    pyalex.config.email = "pyalex_github_unittests@example.com"

    assert pyalex.config.email == "pyalex_github_unittests@example.com"
    assert pyalex.config.api_key is None
    pyalex.config.api_key = "my_api_key"
    assert pyalex.config.api_key == "my_api_key"
    pyalex.config.api_key = None


@pytest.mark.parametrize("entity", OPEN_ALEX_ENTITIES)
def test_meta_entities(entity):
    r = entity().get()
    assert r.meta.get("count", False)


@pytest.mark.filterwarnings("ignore:.*deprecated.*:DeprecationWarning")
def test_meta_entities_deprecated():
    r = Concepts().get()
    assert r.meta.get("count", False)


def test_works_params():
    assert len(Works(params={"filter": {"publication_year": "2020"}}).get()) == 25


def test_works():
    assert len(Works().filter(publication_year=2020).get()) == 25


def test_works_count():
    assert Works().filter(publication_year=2020).count() > 10_000_000


def test_per_page():
    assert len(Works().filter(publication_year=2020).get(per_page=200)) == 200


def test_per_page_none():
    assert len(Works().filter(publication_year=2020).get(per_page=None)) == 25


def test_per_page_1000():
    with pytest.raises(ValueError):
        Works().filter(publication_year=2020).get(per_page=1000)


def test_per_page_str():
    with pytest.raises(ValueError):
        Works().filter(publication_year=2020).get(per_page="100")


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

    assert len(Works()[w["referenced_works"]]) >= 38

    assert (
        len(Works().filter_or(openalex_id=w["referenced_works"]).get(per_page=100))
        >= 38
    )


def test_works_multifilter():
    r = requests.get(
        "https://api.openalex.org/works?filter=publication_year:2020,is_oa:true"
    ).json()

    r1 = Works().filter(publication_year=2020, is_oa=True).get()
    r2 = Works().filter(publication_year=2020).filter(is_oa=True).get()

    # openalex bug
    # r = (
    #     Works()
    #     .filter(publication_year=2020, open_access={"is_oa": True})
    #     .get()
    # )

    assert r["meta"]["count"] == r1.meta["count"]
    assert r["meta"]["count"] == r2.meta["count"]
    # assert r["meta"]["count"] == c["count"]


def test_works_url():
    url = "https://api.openalex.org/works?filter=publication_year:2020,is_oa:true"

    assert isinstance(Works().filter(publication_year=2020, is_oa=True).url, str)
    assert url == Works().filter(publication_year=2020, is_oa=True).url
    assert url == Works().filter(publication_year=2020).filter(is_oa=True).url

    assert Works().url == "https://api.openalex.org/works"


def test_works_multifilter_meta():
    r1 = Works().filter(publication_year=2020, is_oa=True).get()
    r2 = Works().filter(publication_year=2020).filter(is_oa=True).get()

    assert r1.meta["count"] == r2.meta["count"]


def test_query_error():
    with pytest.raises(QueryError):
        Works().filter(publication_year_error=2020).get()


def test_data_publications():
    w = (
        Works()
        .filter(authorships={"institutions": {"ror": "04pp8hn57"}})
        .filter(type="dataset")
        .group_by("publication_year")
        .get()
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

    a_count = Authors().search_filter(display_name="einstein").count()

    assert r["meta"]["count"] == a_count


def test_referenced_works():
    # the work to extract the referenced works of
    w = Works()["W2741809807"]

    r = Works().filter_or(openalex_id=w["referenced_works"]).get()

    assert r.meta["count"] <= len(w["referenced_works"])


@pytest.mark.xfail()
def test_code_examples():
    # /works?filter=institutions.is_global_south:true,type:dataset&group-by=institutions.country_code  # noqa
    # /works?filter=institutions.is_global_south:true,type:dataset&group-by=institutions.country_code&sort=count:desc  # noqa

    r_original = requests.get(
        "https://api.openalex.org/works?filter=institutions.is_global_south:true"
        + ",type:dataset&group-by=institutions.country_code"
    ).json()

    # the work to extract the referenced works of
    r = (
        Works()
        .filter(institutions={"is_global_south": True})
        .filter(type="dataset")
        .group_by("institutions.country_code")
        .sort(count="desc")
        .get()
    )

    assert r_original["group_by"][0]["count"] == r[0]["count"]


def test_serializable(tmpdir):
    with open(Path(tmpdir, "test.json"), "w") as f:
        json.dump(Works()["W4238809453"], f)

    with open(Path(tmpdir, "test.json")) as f:
        assert "W4238809453" in json.load(f)["id"]


def test_serializable_list(tmpdir):
    with open(Path(tmpdir, "test.json"), "w") as f:
        json.dump(Works().get(), f)

    with open(Path(tmpdir, "test.json")) as f:
        works = [Work(w) for w in json.load(f)]

    assert len(works) == 25
    assert all(isinstance(w, Work) for w in works)


@pytest.mark.skip("This test is not working due to unavailable API.")
def test_ngrams_without_metadata():
    r = Works()["W2023271753"].ngrams()

    assert len(r) == 1068


@pytest.mark.skip("This test is not working due to unavailable API.")
def test_ngrams_with_metadata():
    r, meta = Works()["W2023271753"].ngrams()

    assert meta["count"] == 1068


def test_random_publishers():
    assert isinstance(Publishers().random(), dict)


def test_and_operator():
    urls = [
        "https://api.openalex.org/works?filter=institutions.country_code:tw,institutions.country_code:hk,institutions.country_code:us,publication_year:2022",
        "https://api.openalex.org/works?filter=institutions.country_code:tw+hk+us,publication_year:2022",
    ]

    assert (
        Works()
        .filter(
            institutions={"country_code": ["tw", "hk", "us"]}, publication_year=2022
        )
        .url
        in urls
    )
    assert (
        Works()
        .filter(institutions={"country_code": "tw"})
        .filter(institutions={"country_code": "hk"})
        .filter(institutions={"country_code": "us"})
        .filter(publication_year=2022)
        .url
        in urls
    )
    assert (
        Works()
        .filter(institutions={"country_code": ["tw", "hk"]})
        .filter(institutions={"country_code": "us"})
        .filter(publication_year=2022)
        .url
        in urls
    )


def test_or_operator():
    assert (
        Works()
        .filter_or(
            institutions={"country_code": ["tw", "hk", "us"]}, publication_year=2022
        )
        .url
        == "https://api.openalex.org/works?filter=institutions.country_code:tw|hk|us,publication_year:2022"
    )


def test_not_operator():
    assert (
        Works()
        .filter_not(institutions={"country_code": "us"})
        .filter(publication_year=2022)
        .url
        == "https://api.openalex.org/works?filter=institutions.country_code:!us,publication_year:2022"
    )


def test_not_operator_list():
    assert (
        Works()
        .filter_not(institutions={"country_code": ["tw", "hk", "us"]})
        .filter(publication_year=2022)
        .url
        == "https://api.openalex.org/works?filter=institutions.country_code:!tw+!hk+!us,publication_year:2022"
    )


@pytest.mark.skip("Wait for feedback on issue by OpenAlex")
def test_combined_operators():
    # works:
    # https://api.openalex.org/works?filter=publication_year:>2022,publication_year:!2023

    # doesn't work
    # https://api.openalex.org/works?filter=publication_year:>2022+!2023

    assert (
        Works().filter_gt(publication_year=2022).filter_not(publication_year=2023).url
        == "https://api.openalex.org/works?filter=publication_year:>2022+!2023"
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


def test_auth():
    w_no_auth = Works().get()
    pyalex.config.email = "pyalex_github_unittests@example.com"
    pyalex.config.api_key = "my_api_key"

    w_auth = Works().get()

    pyalex.config.email = None
    pyalex.config.api_key = None

    assert len(w_no_auth) == len(w_auth)


def test_autocomplete_works():
    w = Works().filter(publication_year=2023).autocomplete("planetary boundaries")

    assert all(["external_id" in x for x in w])


def test_autocomplete():
    a = autocomplete("stockholm resilience")

    assert all(["external_id" in x for x in a])


def test_filter_urlencoding():
    assert Works().filter(doi="10.1207/s15327809jls0703&4_2").count() == 1
    assert (
        Works()["https://doi.org/10.1207/s15327809jls0703&4_2"]["id"]
        == "https://openalex.org/W4238483711"
    )


def test_urlencoding_list():
    assert (
        Works()
        .filter_or(
            doi=[
                "https://doi.org/10.1207/s15327809jls0703&4_2",
                "https://doi.org/10.1001/jama.264.8.944b",
            ]
        )
        .count()
        == 2
    )
