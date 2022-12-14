import logging
from urllib.parse import quote_plus

import requests

try:
    from openalex._version import __version__
except ImportError:
    __version__ = "0.0.0"


class AlexConfig(dict):
    def __getattr__(self, key):
        return super().__getitem__(key)

    def __setattr__(self, key, value):
        return super().__setitem__(key, value)


config = AlexConfig(email=None, openalex_url="https://api.openalex.org")


def _flatten_kv(k, v):

    if isinstance(v, dict):

        if len(v.keys()) > 1:
            raise ValueError()

        k_0 = list(v.keys())[0]
        return str(k) + "." + _flatten_kv(k_0, v[k_0])
    else:

        # workaround for bug https://groups.google.com/u/1/g/openalex-users/c/t46RWnzZaXc
        v = str(v).lower() if isinstance(v, bool) else v

        return str(k) + ":" + str(v)


def invert_abstract(inv_index):

    if inv_index is not None:
        l = [(w, p) for w, pos in inv_index.items() for p in pos]
        return " ".join(map(lambda x: x[0], sorted(l, key=lambda x: x[1])))


class QueryError(ValueError):
    pass


class OpenAlexEntity(dict):

    pass


class Work(OpenAlexEntity):
    """OpenAlex work object."""

    def __getitem__(self, key):

        if key == "abstract":
            return invert_abstract(self["abstract_inverted_index"])

        return super().__getitem__(key)

    def ngrams(self, return_meta=False):

        openalex_id = self["id"].split("/")[-1]

        res = requests.get(
            f"{config.openalex_url}/works/{openalex_id}/ngrams",
            headers={"User-Agent": "pyalex/" + __version__, "email": config.email},
        )
        res.raise_for_status()
        results = res.json()

        # return result and metadata
        if return_meta:
            return results["ngrams"], results["meta"]
        else:
            return results["ngrams"]


class Author(OpenAlexEntity):
    pass


class Venue(OpenAlexEntity):
    pass


class Institution(OpenAlexEntity):
    pass


class Concept(OpenAlexEntity):
    pass


class CursorPaginator(object):
    def __init__(self, alex_class=None, per_page=None, cursor="*", n_max=None):

        self.alex_class = alex_class
        self.per_page = per_page
        self.cursor = cursor
        self.n_max = n_max

    def __iter__(self):

        self.n = 0

        return self

    def __next__(self):

        if self.n_max and self.n >= self.n_max:
            raise StopIteration

        r, m = self.alex_class.get(
            return_meta=True, per_page=self.per_page, cursor=self.cursor
        )

        if m["next_cursor"] is None:
            raise StopIteration

        self.n = self.n + len(r)
        self.cursor = m["next_cursor"]

        return r


class BaseOpenAlex(object):

    """Base class for OpenAlex objects."""

    url = None

    def __init__(self, params={}):

        self.params = params

    def _get_multi_items(self, record_list):

        return self.filter(openalex_id="|".join(record_list)).get()

    def __getattr__(self, key):

        if key == "groupby":
            raise AttributeError(
                "Object has no attribute 'groupby'. "
                "Did you mean 'group_by'?")

        if key == "filter_search":
            raise AttributeError(
                "Object has no attribute 'filter_search'. "
                "Did you mean 'search_filter'?")

        return getattr(self, key)

    def __getitem__(self, record_id):

        if isinstance(record_id, list):
            return self._get_multi_items(record_id)

        url = self.url + "/" + record_id

        res = requests.get(
            url, headers={"User-Agent": "pyalex/" + __version__, "email": config.email}
        )
        res.raise_for_status()
        res_json = res.json()

        return self.obj(res_json)

    def get(self, return_meta=False, page=None, per_page=None, cursor=None):

        if per_page is not None and (per_page < 1 or per_page > 200):
            raise ValueError("per_page should be a number between 1 and 200.")

        self.params["per-page"] = per_page
        self.params["page"] = page
        self.params["cursor"] = cursor

        l = []
        for k, v in self.params.items():
            if k in ["filter", "sort"]:
                l.append(k + "=" + ",".join(_flatten_kv(k, d) for k, d in v.items()))
            elif v is None:
                pass
            else:
                l.append(k + "=" + quote_plus(str(v)))

        url = self.url + "?" + "&".join(l)

        res = requests.get(
            url, headers={"User-Agent": "pyalex/" + __version__, "email": config.email}
        )
        res_json = res.json()

        if res.status_code == 403 and "query parameters" in res_json["error"]:
            raise QueryError(res_json["message"])

        res.raise_for_status()

        # group-by or results page
        if "group-by" in self.params:
            results = res_json["group_by"]
        else:
            results = [self.obj(ent) for ent in res_json["results"]]

        # return result and metadata
        if return_meta:
            return results, res_json["meta"]
        else:
            return results

    def paginate(self, per_page=None, cursor="*", n_max=10000):

        return CursorPaginator(self, per_page=per_page, cursor=cursor, n_max=n_max)

    def random(self):

        return self.__getitem__("random")

    def filter(self, **kwargs):

        p = self.params.copy()

        if "filter" in p:
            p["filter"] = {**p["filter"], **kwargs}
        else:
            p["filter"] = kwargs

        self.params = p
        logging.debug("Params updated:", p)

        return self

    def search_filter(self, **kwargs):

        search_kwargs = {f"{k}.search": v for k, v in kwargs.items()}

        p = self.params.copy()

        if "filter" in p:
            p["filter"] = {**p["filter"], **search_kwargs}
        else:
            p["filter"] = search_kwargs

        self.params = p
        logging.debug("Params updated:", p)

        return self

    def sort(self, **kwargs):

        p = self.params.copy()

        if "sort" in p:
            p["sort"] = {**p["sort"], **kwargs}
        else:
            p["sort"] = kwargs

        self.params = p
        logging.debug("Params updated:", p)

        return self

    def group_by(self, group_key):

        p = self.params.copy()
        p["group-by"] = group_key
        self.params = p

        logging.debug("Params updated:", p)

        return self

    def search(self, s):

        p = self.params.copy()
        p["search"] = s
        self.params = p

        logging.debug("Params updated:", p)

        return self


class Works(BaseOpenAlex):

    url = config.openalex_url + "/works"
    obj = Work


class Authors(BaseOpenAlex):

    url = config.openalex_url + "/authors"
    obj = Author


class Venues(BaseOpenAlex):

    url = config.openalex_url + "/venues"
    obj = Venue


class Institutions(BaseOpenAlex):

    url = config.openalex_url + "/institutions"
    obj = Institution


class Concepts(BaseOpenAlex):

    url = config.openalex_url + "/concepts"
    obj = Concept


# aliases
People = Authors
Journals = Venues
