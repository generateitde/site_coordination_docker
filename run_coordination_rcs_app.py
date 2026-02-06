"""Run the coordination dashboard locally."""

import os

from site_coordination.coordination_app import create_app


def _debug_enabled() -> bool:
    return os.environ.get("SITE_COORDINATION_DEBUG", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=_debug_enabled())
