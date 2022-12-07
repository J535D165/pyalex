try:
    from pyalex._version import __version__
    from pyalex._version import __version_tuple__
except ImportError:
    __version__ = "0.0.0"
    __version_tuple__ = (0, 0, 0)

from pyalex.api import Author
from pyalex.api import Authors
from pyalex.api import Concept
from pyalex.api import Concepts
from pyalex.api import Institution
from pyalex.api import Institutions
from pyalex.api import Journals
from pyalex.api import People
from pyalex.api import Venue
from pyalex.api import Venues
from pyalex.api import Work
from pyalex.api import Works
from pyalex.api import config
from pyalex.api import invert_abstract

__all__ = [
    "Works",
    "Work",
    "Authors",
    "Author",
    "Venues",
    "Venue",
    "Institutions",
    "Institution",
    "Concepts",
    "Concept",
    "People",
    "Journals",
    "config",
    "invert_abstract",
]
