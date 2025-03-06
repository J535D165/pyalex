import logging
import warnings
from urllib.parse import quote_plus
from urllib.parse import urlunparse

import requests
from requests.auth import AuthBase
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
    user_agent=f"pyalex/{__version__}",
    openalex_url="https://api.openalex.org",
    max_retries=0,
    retry_backoff_factor=0.1,
    retry_http_codes=[429, 500, 503],
)


class or_(dict):
    pass


class _LogicalExpression:
    token = None

    def __init__(self, value):
        self.value = value

    def __str__(self) -> str:
        return f"{self.token}{self.value}"


class not_(_LogicalExpression):
    token = "!"


class gt_(_LogicalExpression):
    token = ">"


class lt_(_LogicalExpression):
    token = "<"


def _quote_oa_value(v):
    """Prepare a value for the OpenAlex API.

    Applies URL encoding to strings and converts booleans to lowercase strings.
    """

    # workaround for bug https://groups.google.com/u/1/g/openalex-users/c/t46RWnzZaXc
    if isinstance(v, bool):
        return str(v).lower()

    if isinstance(v, _LogicalExpression) and isinstance(v.value, str):
        v.value = quote_plus(v.value)
        return v

    if isinstance(v, str):
        return quote_plus(v)

    return v


def _flatten_kv(d, prefix=None, logical="+"):
    if prefix is None and not isinstance(d, dict):
        raise ValueError("prefix should be set if d is not a dict")

    if isinstance(d, dict):
        logical_subd = "|" if isinstance(d, or_) else logical

        t = []
        for k, v in d.items():
            x = _flatten_kv(
                v, prefix=f"{prefix}.{k}" if prefix else f"{k}", logical=logical_subd
            )
            t.append(x)

        return ",".join(t)
    elif isinstance(d, list):
        list_str = logical.join([f"{_quote_oa_value(i)}" for i in d])
        return f"{prefix}:{list_str}"
    else:
        return f"{prefix}:{_quote_oa_value(d)}"


def _params_merge(params, add_params):
    for k in add_params.keys():
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


def _wrap_values_nested_dict(d, func):
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = _wrap_values_nested_dict(v, func)
        elif isinstance(v, list):
            d[k] = [func(i) for i in v]
        else:
            d[k] = func(v)

    return d


class QueryError(ValueError):
    pass


class OpenAlexEntity(dict):
    pass


class OpenAlexResponseList(list):
    """A list of OpenAlexEntity objects with metadata.

    Attributes:
        meta: a dictionary with metadata about the results
        resource_class: the class to use for each entity in the results

    Arguments:
        results: a list of OpenAlexEntity objects
        meta: a dictionary with metadata about the results
        resource_class: the class to use for each entity in the results

    Returns:
        a OpenAlexResponseList object
    """

    def __init__(self, results, meta=None, resource_class=OpenAlexEntity):
        self.resource_class = resource_class
        self.meta = meta

        super().__init__([resource_class(ent) for ent in results])


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

        r = self.endpoint_class.get(per_page=self.per_page, **pagination_params)

        if self.method == "cursor":
            self._next_value = r.meta["next_cursor"]

        if self.method == "page":
            if len(r) > 0:
                self._next_value = r.meta["page"] + 1
            else:
                self._next_value = None

        self.n = self.n + len(r)

        return r


class OpenAlexAuth(AuthBase):
    """OpenAlex auth class based on requests auth

    Includes the email, api_key and user-agent headers.

    arguments:
        config: an AlexConfig object

    """

    def __init__(self, config):
        self.config = config

    def __call__(self, r):
        if self.config.api_key:
            r.headers["Authorization"] = f"Bearer {self.config.api_key}"

        if self.config.email:
            r.headers["From"] = self.config.email

        if self.config.user_agent:
            r.headers["User-Agent"] = self.config.user_agent

        return r


