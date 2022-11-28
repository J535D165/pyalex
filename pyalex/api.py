import logging
from urllib.parse import quote_plus

import requests

try:
    from openalex._version import __version__
except ImportError:
    __version__ = "0.0.0"

OPENALEX_URL = "https://api.openalex.org"
EMAIL = None


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


class BaseOpenAlex(object):

    """Base class for OpenAlex objects."""

    def __init__(self, record_id=None, params={}):
        # super(BaseOpenAlex, self).__init__()

        self.record_id = record_id
        self.url = None
        self.params = params

    @property
    def _headers(self):
        return {"User-Agent": "pyalex/" + __version__, "email": EMAIL}

    def _parse_result(self, res):

        return res

    def get(self, return_meta=False, page=None, per_page=None, cursor=None):

        if per_page is not None and (per_page < 1 or per_page > 200):
            raise ValueError("per_page should be a number between 1 and 200.")

        if self.record_id is not None:
            url = self.url + "/" + self.record_id
        else:
            self.params["per-page"] = per_page
            self.params["page"] = page
            self.params["cursor"] = cursor

            l = []
            for k, v in self.params.items():
                if k in ["filter", "sort"]:
                    l.append(
                        k + "=" + ",".join(_flatten_kv(k, d) for k, d in v.items())
                    )
                elif v is None:
                    pass
                else:
                    l.append(k + "=" + quote_plus(str(v)))

            url = self.url + "?" + "&".join(l)

        res = requests.get(url, headers=self._headers)
        res.raise_for_status()
        res_json = res.json()

        # single result
        if self.record_id is not None:
            return self._parse_result(res_json)

        # group-by or results page
        if "group-by" in self.params:
            results = res_json["group_by"]
        else:
            results = self._parse_result(res_json["results"])

        # return result and metadata
        if return_meta:
            return results, res_json["meta"]
        else:
            return results

    def random(self):

        self.record_id = "random"
        return self.get()

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
    def __init__(self, *args, abstract=True, **kwargs):
        super(Works, self).__init__(*args, **kwargs)

        self.abstract = abstract
        self.url = OPENALEX_URL + "/works"

    def _parse_result(self, res):

        if self.abstract and "abstract_inverted_index" in res:
            res["abstract"] = invert_abstract(res["abstract_inverted_index"])
            del res["abstract_inverted_index"]

        return res


class Authors(BaseOpenAlex):
    def __init__(self, *args, **kwargs):
        super(Authors, self).__init__(*args, **kwargs)

        self.url = OPENALEX_URL + "/authors"


class Venues(BaseOpenAlex):
    def __init__(self, *args, **kwargs):
        super(Venues, self).__init__(*args, **kwargs)

        self.url = OPENALEX_URL + "/venues"


class Institutions(BaseOpenAlex):
    def __init__(self, *args, **kwargs):
        super(Institutions, self).__init__(*args, **kwargs)

        self.url = OPENALEX_URL + "/institutions"


class Concepts(BaseOpenAlex):
    def __init__(self, *args, **kwargs):
        super(Concepts, self).__init__(*args, **kwargs)

        self.url = OPENALEX_URL + "/concepts"


# aliases
People = Authors
Journals = Venues
