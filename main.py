import os
import secrets
import string
from datetime import datetime, timezone
from urllib.parse import urlparse

import click
from flask import Flask, jsonify, redirect, request
from sqlalchemy import DateTime, String, Text, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class URL(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    short_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Example: postgresql+psycopg://user:password@host:5432/dbname"
        )
    return database_url


def create_app() -> Flask:
    app = Flask(__name__)
    engine = create_engine(get_database_url(), pool_pre_ping=True)

    @app.get("/")
    def health() -> dict[str, str]:
        return {"message": "URL shortener is running"}

    @app.post("/shorten")
    def shorten_url():
        payload = request.get_json(silent=True) or {}
        original_url = (payload.get("url") or "").strip()

        if not is_valid_url(original_url):
            return jsonify({"error": "Provide a valid URL including http:// or https://"}), 400

        with Session(engine) as session:
            # Reuse existing short URL for same original URL.
            existing = session.query(URL).filter_by(original_url=original_url).first()
            if existing:
                return jsonify(build_shortened_response(existing.short_code))

            new_url = URL(original_url=original_url, short_code=generate_short_code())
            session.add(new_url)

            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                # Very unlikely collision, retry once with a new code.
                new_url.short_code = generate_short_code()
                session.add(new_url)
                session.commit()

            return jsonify(build_shortened_response(new_url.short_code)), 201

    @app.get("/<short_code>")
    def resolve_short_url(short_code: str):
        with Session(engine) as session:
            url = session.query(URL).filter_by(short_code=short_code).first()
            if not url:
                return jsonify({"error": "Short URL not found"}), 404
            return redirect(url.original_url, code=302)

    return app


def build_shortened_response(short_code: str) -> dict[str, str]:
    base_url = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
    return {"short_code": short_code, "short_url": f"{base_url}/{short_code}"}


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def generate_short_code(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


app = create_app()


@app.cli.command("init-db")
def init_db_command() -> None:
    engine = create_engine(get_database_url(), pool_pre_ping=True)
    Base.metadata.create_all(engine)
    print("Database initialized.")


@app.cli.command("clean-db")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--recreate", is_flag=True, help="Recreate tables after cleanup.")
def clean_db_command(yes: bool, recreate: bool) -> None:
    if not yes and not click.confirm("This will delete all URL data. Continue?"):
        click.echo("Aborted.")
        return

    engine = create_engine(get_database_url(), pool_pre_ping=True)
    Base.metadata.drop_all(engine)

    if recreate:
        Base.metadata.create_all(engine)
        click.echo("Database cleaned and recreated.")
        return

    click.echo("Database cleaned.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
