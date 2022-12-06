<p align="center">
  <img alt="PyAlex - a Python wrapper for OpenAlex" src="https://github.com/J535D165/pyalex/raw/main/pyalex_repocard.svg">
</p>

# PyAlex

PyAlex is a Python library for [OpenAlex](https://openalex.org/). OpenAlex is
an index of hundreds of millions of interconnected scholarly papers, authors,
institutions, and more.

PyAlex follows the format of the [OpenAlex REST API]
(https://docs.openalex.org/). Not all components of PyAlex are documented, as
the use of PyAlex is often intuitive when looking at the REST API
documentation.

The following features of the OpenAlex REST API are currently supported by
PyAlex:

- [x] Get single entities
- [x] Filter entities
- [x] Search entities
- [x] Group entities
- [x] Search filters
- [x] Pagination
- [ ] [Autocomplete endpoint](https://docs.openalex.org/api/autocomplete-endpoint)
- [x] N-grams

We aim to cover the entire API and we are looking for help. We are welcoming Pull Requests. 

## Key features

- **Plaintext abstracts** - OpenAlex [doesn't include plaintext abstracts](https://docs.openalex.org/about-the-data/work#abstract_inverted_index) due to legal constraints. PyAlex converts the inverted abstracts into plaintext abstracts on the fly.
- **Pipe operations** - PyAlex can handle multiple operations in a seqence. This allows the developer to write understandable queries. For examples, see [code snippets](#code-snippets).
- **Permissive license** - OpenAlex data is CC0 licensed :raised_hands:. PyAlex is published under the MIT license.

## Installation

PyAlex requires Python 3.6 or later.

```sh
pip install pyalex
```

## Getting started

PyAlex offers support for all [Entity Objects]
(https://docs.openalex.org/about-the-data#entity-objects).

```python
from pyalex import Works, Authors, Venues, Institutions, Concepts
```

### Get single entities

Get a single Work, Author, Venue, Institution or Concept from OpenAlex via the
class

```python
Works()["W2741809807"]
```

### Get lists of entities

For list of enities, you can return the result as well as the metadata. By default, only the results are returned.

```python
results, meta = Concepts().get(return_meta=True)
print(meta)
```

```python
{'count': 65073, 'db_response_time_ms': 16, 'page': 1, 'per_page': 25}
```

### Filter records

```python
Works().filter(publication_year=2020, is_oa=True).get()
```

which is identical to:

```python
Works().filter(publication_year=2020).filter(is_oa=True).get()
```

#### Nested attribute filters

Some attribute filers are nested and separated with dots by OpenAlex. For
example, filter on [`authorships.institutions.ror`]
(https://docs.openalex.org/api/get-lists-of-entities/filter-entity-lists#works-attribute-filters).

In case of nested attribute filters, use a dict to built the query.

```python
Works()
  .filter(authorships={"institutions": {"ror": "04pp8hn57"}})
  .get()
```

### Search entities

[The search parameter](https://docs.openalex.org/api/get-lists-of-entities/search-entity-lists#the-search-parameter)

```python
Works().search("fierce creatures").get()
```

### Paging

OpenAlex offers two methods for paging: [basic paging](https://docs.openalex.org/api#basic-paging) and [cursor paging](https://docs.openalex.org/api#cursor-paging). Both methods are supported by
PyAlex, although it is STRONGLY ADVISED to use cursor paging. Cursor paging
is easier to implement and less error-prone.

#### Basic paging

See limitations of [basic paging](https://docs.openalex.org/api#basic-paging) on OpenAlex API documentation.
Cursor paging is probably a better solution to implement.

```python
from openalex import Authors

# example query
query = Authors().search_filter(display_name="einstein")

# set the page
page = 1

# store the results
results = []

# loop till page is None
while page is not None:

    # get the results
    r, m = query.get(return_meta=True, per_page=200, page=page)

    # results
    results.append(r)

    page = m["page"] + 1 if page is not None else None
```

#### Cursor paging

```python
from openalex import Authors

# example query
query = Authors().search_filter(display_name="einstein")

# set the next_cursor (to *)
next_cursor = "*"

# store the results
results = []

# loop till next_cursor is None
while next_cursor is not None:

    # get the results
    r, m = query.get(return_meta=True, per_page=200, cursor=next_cursor)

    # results
    results.extend(r)

    # set the next cursor
    next_cursor = m["next_cursor"]
```

### Search filter

[The search filter](https://docs.openalex.org/api/get-lists-of-entities/search-entity-lists#the-search-filter)

```python
Authors().search_filter(display_name="einstein").get()
```

```python
Works().search_filter(title="cubist").get()
```

### Sort entity lists

See [Sort entity lists](https://docs.openalex.org/api/get-lists-of-entities/sort-entity-lists).

```python
Works().sort(cited_by_count="desc").get()
```

### Get N-grams

See [Get N-grams](https://docs.openalex.org/api/get-n-grams).


```python
Works()["W2023271753"].ngrams()
```

### Get random

Get a [random Work, Author, Venue, Institution or Concept](https://docs.openalex.org/api/get-single-entities#random-entity).

```python
Works().random()
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
