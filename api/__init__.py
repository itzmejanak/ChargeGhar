from __future__ import annotations

import os

try:
    _version = (
        os.popen("git describe --tags --dirty --always")  # noqa: S605, S607
        .read()
        .strip()
    )
except Exception:  # noqa: BLE001
    _version = "0.0.0"

__version__ = _version

# Note: django.setup() should NOT be called here as it causes circular imports
# Django setup is handled automatically by management commands and WSGI/ASGI applications
# If you need Django setup in standalone scripts, call it explicitly in those scripts
