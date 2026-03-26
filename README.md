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
  - Example: `postgresql+psycopg://postgres:password@localhost:5432/url_shortener`
- `BASE_URL` (optional, default `http://localhost:5000`)
  - Set this to your EC2 domain/IP when deploying.
- `PORT` (optional, default `5000`)

## Run Locally

```bash
uv sync
export DATABASE_URL="postgresql+psycopg://postgres:password@localhost:5432/url_shortener"
export BASE_URL="http://localhost:5000"
uv run python main.py
```

## EC2 Deployment Notes

1. Install Python 3.11+, PostgreSQL client libs, and `uv` (or use pip).
2. Set environment variables (`DATABASE_URL`, `BASE_URL`, `PORT`) on your EC2 instance.
3. Run with Gunicorn behind Nginx for production:

```bash
uv add gunicorn
uv run gunicorn -w 2 -b 0.0.0.0:5000 main:app
```

4. Open security group inbound rules for your app/Nginx ports.
