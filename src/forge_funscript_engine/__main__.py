"""Enable `python -m forge_funscript_engine ...`."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
