"""Refresh the bundled extensions to the latest GitHub releases.

Thin dev wrapper: the download logic lives in hatch_build.py, where the
hatchling build hook reuses it at wheel-build time.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch_build import EXTENSIONS_DIR, download_extensions  # noqa: E402


def main() -> int:
    download_extensions(EXTENSIONS_DIR, force=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
