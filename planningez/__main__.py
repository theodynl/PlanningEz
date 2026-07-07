"""Run the PlanningEz web server: ``python -m planningez``."""

import os
import sys


def main() -> int:
    """Launch the PlanningEz FastAPI server with uvicorn."""
    import uvicorn

    host = os.environ.get("PLANNINGEZ_HOST", "127.0.0.1")
    port = int(os.environ.get("PLANNINGEZ_PORT", "8000"))
    uvicorn.run("planningez.api.app:app", host=host, port=port, reload=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
