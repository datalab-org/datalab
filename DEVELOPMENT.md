# Development

Hot-reloading datalab stack (API + web app + MongoDB) in Docker. Only Docker is required.

## Quick start

```bash
cp pydatalab/.env.example pydatalab/.env     # backend config (edit it, see below)
cp webapp/.env.example webapp/.env           # web app config

docker compose --profile dev up --build      # first run builds; later just `up`
docker compose exec api-dev /opt/.venv/bin/invoke dev.seed   # optional: spawn example data in the DB
```

- Web app: http://localhost:8081
- API: http://localhost:5001
- Database: `mongodb://localhost:27018`

Edits to `pydatalab/` and `webapp/` hot-reload. Editing `.env` does not — restart the
service: `docker compose --profile dev restart api-dev` (or `app-dev`).

## Logging in

The web app needs a logged-in session. Set up GitHub OAuth once:

1. Create an OAuth App at https://github.com/settings/developers
   - Homepage URL: `http://localhost:8081`
   - Authorization callback URL: `http://localhost:5001/login/github/authorized`
2. Put the credentials in `pydatalab/.env` (see the commented GitHub block in
   `.env.example`), set `PYDATALAB_TESTING=false`, restart `api-dev`.
3. Set `PYDATALAB_SECRET_KEY` to a real value (generate one with
   `python3 -c 'import secrets; print(secrets.token_hex(64))'`).
4. **Login via GitHub** in the web app.


## Handy commands

```bash
# Make yourself admin (display name = the name shown in the web app)
docker compose exec api-dev /opt/.venv/bin/invoke admin.change-user-role \
  --display-name "Your Name" --role admin

docker compose logs -f api-dev          # follow API logs
docker compose --profile dev down       # stop (add -v to wipe the DB + files)

# Use a custom database name (default: datalabvue). Set in your shell before
# running `docker compose up` — it is not read from pydatalab/.env.
export DATALAB_DB_NAME=my_project
docker compose --profile dev up
```

Backend tests run natively (the Docker dev image ships without test deps); from
`pydatalab/` use `uv sync --all-extras --dev` once, then `uv run pytest`.


## `dev` vs `prod` profiles

Both profiles are in `docker-compose.yml` and share the same Dockerfiles; the `dev`
services target earlier build stages and override the run command.

| | `prod` (`app`, `api`, `database`) | `dev` (`app-dev`, `api-dev`, `database-dev`) |
|---|---|---|
| Code | baked into the image at build time | bind-mounted from your checkout |
| Reload | none (rebuild to change code) | hot reload (Flask `--reload`, Vue HMR) |
| Server | gunicorn / static build | dev servers (`dev.serve`, `vue-cli-service serve`) |
| Database | host path `/data/db`, port not exposed | Docker volume, port `27018`, isolated per dev |
| Files/backups | mounted host paths under `/data` | a throwaway Docker volume |
| Restart policy | `unless-stopped` | none |

Run with `docker compose --profile prod up` or `--profile dev up`. Don't run both at
once — they share ports 5001/8081.
