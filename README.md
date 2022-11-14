<p align="center">
  <img alt="OpenAlex" src="https://github.com/J535D165/openalex/raw/main/openalex_repocard.svg">
</p>

# PyAlex

PyAlex is a Python library for the OpenAlex. It makes use of OpenAlex's
extensive REST API. This Python library tries to stick as close as possible
to the format of the original API. Not all components are documented, as
things are often intuitive when looking at the REST API documentation.

The following features of the OpenAlex REST API are currently supported:

- [x] Retrieve single Work, Author, Venue, Institution, or Concept
- [x] Filter Works, Authors, Venues, Institutions, or Concepts
- [x] Search Works, Authors, Venues, Institutions, or Concepts
- [x] Group Works, Authors, Venues, Institutions, or Concepts
- [] Search filters

## Principles

## Installation

PyAlex requires Python 3.6 or later.

```sh
pip install pyalex
```

## Getting started

### Single Work, Author, Venue, Institution or Concept

Get a single record from OpenAlex via the class

```python
from pyalex import Work, Authors, Venues, Institutions, Concepts

Works("W4238809453").get()
```

### Filter records

```python
Works().filter(publication_year=2020, is_oa=True).get(return_meta=True)
```

More complex filter queries (the dataset publications of an institute):

```python
Works()
.filter(authorships={"institutions": {"ror": "04pp8hn57"}})
.filter(type="dataset")
.get()
```


## License

[MIT](/LICENSE)

## Contact

Feel free to reach out with questions, remarks, and suggestions. The
[issue tracker](/issues) is a good starting point. You can also email me at
[jonathandebruinos@gmail.com](mailto:jonathandebruinos@gmail.com).
