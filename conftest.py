"""Root-level conftest.py — ensures local packages are importable.

When mutmut copies the project to a ``mutants/`` subdirectory and runs
tests from there, Python doesn't automatically add the working directory
to ``sys.path``.  This conftest.py fixes that by inserting the project
root (the directory containing this file) at the front of ``sys.path``.
"""

import sys
from pathlib import Path

# conftest.py is loaded by pytest before any test collection, so this
# runs early enough to fix imports for all test modules.
_root = str(Path(__file__).parent.resolve())
if _root not in sys.path:
    sys.path.insert(0, _root)
