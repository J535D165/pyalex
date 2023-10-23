import logging
import warnings
from urllib.parse import quote_plus

import requests
from urllib3.util import Retry

try:
    from pyalex._version import __version__
except ImportError:
    __version__ = "0.0.0"


class AlexConfig(dict):
    def __getattr__(self, key):
        return super().__getitem__(key)

    def __setattr__(self, key, value):
        return super().__setitem__(key, value)


config = AlexConfig(
    email=None,
    api_key=None,
    openalex_url="https://api.openalex.org",
    max_retries=0,
    retry_backoff_factor=0.1,
    retry_http_codes=[429, 500, 503],
)


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


def _get_requests_session():
    # create an Requests Session with automatic retry:
    requests_session = requests.Session()
    retries = Retry(
        total=config.max_retries,
        backoff_factor=config.retry_backoff_factor,
        status_forcelist=config.retry_http_codes,
        allowed_methods={"GET"},
    )
    requests_session.mount(
        "https://", requests.adapters.HTTPAdapter(max_retries=retries)
    )

    return requests_session


def invert_abstract(inv_index):
    if inv_index is not None:
        l_inv = [(w, p) for w, pos in inv_index.items() for p in pos]
        return " ".join(map(lambda x: x[0], sorted(l_inv, key=lambda x: x[1])))


class QueryError(ValueError):
    pass


class OpenAlexEntity(dict):
    pass


class Paginator:
    VALUE_CURSOR_START = "*"
    VALUE_NUMBER_START = 1

    def __init__(
        self, endpoint_class, method="cursor", value=None, per_page=None, n_max=None
    ):
        self.method = method
        self.endpoint_class = endpoint_class
        self.value = value
        self.per_page = per_page
        self.n_max = n_max

        self._next_value = value

    def __iter__(self):
        self.n = 0

        return self

    def _is_max(self):
        if self.n_max and self.n >= self.n_max:
            return True
        return False

    def __next__(self):
        if self._next_value is None or self._is_max():
            raise StopIteration

        if self.method == "cursor":
            pagination_params = {"cursor": self._next_value}
        elif self.method == "page":
            pagination_params = {"page": self._next_value}
        else:
            raise ValueError()

        results, meta = self.endpoint_class.get(
            return_meta=True, per_page=self.per_page, **pagination_params
        )

        if self.method == "cursor":
            self._next_value = meta["next_cursor"]

        if self.method == "page":
            if len(results) > 0:
                self._next_value = meta["page"] + 1
            else:
                self._next_value = None

        self.n = self.n + len(results)

        return results


class BaseOpenAlex:
    """Base class for OpenAlex objects."""

    def __init__(self, params=None):
        self.params = params

    def _get_multi_items(self, record_list):
        return self.filter(openalex_id="|".join(record_list)).get()

    def _full_collection_name(self):
        return config.openalex_url + "/" + self.__class__.__name__.lower()

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

        return self._get_from_url(
            self._full_collection_name() + "/" + record_id, return_meta=False
        )

    @property
    def url(self):
        if not self.params:
            return self._full_collection_name()

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
            return self._full_collection_name() + "?" + "&".join(l_params)

        return self._full_collection_name()

    def count(self):
        _, m = self.get(return_meta=True, per_page=1)

        return m["count"]

    def _get_from_url(self, url, return_meta=False):
        params = {"api_key": config.api_key} if config.api_key else {}

        res = _get_requests_session().get(
            url,
            headers={"User-Agent": "pyalex/" + __version__, "email": config.email},
            params=params,
        )

        # handle query errors
        if res.status_code == 403:
            if (
                isinstance(res.json()["error"], str)
                and "query parameters" in res.json()["error"]
            ):
                raise QueryError(res.json()["message"])

        res.raise_for_status()
        res_json = res.json()

        # group-by or results page
        if self.params and "group-by" in self.params:
            results = res_json["group_by"]
        elif "results" in res_json:
            results = [self.resource_class(ent) for ent in res_json["results"]]
        elif "id" in res_json:
            results = self.resource_class(res_json)
        else:
            raise ValueError("Unknown response format")

        # return result and metadata
        if return_meta:
            return results, res_json["meta"]
        else:
            return results

    def get(self, return_meta=False, page=None, per_page=None, cursor=None):
        if per_page is not None and (per_page < 1 or per_page > 200):
            raise ValueError("per_page should be a number between 1 and 200.")

        self._add_params("per-page", per_page)
        self._add_params("page", page)
        self._add_params("cursor", cursor)

        return self._get_from_url(self.url, return_meta=return_meta)

    def paginate(self, method="cursor", page=1, per_page=None, cursor="*", n_max=10000):
        if method == "cursor":
            value = cursor
        elif method == "page":
            value = page
        else:
            raise ValueError("Method should be 'cursor' or 'page'")

        return Paginator(
            self, method=method, value=value, per_page=per_page, n_max=n_max
        )

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


# The API


class Work(OpenAlexEntity):
    def __getitem__(self, key):
        if key == "abstract":
            return invert_abstract(self["abstract_inverted_index"])

        return super().__getitem__(key)

    def ngrams(self, return_meta=False):
        openalex_id = self["id"].split("/")[-1]

        res = _get_requests_session().get(
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


class Works(BaseOpenAlex):
    resource_class = Work


class Author(OpenAlexEntity):
    pass


class Authors(BaseOpenAlex):
    resource_class = Author


class Source(OpenAlexEntity):
    pass


class Sources(BaseOpenAlex):
    resource_class = Source


class Institution(OpenAlexEntity):
    pass


class Institutions(BaseOpenAlex):
    resource_class = Institution


class Concept(OpenAlexEntity):
    pass


class Concepts(BaseOpenAlex):
    resource_class = Concept


class Publisher(OpenAlexEntity):
    pass


class Publishers(BaseOpenAlex):
    resource_class = Publisher


class Funder(OpenAlexEntity):
    pass


class Funders(BaseOpenAlex):
    resource_class = Funder


def Venue(*args, **kwargs):  # deprecated
    # warn about deprecation
    warnings.warn(
        "Venue is deprecated. Use Sources instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return Source(*args, **kwargs)


def Venues(*args, **kwargs):  # deprecated
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
