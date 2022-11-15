<p align="center">
  <img alt="OpenAlex" src="https://github.com/J535D165/openalex/raw/main/openalex_repocard.svg">
</p>

# PyAlex

PyAlex is a Python library for the OpenAlex. It makes use of OpenAlex's
extensive REST API. This Python library tries to stick as close as possible
to the format of the original API. Not all components are documented, as
things are often intuitive when looking at the REST API documentation.

The following features of the OpenAlex REST API are currently supported:

- [x] Get single entities
- [x] Filter entities
- [x] Search entities
- [x] Group entities
- [x] Search filters
- [x] Pagination
- [ ] [Autocomplete endpoint](https://docs.openalex.org/api/autocomplete-endpoint)
- [ ] [N-grams](https://docs.openalex.org/api/get-n-grams)

## Principles

## Installation

PyAlex requires Python 3.6 or later.

```sh
pip install pyalex
```

## Getting started

PyAlex offers support for all [Entity Objects](https://docs.openalex.org/about-the-data#entity-objects).

```python
from pyalex import Works, Authors, Venues, Institutions, Concepts
```

### Get single entities

Get a single Work, Author, Venue, Institution or Concept from OpenAlex via the
class

```python


Works("W2741809807").get()
```

### Get lists of entities

For list of enities, you can return the result as well as the metadata. By default, only the results are returned.

```python
meta, results = Concepts().get(return_meta=True)
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

### Pagination

#### Per page

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
    m, r = query.get(return_meta=True, per_page=200, page=page)

    # results
    results.append(r)

    page = m["page"] + 1 if page is not None else None
```

#### Cursor

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
    m, r = query.get(return_meta=True, per_page=200, cursor=next_cursor)

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

### Get random

Get a [random Work, Author, Venue, Institution or Concept](https://docs.openalex.org/api/get-single-entities#random-entity).

```python
Works().random()
```

## Tutorial



## License

[MIT](/LICENSE)

## Contact

Feel free to reach out with questions, remarks, and suggestions. The
[issue tracker](/issues) is a good starting point. You can also email me at
[jonathandebruinos@gmail.com](mailto:jonathandebruinos@gmail.com).
