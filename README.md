# Flask URL Shortener (PostgreSQL + SQLAlchemy)

Simple URL shortener API built with Flask, SQLAlchemy, and PostgreSQL.

## Endpoints

- `GET /` health check
- `POST /shorten` create a short URL
- `GET /<short_code>` redirect to the original URL

## Example Request

```bash
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/some/long/path"}'
```

Example response:

```json
{
  "short_code": "Ab12xY",
  "short_url": "http://localhost:5000/Ab12xY"
}
```

## Environment Variables

- `DATABASE_URL` (required)
  - Format: `postgresql+psycopg://<user>:<password>@<host>:5432/<db>?sslmode=require`
  - Example: `postgresql+psycopg://postgres:password@172.31.90.148:5432/postgres?sslmode=require`
- `BASE_URL` (optional, default `http://localhost:5000`)
  - Local: `http://localhost:5000`
  - EC2 with direct Gunicorn access: `http://ec2-xx-xx-xx-xx.compute-1.amazonaws.com:5000`
- `PORT` (optional, default `5000`)

## Run Locally

```bash
uv sync
export DATABASE_URL="postgresql+psycopg://postgres:password@localhost:5432/url_shortener"
export BASE_URL="http://localhost:5000"
uv run flask --app main init-db
uv run python main.py
```

## Database Commands

```bash
# create tables if missing
uv run flask --app main init-db

# wipe all app tables (asks for confirmation)
uv run flask --app main clean-db

# wipe without prompt
uv run flask --app main clean-db --yes

# wipe and recreate tables in one command
uv run flask --app main clean-db --yes --recreate
```

## EC2 Setup Guide

1. Launch an Ubuntu EC2 instance.
2. In EC2 Security Group inbound rules, allow:
   - `22/tcp` from your IP (SSH)
   - `5000/tcp` from `0.0.0.0/0` (temporary/testing direct Gunicorn access)
   - Later for production, prefer `80` and `443` with Nginx.
3. SSH into EC2 and install dependencies:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

4. Clone project and enter server directory:

```bash
cd ~/aws-url-shortner/server
uv sync
```

5. Set environment variables:

```bash
export DATABASE_URL="postgresql+psycopg://postgres:password@DB_HOST:5432/postgres?sslmode=require"
export BASE_URL="http://ec2-44-211-40-78.compute-1.amazonaws.com:5000"
```

6. Initialize database one time:

```bash
uv run flask --app main init-db
```

7. Start app:

```bash
uv run gunicorn -w 2 -b 0.0.0.0:5000 main:app
```

8. Open in browser:

```text
http://ec2-44-211-40-78.compute-1.amazonaws.com:5000/
```

## Problems Faced and Fixes

1. PostgreSQL authentication failed:
   - Error: `password authentication failed for user "postgres"`
   - Fix: corrected username/password in `DATABASE_URL`.

2. PostgreSQL rejected connection by host / encryption:
   - Error: `no pg_hba.conf entry ... no encryption`
   - Fix: added `?sslmode=require` in `DATABASE_URL` (no `pg_hba.conf` change was needed in this setup).

3. Invalid sslmode value:
   - Error: `invalid sslmode value: "require""`
   - Fix: removed extra quote. Correct value is exactly `sslmode=require`.

4. Duplicate key on startup (`urls_id_seq`) with multiple workers:
   - Cause: parallel Gunicorn workers attempted schema creation at startup.
   - Fix: moved table creation to explicit command `uv run flask --app main init-db`.

5. Site not reachable from internet:
   - Cause: opened `https://.../` (port 443) while app was running on `http://...:5000`.
   - Fix: use `http://<public-dns>:5000/` and ensure EC2 Security Group allows `5000/tcp`.

## Production Note

For production, run Gunicorn behind Nginx and expose only `80/443` publicly. Keep `5000` private if possible.
