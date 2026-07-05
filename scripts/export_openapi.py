"""Izvoz OpenAPI sheme i generiranje statičke Redoc dokumentacije u docs/.

Pokretanje iz roota projekta: python scripts/export_openapi.py
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tickethub.main import app  # noqa: E402

REDOC_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <title>TicketHub — API dokumentacija</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body {{ margin: 0; padding: 0; }}</style>
  </head>
  <body>
    <redoc spec-url="openapi.json"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
  </body>
</html>
"""


def main() -> None:
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)

    (docs / "openapi.json").write_text(
        json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (docs / "index.html").write_text(REDOC_TEMPLATE, encoding="utf-8")
    print(f"OpenAPI dokumentacija generirana u {docs}")


if __name__ == "__main__":
    main()
