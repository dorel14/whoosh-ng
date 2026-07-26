import sys

if sys.version_info[0] >= 3:
    unicode = str  # type: ignore[assignment]
