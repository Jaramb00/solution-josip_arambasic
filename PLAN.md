# TicketHub — plan rada

FastAPI middleware servis: povlači todo-e s DummyJSON-a, transformira ih u
vlastiti `Ticket` model i sprema u lokalnu bazu. Svi endpointi rade nad
lokalnom bazom, ne nad živim pozivom prema izvoru.

Stack: Python 3.11 · FastAPI · httpx · pydantic · SQLAlchemy 2 (async) ·
Alembic · pytest. SQLite (dev), opcionalno PostgreSQL.

## Faze

- [ ] **1. Temelji** — scaffold, config, async database, `Ticket` model, Alembic migracija
- [ ] **2. Sync** — DummyJSON klijent, transformacija polja, punjenje baze na startupu
- [ ] **3. Read endpointi** — paginirana lista, detalji, filtriranje, pretraga
- [ ] **4. Write endpointi** — POST + PATCH (validacija, perzistencija kroz restart)
- [ ] **5. Nice-to-have** — /stats, JWT auth, caching, rate limiting, logiranje, health-check, background sync
- [ ] **6. Isporuka** — Docker, CI, README, statička OpenAPI dokumentacija

## Prioritizacija

Obavezno prvo (faze 1–4 + testovi uz svaku fazu), nice-to-have redom dok ima
vremena. Testovi se pišu uz feature, ne na kraju