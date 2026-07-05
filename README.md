# TicketHub

[![CI](https://github.com/Jaramb00/solution-josip_arambasic/actions/workflows/ci.yml/badge.svg)](https://github.com/Jaramb00/solution-josip_arambasic/actions)

Middleware REST servis (FastAPI) koji prikuplja, pohranjuje i izlaže "support
tickete" iz vanjskog izvora (DummyJSON). Svi read/write endpointi rade nad
lokalnom bazom, a ne nad živim pozivom prema izvoru.

> Plan rada po fazama: [PLAN.md](PLAN.md)

## Tehnološki stack

Python 3.11 · FastAPI 0.111 · httpx 0.27 · pydantic 2.7 · SQLAlchemy 2.x (async) ·
Alembic · pytest · slowapi · PyJWT. Baza: SQLite (default) ili PostgreSQL.

## Model podataka

DummyJSON `todo` se transformira u `Ticket`:

| Ticket polje | Izvor |
|--------------|-------|
| `id`         | `todo.id` |
| `title`      | `todo.todo` |
| `status`     | `closed` ako `completed == true`, inače `open` |
| `priority`   | `id % 3` → `low` / `medium` / `high` |
| `assignee`   | `username` razriješen preko `userId` |
| `source`     | puni originalni JSON iz izvora |

## Postavljanje okruženja

```bash
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements-dev.txt
```

## Konfiguracija (env varijable)

Sve varijable imaju prefiks `TICKETHUB_` i mogu se zadati kroz `.env`
(predložak: `.env.example`). Sve imaju razumne defaulte — projekt radi
out-of-the-box.

| Varijabla | Default | Opis |
|-----------|---------|------|
| `TICKETHUB_DATABASE_URL` | `sqlite+aiosqlite:///./tickethub.db` | Async SQLAlchemy URL |
| `TICKETHUB_DUMMYJSON_BASE_URL` | `https://dummyjson.com` | Vanjski izvor |
| `TICKETHUB_HTTP_TIMEOUT` | `20.0` | HTTP timeout prema izvoru (s) |
| `TICKETHUB_SYNC_ON_STARTUP` | `true` | Napuni bazu na startupu ako je prazna |
| `TICKETHUB_SYNC_INTERVAL_SECONDS` | `0` | Pozadinski sync interval (0 = isključeno) |
| `TICKETHUB_CACHE_TTL_SECONDS` | `30` | TTL in-memory cachea za `/stats` |
| `TICKETHUB_JWT_SECRET` | `change-me-in-production` | Tajni ključ za potpis JWT-a |
| `TICKETHUB_JWT_ALGORITHM` | `HS256` | Algoritam potpisa |
| `TICKETHUB_JWT_EXPIRE_MINUTES` | `60` | Trajanje tokena (min) |
| `TICKETHUB_RATE_LIMIT` | `120/minute` | Globalni rate limit (slowapi) |
| `TICKETHUB_LOG_LEVEL` | `INFO` | Razina logiranja |

Za produkciju generirajte vlastiti JWT secret, npr.:
`python -c "import secrets; print(secrets.token_hex(32))"`

## Pokretanje

```bash
# 1. Migracije sheme
alembic upgrade head

# 2. Server (na startupu puni bazu iz izvora ako je prazna)
python main.py
# ili s auto-reloadom:
uvicorn tickethub.main:app --reload --app-dir src
```

Servis je na http://127.0.0.1:8000 — interaktivna OpenAPI dokumentacija:
http://127.0.0.1:8000/docs

S Makefileom (Linux/macOS/Git Bash): `make install`, `make run`, `make lint`,
`make test`, `make docs`, `make docker-build`, `make docker-up`, `make docker-down`.

### Docker

```bash
docker compose up --build
```

Migracije se primjenjuju automatski na startu kontejnera. SQLite baza živi u
imenovanom volumenu (`tickethub-data`) pa podaci i izmjene preživljavaju
restart kontejnera.

### Statička API dokumentacija

Generirana Redoc dokumentacija: [`docs/index.html`](docs/index.html) (otvara se
lokalno u browseru, bez servera) — online verzija (GitHub Pages):
https://jaramb00.github.io/solution-josip_arambasic/

Regeneriranje: `python scripts/export_openapi.py` ili `make docs`.

## API pregled

| Metoda | Putanja | Auth | Opis |
|--------|---------|------|------|
| GET | `/tickets` | — | Paginirana lista; filtri `status`, `priority`; `limit`/`offset` |
| GET | `/tickets/search?q=` | — | Pretraga po nazivu (case-insensitive) |
| GET | `/tickets/{id}` | — | Detalji + puni JSON iz izvora |
| POST | `/tickets` | JWT | Kreiranje ticketa (validacija ulaza) |
| PATCH | `/tickets/{id}` | JWT | Izmjena (status/priority/assignee); preživljava restart |
| GET | `/stats` | — | Agregirane statistike (keširano, TTL) |
| POST | `/auth/login` | — | Prijava preko DummyJSON-a → izdaje JWT |
| POST | `/sync` | JWT | Ručno osvježavanje podataka iz izvora (upsert) |
| GET | `/health` | — | Health-check (k8s/Compose) |

### Autentifikacija — brzi start

Write endpointi zahtijevaju `Authorization: Bearer <token>`. Token se dobiva
prijavom s kredencijalima bilo kojeg [DummyJSON korisnika](https://dummyjson.com/users)
(lozinka je `{username}pass`), npr. `emilys` / `emilyspass`:

```bash
# 1. Login
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "emilys", "password": "emilyspass"}'
# -> {"access_token": "<TOKEN>", "token_type": "bearer"}

# 2. Zaštićeni poziv
curl -s -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"title": "Novi ticket", "priority": "high"}'
```

U Swaggeru (`/docs`): login → kopiraj token → gumb **Authorize**.

## Testovi i lint

```bash
pytest -q      # 33 testa (unit + integracijski; bez mrežnih poziva)
ruff check .   # PEP-8 stil (line-length 100), isort, bugbear
```

CI (GitHub Actions) na svaki push izvršava: ruff → alembic upgrade head → pytest.

## Struktura projekta

```
tickethub/
├── src/tickethub/
│   ├── main.py            # FastAPI app, lifespan, middleware
│   ├── config.py          # pydantic-settings (env varijable)
│   ├── database.py        # async engine + session dependency
│   ├── models.py          # SQLAlchemy Ticket model
│   ├── schemas.py         # pydantic modeli (ulaz/izlaz)
│   ├── auth.py            # JWT (login preko DummyJSON-a, provjera tokena)
│   ├── cache.py           # in-memory TTL cache
│   ├── crud.py            # upiti nad bazom
│   ├── routers/           # tickets, stats, auth, admin (/sync)
│   └── services/          # dummyjson klijent, sync (upsert)
├── tests/                 # pytest (fixtures u conftest.py)
├── alembic/               # migracije sheme
├── scripts/               # export_openapi.py (redoc-static)
├── .github/workflows/     # CI
├── Dockerfile / docker-compose.yml / Makefile
└── README.md / PLAN.md
```

## Dizajnerske odluke

- **`description` u listi** — izvor nema polje opisa, pa se koristi naslov
  skraćen na ≤ 100 znakova.
- **Sync = upsert** (dialect-aware, SQLite/PostgreSQL) — osvježava polja iz
  izvora, ne briše lokalno kreirane tickete; zato PATCH izmjene i ručno dodani
  ticketi preživljavaju restart.
- **JWT HS256** — servis sam izdaje i provjerava tokene, pa je simetrični ključ
  dovoljan. Write endpointi su namjerno zaštićeni; token je trivijalno dobiti.
- **In-memory cache i rate limit** — dovoljni za jednu instancu; za više
  instanci prirodna nadogradnja je Redis.

## Korištenje AI alata

Projekt je razvijan uz pomoć AI asistenta (Claude), korištenog kao vodič i
pair-programmer. Budući da s dijelom ovih tehnologija (async SQLAlchemy,
Alembic, pytest) nemam puno praktičnog iskustva, AI sam koristio da svaki
korak napravim ispravno i da mi ništa ne ostane nejasno.
AI je korišten za:

- **Planiranje i scaffold** — razrada plana rada (PLAN.md), redoslijed
  feature-based commitova i početna struktura projekta (src/tests/ci layout,
  ruff/pytest konfiguracija)
- **Objašnjavanje tehnika prije implementacije** — async SQLAlchemy (engine,
  sesije, expire_on_commit), Alembic migracije, FastAPI dependency injection,
  pydantic validacija, JWT/HMAC, upsert, TTL caching, asyncio background taskovi
- **Pomoć i objašnjenja kroz cijeli razvoj** — pisanje i pregled koda, struktura
  testova (fixtures, monkeypatch, parametrize) i rubni slučajevi, Docker/CI setup
- **Debugging** — čitanje traceback-ova (ImportError/NameError), okolišni
  problemi na Windowsu (venv aktivacija, PowerShell execution policy, encoding),
  dijagnoza 404/403 kroz test logove

Sav kod je pregledan, testiran (pytest) i lintan (ruff) prije svakog commita.

**Primjeri promptova**:

> „Dodaj pozadinski sync job koji periodički osvježava podatke iz izvora:
> asyncio task pokrenut kroz lifespan, interval konfigurabilan env varijablom
> (0 = isključeno), job ne smije srušiti aplikaciju ako vanjski API padne i
> mora se uredno ugasiti (CancelledError) pri gašenju servera. Objasni i kako
> testirati beskonačnu petlju."

> „Implementiraj /stats endpoint s in-memory TTL cacheom bez vanjskih ovisnosti:
> GROUP BY agregacija u bazi, konfigurabilan TTL, invalidacija cachea na svaki
> write (POST/PATCH/sync). Objasni zašto time.monotonic umjesto time.time i
> kada bi ovo trebalo zamijeniti Redisom."

> „Dodaj globalni rate limiting (slowapi) s limitom iz env varijable i
> middleware koji logira svaki request (metoda, putanja, status, trajanje;
> WARNING za statuse >= 400)."

> „Objasni mi detaljno kako napisati testove za ovaj projekt koristeći pytest.
> Nemoj samo generirati kod, nego objasni svaki korak i razlog zašto se nešto
> radi. Posebno objasni: ulogu conftest.py i kako rade fixturei; kako napraviti
> izoliranu SQLite test bazu za svaki test; korištenje httpx.AsyncClient i
> ASGITransport bez pokretanja pravog servera; kako radi
> app.dependency_overrides i zašto se koristi; pytest-asyncio i pisanje
> asinkronih testova; pytest.mark.parametrize za testiranje više ulaza;
> monkeypatch za mockiranje DummyJSON API-ja kako testovi ne bi ovisili o
> internetu; autouse fixture za čišćenje globalnog cachea; kako testirati JWT
> autentifikaciju generiranjem tokena direktno, bez pozivanja login endpointa.
> Za svaki feature projekta napiši primjer testa i objasni ga redak po redak.
> Uključi i testove za rubne slučajeve poput: 404 Not Found, 422 Validation
> Error, prazan PATCH zahtjev, nepostojeći korisnik, neispravan JWT, prazni
> rezultati pretrage. Pretpostavi da sam početnik u pytestu i želim razumjeti
> svaki dio koda, a ne samo kopirati rješenje."