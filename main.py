"""Ulazna točka za lokalno pokretanje: `python main.py`.

Za razvoj s auto-reloadom koristi:
`uvicorn tickethub.main:app --reload --app-dir src`.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))

import uvicorn  # noqa: E402

from tickethub.main import app  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
