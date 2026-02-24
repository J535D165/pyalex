import datetime
import json
import os
from functools import wraps
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from requests import HTTPError

import pyalex
from pyalex import Authors
from pyalex import Awards
from pyalex import Concepts
from pyalex import Domains
from pyalex import Fields
from pyalex import Funders
from pyalex import Institutions
from pyalex import Keywords
from pyalex import Publishers
from pyalex import Sources
from pyalex import Subfields
from pyalex import Topics
from pyalex import Work
from pyalex import Works
from pyalex import autocomplete
from pyalex.api import QueryError

# Load environment variables from .env file
load_dotenv()

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


OPEN_ALEX_ENTITIES = [
    Authors,
    Awards,
    Domains,
    Fields,
    Funders,
    Institutions,
    Keywords,
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


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
@pytest.mark.parametrize("entity", OPEN_ALEX_ENTITIES)
def test_meta_entities(entity):
    r = entity().get()
    assert r.meta.get("count", False)


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
@pytest.mark.filterwarnings("ignore:.*deprecated.*:DeprecationWarning")
def test_meta_entities_deprecated():
    r = Concepts().get()
    assert r.meta is not None
    assert r.meta.get("count", False)


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_works_params():
    assert len(Works(params={"filter": {"publication_year": "2020"}}).get()) == 25


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_works():
    assert len(Works().filter(publication_year=2020).get()) == 25


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_works_count():
    assert Works().filter(publication_year=2020).count() > 10_000_000


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_per_page():
    assert len(Works().filter(publication_year=2020).get(per_page=200)) == 200


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_per_page_none():
    assert len(Works().filter(publication_year=2020).get(per_page=None)) == 25


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_per_page_1000():
    with pytest.raises(ValueError):
        Works().filter(publication_year=2020).get(per_page=1000)


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
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


@requires_api_key(reason="OpenAlex requires authentication for random() endpoint")
def test_random_works():
    assert isinstance(Works().random(), dict)


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_multi_works():
    # the work to extract the referenced works of
    w = Works()["W2741809807"]

    assert len(Works()[w["referenced_works"]]) >= 38

    assert (
        len(Works().filter_or(openalex_id=w["referenced_works"]).get(per_page=100))
        >= 38
    )


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
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
    assert r1.meta is not None
    assert r2.meta is not None

    assert r["meta"]["count"] == r1.meta["count"]
    assert r["meta"]["count"] == r2.meta["count"]
    # assert r["meta"]["count"] == c["count"]


def test_works_url():
    url = "https://api.openalex.org/works?filter=publication_year:2020,is_oa:true"

    assert isinstance(Works().filter(publication_year=2020, is_oa=True).url, str)
    assert url == Works().filter(publication_year=2020, is_oa=True).url
    assert url == Works().filter(publication_year=2020).filter(is_oa=True).url

    assert Works().url == "https://api.openalex.org/works"


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_works_multifilter_meta():
    r1 = Works().filter(publication_year=2020, is_oa=True).get()
    r2 = Works().filter(publication_year=2020).filter(is_oa=True).get()

    assert r1.meta is not None
    assert r2.meta is not None
    assert r1.meta["count"] == r2.meta["count"]


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_query_error():
    with pytest.raises(QueryError):
        Works().filter(publication_year_error=2020).get()


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_data_publications():
    w = (
        Works()
        .filter(authorships={"institutions": {"ror": "04pp8hn57"}})
        .filter(type="dataset")
        .group_by("publication_year")
        .get()
    )

    assert len(w) > 20


@requires_api_key(reason="OpenAlex requires authentication for search queries")
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


@requires_api_key(reason="OpenAlex requires authentication for search_filter queries")
def test_search_filter():
    r = requests.get(
        "https://api.openalex.org/authors?filter=display_name.search:einstein"
    ).json()

    a_count = Authors().search_filter(display_name="einstein").count()

    assert r["meta"]["count"] == a_count


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_referenced_works():
    # the work to extract the referenced works of
    w = Works()["W2741809807"]

    r = Works().filter_or(openalex_id=w["referenced_works"]).get()

    assert r.meta is not None
    assert r.meta["count"] <= len(w["referenced_works"])


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
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


@requires_api_key(reason="OpenAlex requires authentication for unfiltered queries")
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


@requires_api_key(reason="OpenAlex requires authentication for random() endpoint")
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


@requires_api_key(
    reason="OpenAlex requires authentication for filter queries with autocomplete"
)
def test_autocomplete_works():
    w = Works().filter(publication_year=2023).autocomplete("planetary boundaries")

    assert all(["external_id" in x for x in w])


@requires_api_key(reason="OpenAlex requires authentication for autocomplete endpoint")
def test_autocomplete():
    a = autocomplete("stockholm resilience")

    assert all(["external_id" in x for x in a])


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
def test_filter_urlencoding():
    assert Works().filter(doi="10.1207/s15327809jls0703&4_2").count() == 1
    assert (
        Works()["https://doi.org/10.1207/s15327809jls0703&4_2"]["id"]
        == "https://openalex.org/W4238483711"
    )


@requires_api_key(reason="OpenAlex requires authentication for filter queries")
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


def test_premium_api_no_valid_key():
    pyalex.config.email = "pyalex_github_unittests@example.com"
    pyalex.config.api_key = "my_api_key"
    with pytest.raises(QueryError):
        Works().get()


def test_unauthenticated_filter_call():
    """Test that filter/search calls without authentication will fail.

    (post Feb 11, 2025)

    This test documents the expected behavior when OpenAlex enforces their new policy
    allowing only singleton calls without authentication. Filter and search queries
    will require an API key.

    Note: This test currently passes the filter call because OpenAlex hasn't yet
    enforced the restriction. Once the policy is enforced, this test should fail
    and we'll need to mark it as @requires_api_key instead.
    """
    # Ensure no API key is set
    original_api_key = pyalex.config.api_key
    pyalex.config.api_key = None

    try:
        # This should work for now, but will fail once OpenAlex enforces the policy
        # Singleton calls like Works()["ID"] should still work without auth
        result = Works()["W2741809807"]
        assert result["id"] == "https://openalex.org/W2741809807"

        # Filter/search calls will fail once policy is enforced
        # For now, they still work, so we document the expected future behavior
        # Once OpenAlex enforces the policy, this should raise an error
        filter_result = Works().filter(publication_year=2020).get()
        # If we get here, the policy hasn't been enforced yet
        assert len(filter_result) > 0
    finally:
        # Restore original API key
        pyalex.config.api_key = original_api_key


@pytest.mark.skipif(
    not os.environ.get("OPENALEX_API_KEY"),
    reason="OPENALEX_API_KEY is not set in the environment variables",
)
def test_premium_api():
    # This test requires a valid API key set in the config. If from_updated_date
    # is set, it should return works updated since the start of the current
    # year. If no API key is set, it should raise an error.
    pyalex.config.api_key = os.environ["OPENALEX_API_KEY"]

    Works().filter(from_updated_date=f"{datetime.datetime.now().year}-01-01").get()

    pyalex.config.api_key = None


def test_work_pdf_and_tei_download(tmpdir):
    """Test downloading PDF and TEI content for a Work.

    This test verifies that:
    1. A Work object has accessible pdf and tei properties
    2. PDF and TEI objects have correct URLs
    3. PDF and TEI content can be retrieved and downloaded to files
    """

    pyalex.config.api_key = os.environ["OPENALEX_API_KEY"]

    # Get a work
    work = Works()["W4412002745"]

    # Test that pdf and tei properties return the correct types
    assert work.pdf is not None
    assert work.tei is not None

    # Test that PDF has a valid URL
    pdf_url = work.pdf.url
    assert pdf_url.endswith(".pdf")
    assert "content.openalex.org" in pdf_url
    assert "W4412002745" in pdf_url

    # Test that TEI has a valid URL
    tei_url = work.tei.url
    assert "grobid-xml" in tei_url
    assert "content.openalex.org" in tei_url
    assert "W4412002745" in tei_url

    # Test downloading PDF content
    pdf_path = Path(tmpdir) / "test.pdf"
    work.pdf.download(str(pdf_path))
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    # Test downloading TEI content
    tei_path = Path(tmpdir) / "test.xml"
    work.tei.download(str(tei_path))
    assert tei_path.exists()
    assert tei_path.stat().st_size > 0


# Tests for similar() functionality


def test_similar_url():
    """Test URL construction with similar()."""
    url = Works().similar("machine learning").url
    assert "works" in url
    assert "search.semantic=machine" in url


@requires_api_key(reason="OpenAlex requires authentication for semantic search queries")
def test_similar_short():
    """Test basic similar() with short text."""
    w = Works().similar("machine learning").get()
    assert len(w) >= 0
    assert w.meta.get("count") is not None


@requires_api_key(reason="OpenAlex requires authentication for semantic search queries")
def test_similar_with_filter():
    """Test similar() with filters."""
    w = Works().similar("climate change").filter(publication_year=2023).get()
    assert len(w) >= 0
    # All results should be from 2023 if there are results
    if len(w) > 0:
        assert all(work.get("publication_year") == 2023 for work in w)


@requires_api_key(reason="OpenAlex requires authentication for semantic search queries")
def test_similar_count():
    """Test count() with similar()."""
    count = Works().similar("artificial intelligence").count()
    assert count >= 0


@requires_api_key(reason="OpenAlex requires authentication for semantic search queries")
def test_similar_per_page():
    """Test similar() with per_page parameter."""
    w = Works().similar("deep learning").get(per_page=10)
    assert len(w) <= 10
