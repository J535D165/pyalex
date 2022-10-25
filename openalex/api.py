import requests
from urllib.parse import quote_plus, quote, urlencode
import logging

def _flatten_kv(k, v):

    if isinstance(v, dict):

        if len(v.keys()) > 1:
            raise ValueError()

        k_0 = list(v.keys())[0]
        return str(k) + "." + _flatten_kv(k_0, v[k_0])
    else:
        return str(k) + ":" + str(v)


class BaseOpenAlex(object):

    """Base class for OpenAlex objects."""
    def __init__(self, record_id=None, params= {}):
        # super(BaseOpenAlex, self).__init__()

        self.record_id = record_id
        self.url = None
        self.params = params

    def get(self, return_meta=False):

        if self.record_id is not None:
            url = self.url + "/" + self.record_id
        else:
            url = self.url

        l = []
        # level of filter and sort
        for k, v in self.params.items():
            l.append(k + "=" + ",".join(_flatten_kv(k, d) for k, d in v.items()))

        res = requests.get(url + "?" + '&'.join(l))
        res.raise_for_status()
        res_json = res.json()

        if self.record_id is not None:
            return res_json

        if return_meta:
            return res_json["meta"], res_json["results"]
        else:
            return res_json["results"]

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

    # def sort(self, **kwargs):

    #     parsed_args = list(_parse_kwargs(kwargs))

    #     if "sort" in self.params:
    #         self.params["sort"].extend(parsed_args)
    #     else:
    #         self.params["sort"] = parsed_args

    #     return self


class Works(BaseOpenAlex):

    def __init__(self, *args, **kwargs):
        super(Works, self).__init__(*args, **kwargs)

        self.url = "https://api.openalex.org/works"


class Authors(BaseOpenAlex):

    def __init__(self, *args, **kwargs):
        super(Authors, self).__init__(*args, **kwargs)

        self.url = "https://api.openalex.org/authors"


class Venues(BaseOpenAlex):

    def __init__(self, *args, **kwargs):
        super(Venues, self).__init__(*args, **kwargs)

        self.url = "https://api.openalex.org/venue"


class Institutions(BaseOpenAlex):

    def __init__(self, *args, **kwargs):
        super(Institutions, self).__init__(*args, **kwargs)

        self.url = "https://api.openalex.org/institution"


class Concepts(BaseOpenAlex):

    def __init__(self, *args, **kwargs):
        super(Concepts, self).__init__(*args, **kwargs)

        self.url = "https://api.openalex.org/concept"

