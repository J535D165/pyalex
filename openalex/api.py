import logging
from urllib.parse import quote
from urllib.parse import quote_plus
from urllib.parse import urlencode

import requests

OPENALEX_URL = "https://api.openalex.org"


def _flatten_kv(k, v):

    if isinstance(v, dict):

        if len(v.keys()) > 1:
            raise ValueError()

        k_0 = list(v.keys())[0]
        return str(k) + "." + _flatten_kv(k_0, v[k_0])
    else:
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

    def _parse_result(self, res):

        return res

    def get(self, return_meta=False):

        if self.record_id is not None:
            url = self.url + "/" + self.record_id
        else:
            l = []
            for k, v in self.params.items():
                if k in ["filter", "sort"]:
                    l.append(
                        k + "=" + ",".join(_flatten_kv(k, d) for k, d in v.items())
                    )
                else:
                    l.append(k + "=" + quote_plus(v))

            url = self.url + "?" + "&".join(l)

        res = requests.get(url)
        res.raise_for_status()
        res_json = res.json()

        # single result
        if self.record_id is not None:
            return self._parse_result(res_json)

        # group_by or results page
        if "group_by" in self.params:
            results = res_json["group_by"]
        else:
            results = self._parse_result(res_json["results"])

        # return result and metadata
        if return_meta:
            return res_json["meta"], results
        else:
            return results

    def get_random(self):

        res = requests.get(self.url + "/random")
        res.raise_for_status()

        return res.json()

    def filter(self, **kwargs):

        p = self.params.copy()

        if "filter" in p:
            p["filter"] = {**p["filter"], **kwargs}
        else:
            p["filter"] = kwargs

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
        p["group_by"] = group_key
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

        self.url = OPENALEX_URL + "/venue"


class Institutions(BaseOpenAlex):
    def __init__(self, *args, **kwargs):
        super(Institutions, self).__init__(*args, **kwargs)

        self.url = OPENALEX_URL + "/institution"


class Concepts(BaseOpenAlex):
    def __init__(self, *args, **kwargs):
        super(Concepts, self).__init__(*args, **kwargs)

        self.url = OPENALEX_URL + "/concept"
