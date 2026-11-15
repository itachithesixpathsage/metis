# Project Métis

Project Métis is a quantitative FX research and portfolio risk platform. This repository contains a React dashboard, a FastAPI service, and a TimescaleDB-backed development environment. The current API provides health and readiness checks; the dashboard pages are the starting point for research and risk workflows.

## Quick start

Run the full development stack with Docker Compose (Docker Compose v2):

```bash
cp .env.example .env
docker compose up --build
```

Then open the dashboard at [http://localhost:5173](http://localhost:5173). The API is at [http://localhost:8000](http://localhost:8000), with interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs). The database is exposed on port `5432`.

To stop the services, run `docker compose down`. Add `-v` to remove the database volume and its data.

## Local development

Requirements: Python 3.12+, Node.js 22+, and a PostgreSQL/TimescaleDB instance.

1. Copy `.env.example` to `.env` and set database connection values.
2. Install the backend and development dependencies, then start the API:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e '.[dev]'
   uvicorn metis.api:create_app --factory --reload
   ```

3. In another terminal, start the frontend:

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

The frontend dev server runs at `http://localhost:5173`; the backend listens on `http://localhost:8000`.

## Configuration and endpoints

Application settings use `METIS_` environment variables. See `.env.example` for database, API, simulation, market data, and logging defaults. The API uses the `/api/v1` prefix:

- `GET /api/v1/health` — basic service status
- `GET /api/v1/ready` — service and database readiness

## Project layout

- `src/metis/` — FastAPI application, settings, database setup, and models
- `alembic/` — database migration configuration and revisions
- `frontend/src/` — React dashboard and pages
- `tests/` — backend unit tests
- `docker/` and `docker-compose.yml` — container build and local stack configuration

## Development checks

Run backend tests from the repository root:

```bash
pytest
```

Run frontend checks from `frontend/`:

```bash
npm run lint
npm run build
```
