"""Compatibility file requested by the publication packaging plan.

Python's standard-library `io` module shadows this directory for normal imports.
Use `contour_io.importers` in code.
"""

from contour_io.importers import *  # noqa: F401,F403
