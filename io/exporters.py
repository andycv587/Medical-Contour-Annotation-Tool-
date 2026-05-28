"""Compatibility file requested by the publication packaging plan.

Python's standard-library `io` module shadows this directory for normal imports.
Use `contour_io.exporters` in code.
"""

from contour_io.exporters import *  # noqa: F401,F403
