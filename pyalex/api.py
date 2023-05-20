import logging
import warnings
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


config = AlexConfig(email=None, api_key=None, openalex_url="https://api.openalex.org")


def _flatten_kv(d, prefix=""):

    if isinstance(d, dict):

        t = []
        for k, v in d.items():
            if isinstance(v, list):
                t.extend([f"{prefix}.{k}:{i}" for i in v])
            else:
                new_prefix = f"{prefix}.{k}" if prefix else f"{k}"
                x = _flatten_kv(v, prefix=new_prefix)
                t.append(x)

        return ",".join(t)
    else:

        # workaround for bug https://groups.google.com/u/1/g/openalex-users/c/t46RWnzZaXc
        d = str(d).lower() if isinstance(d, bool) else d

        return f"{prefix}:{d}"


def _params_merge(params, add_params):

    for k, _v in add_params.items():
        if (
            k in params
            and isinstance(params[k], dict)
            and isinstance(add_params[k], dict)
        ):
            _params_merge(params[k], add_params[k])
        elif (
            k in params
            and not isinstance(params[k], list)
            and isinstance(add_params[k], list)
        ):
            # example: params="a" and add_params=["b", "c"]
            params[k] = [params[k]] + add_params[k]
        elif (
            k in params
            and isinstance(params[k], list)
            and not isinstance(add_params[k], list)
        ):
            # example: params=["b", "c"] and add_params="a"
            params[k] = params[k] + [add_params[k]]
        elif k in params:
            params[k] = [params[k], add_params[k]]
        else:
            params[k] = add_params[k]


def invert_abstract(inv_index):

    if inv_index is not None:
        l_inv = [(w, p) for w, pos in inv_index.items() for p in pos]
        return " ".join(map(lambda x: x[0], sorted(l_inv, key=lambda x: x[1])))


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


class Source(OpenAlexEntity):
    pass


class Institution(OpenAlexEntity):
    pass


class Concept(OpenAlexEntity):
    pass


class Publisher(OpenAlexEntity):
    pass


class Funder(OpenAlexEntity):
    pass

# deprecated


def Venue(*args, **kwargs):

    # warn about deprecation
    warnings.warn(
        "Venue is deprecated. Use Sources instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return Source(*args, **kwargs)


class CursorPaginator:
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


class BaseOpenAlex:

    """Base class for OpenAlex objects."""

    def __init__(self, params=None):

        self.params = params

    def _get_multi_items(self, record_list):

        return self.filter(openalex_id="|".join(record_list)).get()

    def __getattr__(self, key):

        if key == "groupby":
            raise AttributeError(
                "Object has no attribute 'groupby'. " "Did you mean 'group_by'?"
            )

        if key == "filter_search":
            raise AttributeError(
                "Object has no attribute 'filter_search'. "
                "Did you mean 'search_filter'?"
            )

        return getattr(self, key)

    def __getitem__(self, record_id):

        if isinstance(record_id, list):
            return self._get_multi_items(record_id)

        url = self.url_collection + "/" + record_id
        params = {"api_key": config.api_key} if config.api_key else {}
        res = requests.get(
            url,
            headers={"User-Agent": "pyalex/" + __version__, "email": config.email},
            params=params,
        )
        res.raise_for_status()
        res_json = res.json()

        return self.obj(res_json)

    @property
    def url(self):

        if not self.params:
            return self.url_collection

        l_params = []
        for k, v in self.params.items():

            if v is None:
                pass
            elif isinstance(v, list):
                v_quote = [quote_plus(q) for q in v]
                l_params.append(k + "=" + ",".join(v_quote))
            elif k in ["filter", "sort"]:
                l_params.append(k + "=" + _flatten_kv(v))
            else:
                l_params.append(k + "=" + quote_plus(str(v)))

        if l_params:
            return self.url_collection + "?" + "&".join(l_params)

        return self.url_collection

    def get(self, return_meta=False, page=None, per_page=None, cursor=None):

        if per_page is not None and (per_page < 1 or per_page > 200):
            raise ValueError("per_page should be a number between 1 and 200.")

        self._add_params("per-page", per_page)
        self._add_params("page", page)
        self._add_params("cursor", cursor)

        params = {"api_key": config.api_key} if config.api_key else {}
        res = requests.get(
            self.url,
            headers={"User-Agent": "pyalex/" + __version__, "email": config.email},
            params=params,
        )

        # handle query errors
        if res.status_code == 403:
            res_json = res.json()
            if (
                isinstance(res_json["error"], str)
                and "query parameters" in res_json["error"]
            ):
                raise QueryError(res_json["message"])
        res.raise_for_status()

        res_json = res.json()

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
        """Used for paging results of large responses using cursor paging. 
        
        OpenAlex offers two methods for paging: basic paging and cursor paging. 
        Both methods are supported by PyAlex, although cursor paging seems to be 
        easier to implement and less error-prone.

        Args:
            per_page (_type_, optional): Entries per page to return. Defaults to None.
            cursor (str, optional): _description_. Defaults to "*".
            n_max (int, optional): Number of max results (not pages) to return. 
                Defaults to 10000.

        Returns:
            CursorPaginator: Iterator to use for returning and processing each page 
            result in sequence. 
        """
        return CursorPaginator(self, per_page=per_page, cursor=cursor, n_max=n_max)

    def random(self):

        return self.__getitem__("random")

    def _add_params(self, argument, new_params):

        if self.params is None:
            self.params = {argument: new_params}
        elif argument in self.params and isinstance(self.params[argument], dict):
            _params_merge(self.params[argument], new_params)
        else:
            self.params[argument] = new_params

        logging.debug("Params updated:", self.params)

    def filter(self, **kwargs):

        self._add_params("filter", kwargs)
        return self

    def search_filter(self, **kwargs):

        self._add_params("filter", {f"{k}.search": v for k, v in kwargs.items()})
        return self

    def sort(self, **kwargs):

        self._add_params("sort", kwargs)
        return self

    def group_by(self, group_key):

        self._add_params("group-by", group_key)
        return self

    def search(self, s):

        self._add_params("search", s)
        return self

    def sample(self, n, seed=None):

        self._add_params("sample", n)
        self._add_params("seed", seed)
        return self

    def select(self, s):

        self._add_params("select", s)
        return self


class Works(BaseOpenAlex):

    url_collection = config.openalex_url + "/works"
    obj = Work


class Authors(BaseOpenAlex):

    url_collection = config.openalex_url + "/authors"
    obj = Author


class Sources(BaseOpenAlex):

    url_collection = config.openalex_url + "/sources"
    obj = Source


class Institutions(BaseOpenAlex):

    url_collection = config.openalex_url + "/institutions"
    obj = Institution


class Concepts(BaseOpenAlex):

    url_collection = config.openalex_url + "/concepts"
    obj = Concept


class Publishers(BaseOpenAlex):

    url_collection = config.openalex_url + "/publishers"
    obj = Publisher


class Funders(BaseOpenAlex):

    url_collection = config.openalex_url + "/funders"
    obj = Funder

# deprecated


def Venues(*args, **kwargs):

    # warn about deprecation
    warnings.warn(
        "Venues is deprecated. Use Sources instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return Sources(*args, **kwargs)


# aliases
People = Authors
Journals = Sources
