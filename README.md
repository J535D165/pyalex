<p align="center">
  <img alt="PyAlex - a Python wrapper for OpenAlex" src="https://github.com/J535D165/pyalex/raw/main/pyalex_repocard.svg">
</p>

# PyAlex

![PyPI](https://img.shields.io/pypi/v/pyalex) 

PyAlex is a Python library for [OpenAlex](https://openalex.org/). OpenAlex is
an index of hundreds of millions of interconnected scholarly papers, authors,
institutions, and more. OpenAlex offers a robust, open, and free [REST API](https://docs.openalex.org/) to extract, aggregate, or search scholarly data.
PyAlex is a lightweight and thin Python interface to this API. PyAlex tries to
stay as close as possible to the design of the original service.

The following features of OpenAlex are currently supported by PyAlex:

- [x] Get single entities
- [x] Filter entities
- [x] Search entities
- [x] Group entities
- [x] Search filters
- [x] Pagination
- [ ] [Autocomplete endpoint](https://docs.openalex.org/api/autocomplete-endpoint)
- [x] N-grams

We aim to cover the entire API, and we are looking for help. We are welcoming Pull Requests.

## Key features

- **Pipe operations** - PyAlex can handle multiple operations in a sequence. This allows the developer to write understandable queries. For examples, see [code snippets](#code-snippets).
- **Plaintext abstracts** - OpenAlex [doesn't include plaintext abstracts](https://docs.openalex.org/about-the-data/work#abstract_inverted_index) due to legal constraints. PyAlex converts the inverted abstracts into [plaintext abstracts on the fly](#get-abstract).
- **Permissive license** - OpenAlex data is CC0 licensed :raised_hands:. PyAlex is published under the MIT license.

## Installation

PyAlex requires Python 3.6 or later.

```sh
pip install pyalex
```

## Getting started

PyAlex offers support for all [Entity Objects (Works, Authors, Venues, Institutions, Concepts)](https://docs.openalex.org/about-the-data#entity-objects).

```python
from pyalex import Works, Authors, Venues, Institutions, Concepts
```

### The polite pool

[The polite pool](https://docs.openalex.org/api#the-polite-pool) has much
faster and more consistent response times. To get into the polite pool, you
set your email:

```python
import pyalex

pyalex.config.email = "mail@example.com"
```

### Get single entity

Get a single Work, Author, Venue, Institution or Concept from OpenAlex by the
OpenAlex ID, or by DOI or ROR.

```python
Works()["W2741809807"]

# same as
Works()["https://doi.org/10.7717/peerj.4375"]
```

The result is a `Work` object, which is very similar to a dictionary. Find the avialable fields with `.keys()`.

For example, get the open access status:

```python
Works()["W2741809807"]["open_access"]
```

```python
{'is_oa': True, 'oa_status': 'gold', 'oa_url': 'https://doi.org/10.7717/peerj.4375'}
```

The previous works also for Authors, Venues, Institutions and Concepts

```python
Authors()["A2887243803"]
Authors()["https://orcid.org/0000-0002-4297-0502"]  # same
```

#### Get random

Get a [random Work, Author, Venue, Institution or Concept](https://docs.openalex.org/api/get-single-entities#random-entity).

```python
Works().random()
Authors().random()
Venues().random()
Institutions().random()
Concepts().random()
```

#### Get abstract

Only for Works. Request a work from the OpenAlex database:

```python
w = Works()["W3128349626"]
```

All attributes are available like documented under [Works](https://docs.openalex.org/about-the-data/work), as well as `abstract` (only if `abstract_inverted_index` is not None).

```python
w["abstract"]
```

```python
'Abstract To help researchers conduct a systematic review or meta-analysis as efficiently and transparently as possible, we designed a tool to accelerate the step of screening titles and abstracts. For many tasks—including but not limited to systematic reviews and meta-analyses—the scientific literature needs to be checked systematically. Scholars and practitioners currently screen thousands of studies by hand to determine which studies to include in their review or meta-analysis. This is error prone and inefficient because of extremely imbalanced data: only a fraction of the screened studies is relevant. The future of systematic reviewing will be an interaction with machine learning algorithms to deal with the enormous increase of available text. We therefore developed an open source machine learning-aided pipeline applying active learning: ASReview. We demonstrate by means of simulation studies that active learning can yield far more efficient reviewing than manual reviewing while providing high quality. Furthermore, we describe the options of the free and open source research software and present the results from user experience tests. We invite the community to contribute to open source projects such as our own that provide measurable and reproducible improvements over current practice.'
```

Please respect the legal constraints when using this feature.

### Get lists of entities

For list of enities, you can return the result as well as the metadata. By default, only the results are returned.

```python
results, meta = Concepts().get(return_meta=True)
print(meta)
```

```python
{'count': 65073, 'db_response_time_ms': 16, 'page': 1, 'per_page': 25}
```

#### Filter records

```python
Works().filter(publication_year=2020, is_oa=True).get()
```

which is identical to:

```python
Works().filter(publication_year=2020).filter(is_oa=True).get()
```

#### Nested attribute filters

Some attribute filers are nested and separated with dots by OpenAlex. For
example, filter on [`authorships.institutions.ror`](https://docs.openalex.org/api/get-lists-of-entities/filter-entity-lists#works-attribute-filters).

In case of nested attribute filters, use a dict to built the query.

```python
Works()
  .filter(authorships={"institutions": {"ror": "04pp8hn57"}})
  .get()
```

#### Search entities

OpenAlex reference: [The search parameter](https://docs.openalex.org/api/get-lists-of-entities/search-entity-lists#the-search-parameter)

```python
Works().search("fierce creatures").get()
```

#### Search filter

OpenAlex reference: [The search filter](https://docs.openalex.org/api/get-lists-of-entities/search-entity-lists#the-search-filter)

```python
Authors().search_filter(display_name="einstein").get()
```

```python
Works().search_filter(title="cubist").get()
```

#### Sort entity lists

OpenAlex reference: [Sort entity lists](https://docs.openalex.org/api/get-lists-of-entities/sort-entity-lists).

```python
Works().sort(cited_by_count="desc").get()
```

#### Paging

OpenAlex offers two methods for paging: [basic paging](https://docs.openalex.org/api#basic-paging) and [cursor paging](https://docs.openalex.org/api#cursor-paging). Both methods are supported by
PyAlex, although cursor paging seems to be easier to implement and less error-prone.

##### Basic paging

See limitations of [basic paging](https://docs.openalex.org/api#basic-paging) in the OpenAlex documentation.
It's relatively easy to implement basic paging with PyAlex, however it is
advised to use the built-in pager based on cursor paging.

##### Cursor paging

Use `paginate()` for paging results. By default, `paginate`s argument `n_max`
is set to 10000. Use `None` to retrieve all results.

```python
from pyalex import Authors

pager = Authors().search_filter(display_name="einstein").paginate(per_page=200)

for page in pager:
    print(len(page))
```

### Get N-grams

OpenAlex reference: [Get N-grams](https://docs.openalex.org/api/get-n-grams).


```python
Works()["W2023271753"].ngrams()
```


## Code snippets

A list of awesome use cases of the OpenAlex dataset.

### Cited publications (referenced works)

```python
from pyalex import Works

# the work to extract the referenced works of
w = Works()["W2741809807"]

Works().filter(openalex_id="|".join(w["referenced_works"])).get()
```

### Dataset publications in the global south

```python
from pyalex import Works

# the work to extract the referenced works of
w = Works() \
  .filter(institutions={"is_global_south":True}) \
  .filter(type="dataset") \
  .group_by("institutions.country_code") \
  .get()

```

### Most cited publications in your organisation

```python
from pyalex import Works

Works() \
  .filter(authorships={"institutions": {"ror": "04pp8hn57"}}) \
  .sort(cited_by_count="desc") \
  .get()

```

Same, but with only for first authors

```python
from pyalex import Works

Works() \
  .filter(authorships={"institutions": {"ror": "04pp8hn57"},
                       "author_position": "first"}) \
  .sort(cited_by_count="desc") \
  .get()

```

## License

[MIT](/LICENSE)

## Contact

Feel free to reach out with questions, remarks, and suggestions. The
[issue tracker](/issues) is a good starting point. You can also email me at
[jonathandebruinos@gmail.com](mailto:jonathandebruinos@gmail.com).
