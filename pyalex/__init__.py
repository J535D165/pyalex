try:
    from pyalex._version import __version__
    from pyalex._version import __version_tuple__
except ImportError:
    __version__ = "0.0.0"
    __version_tuple__ = (0, 0, 0)

from pyalex.api import Authors
from pyalex.api import Concepts
from pyalex.api import Institutions
from pyalex.api import Journals
from pyalex.api import People
from pyalex.api import Venues
from pyalex.api import Works
from pyalex.api import invert_abstract

__all__ = [
    "Works",
    "Authors",
    "Venues",
    "Institutions",
    "Concepts",
    "People",
    "Journals",
    "invert_abstract",
]