class BaseOpenAlex:
    """Base class for OpenAlex objects."""

    def __init__(self, params=None):
        self.params = params

    def __getattr__(self, key):
        if key == "groupby":
            raise AttributeError(
                "Object has no attribute 'groupby'. Did you mean 'group_by'?"
            )

        if key == "filter_search":
            raise AttributeError(
                "Object has no attribute 'filter_search'. Did you mean 'search_filter'?"
            )

        return getattr(self, key)

    def __getitem__(self, record_id):
        if isinstance(record_id, list):
            if len(record_id) > 100:
                raise ValueError("OpenAlex does not support more than 100 ids")

            return self.filter_or(openalex_id=record_id).get(per_page=len(record_id))
        elif isinstance(record_id, str):
            self.params = record_id
            return self._get_from_url(self.url)
        else:
            raise ValueError("record_id should be a string or a list of strings")

    def _url_query(self):
        if isinstance(self.params, list):
            return self.filter_or(openalex_id=self.params)
        elif isinstance(self.params, dict):
            l_params = []
            for k, v in self.params.items():
                if v is None:
                    pass
                elif isinstance(v, list):
                    l_params.append(
                        "{}={}".format(k, ",".join(map(_quote_oa_value, v)))
                    )
                elif k in ["filter", "sort"]:
                    l_params.append(f"{k}={_flatten_kv(v)}")
                else:
                    l_params.append(f"{k}={_quote_oa_value(v)}")

            if l_params:
                return "&".join(l_params)

        else:
            return ""

    @property
    def url(self):
        base_path = self.__class__.__name__.lower()

        if isinstance(self.params, str):
            path = f"{base_path}/{_quote_oa_value(self.params)}"
            query = ""
        else:
            path = base_path
            query = self._url_query()

        return urlunparse(("https", "api.openalex.org", path, "", query, ""))

    def count(self):
        return self.get(per_page=1).meta["count"]

    def _get_from_url(self, url):
        res = _get_requests_session().get(url, auth=OpenAlexAuth(config))

        if res.status_code == 403:
            if (
                isinstance(res.json()["error"], str)
                and "query parameters" in res.json()["error"]
            ):
                raise QueryError(res.json()["message"])

        res.raise_for_status()
        res_json = res.json()

        if self.params and "group-by" in self.params:
            return OpenAlexResponseList(
                res_json["group_by"], res_json["meta"], self.resource_class
            )
        elif "results" in res_json:
            return OpenAlexResponseList(
                res_json["results"], res_json["meta"], self.resource_class
            )
        elif "id" in res_json:
            return self.resource_class(res_json)
        else:
            raise ValueError("Unknown response format")

    def get(self, return_meta=False, page=None, per_page=None, cursor=None):
        if per_page is not None and (per_page < 1 or per_page > 200):
            raise ValueError("per_page should be a number between 1 and 200.")

        if not isinstance(self.params, (str, list)):
            self._add_params("per-page", per_page)
            self._add_params("page", page)
            self._add_params("cursor", cursor)

        resp_list = self._get_from_url(self.url)

        if return_meta:
            warnings.warn(
                "return_meta is deprecated, call .meta on the result",
                DeprecationWarning,
                stacklevel=2,
            )
            return resp_list, resp_list.meta
        else:
            return resp_list

    def paginate(self, method="cursor", page=1, per_page=None, cursor="*", n_max=10000):
        if method == "cursor":
            if self.params.get("sample"):
                raise ValueError("method should be 'page' when using sample")
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

    def _add_params(self, argument, new_params, raise_if_exists=False):
        if raise_if_exists:
            raise NotImplementedError("raise_if_exists is not implemented")

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

    def filter_and(self, **kwargs):
        return self.filter(**kwargs)

    def filter_or(self, **kwargs):
        self._add_params("filter", or_(kwargs), raise_if_exists=False)
        return self

    def filter_not(self, **kwargs):
        self._add_params("filter", _wrap_values_nested_dict(kwargs, not_))
        return self

    def filter_gt(self, **kwargs):
        self._add_params("filter", _wrap_values_nested_dict(kwargs, gt_))
        return self

    def filter_lt(self, **kwargs):
        self._add_params("filter", _wrap_values_nested_dict(kwargs, lt_))
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

    def autocomplete(self, s, return_meta=False):
        """autocomplete the string s, for a specific type of entity"""
        self._add_params("q", s)

        resp_list = self._get_from_url(
            urlunparse(
                (
                    "https",
                    "api.openalex.org",
                    f"autocomplete/{self.__class__.__name__.lower()}",
                    "",
                    self._url_query(),
                    "",
                )
            )
        )

        if return_meta:
            warnings.warn(
                "return_meta is deprecated, call .meta on the result",
                DeprecationWarning,
                stacklevel=2,
            )
            return resp_list, resp_list.meta
        else:
            return resp_list


# The API


class Work(OpenAlexEntity):
    def __getitem__(self, key):
        if key == "abstract":
            return invert_abstract(self["abstract_inverted_index"])

        return super().__getitem__(key)

    def ngrams(self, return_meta=False):
        openalex_id = self["id"].split("/")[-1]
        n_gram_url = f"{config.openalex_url}/works/{openalex_id}/ngrams"

        res = _get_requests_session().get(n_gram_url, auth=OpenAlexAuth(config))
        res.raise_for_status()
        results = res.json()

        resp_list = OpenAlexResponseList(results["ngrams"], results["meta"])

        if return_meta:
            warnings.warn(
                "return_meta is deprecated, call .meta on the result",
                DeprecationWarning,
                stacklevel=2,
            )
            return resp_list, resp_list.meta
        else:
            return resp_list


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


class Domain(OpenAlexEntity):
    pass


class Domains(BaseOpenAlex):
    resource_class = Domain


class Field(OpenAlexEntity):
    pass


class Fields(BaseOpenAlex):
    resource_class = Field


class Subfield(OpenAlexEntity):
    pass


class Subfields(BaseOpenAlex):
    resource_class = Subfield


class Topic(OpenAlexEntity):
    pass


class Topics(BaseOpenAlex):
    resource_class = Topic


class Publisher(OpenAlexEntity):
    pass


class Publishers(BaseOpenAlex):
    resource_class = Publisher


class Funder(OpenAlexEntity):
    pass


class Funders(BaseOpenAlex):
    resource_class = Funder


class Autocomplete(OpenAlexEntity):
    pass


class autocompletes(BaseOpenAlex):
    """Class to autocomplete without being based on the type of entity"""

    resource_class = Autocomplete

    def __getitem__(self, key):
        return self._get_from_url(
            urlunparse(
                (
                    "https",
                    "api.openalex.org",
                    "autocomplete",
                    "",
                    f"q={quote_plus(key)}",
                    "",
                )
            )
        )


class Concept(OpenAlexEntity):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Concept is deprecated by OpenAlex and replaced by topics.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class Concepts(BaseOpenAlex):
    resource_class = Concept

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Concepts is deprecated by OpenAlex and replaced by topics.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


def autocomplete(s):
    """autocomplete with any type of entity"""
    return autocompletes()[s]


# aliases
People = Authors
Journals = Sources
