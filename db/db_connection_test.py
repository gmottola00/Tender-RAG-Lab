#!/usr/bin/env python3
"""DB connection tester.

Loads environment variables (supports .env via python-dotenv if installed),
parses DATABASE_URL, performs DNS resolution on the host, and attempts to
connect using asyncpg and SQLAlchemy async engine (if available).

Logs go to stdout and to logs/db_test.log (rotating file handler).
"""
from __future__ import annotations

import asyncio
import logging
import os
import socket
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv, find_dotenv
except Exception:
    load_dotenv = None
    find_dotenv = None

try:
    import asyncpg  # type: ignore
except Exception:
    asyncpg = None

try:
    from sqlalchemy.ext.asyncio import create_async_engine
except Exception:
    create_async_engine = None


LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "db_test.log")


def setup_logging() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("db_test")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)

        fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=2)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


logger = setup_logging()


def mask_secret(s: Optional[str], left: int = 2, right: int = 2) -> str:
    if s is None:
        return "<none>"
    s = str(s)
    if len(s) <= left + right:
        return "*" * len(s)
    return s[:left] + "*" * max(0, len(s) - left - right) + s[-right:]


def load_env() -> None:
    """Load .env if python-dotenv is available and .env exists in project root."""
    if find_dotenv and load_dotenv:
        path = find_dotenv()
        if path:
            load_dotenv(path)
            logger.info("Loaded .env from: %s", path)
        else:
            logger.info("No .env file found automatically; using environment variables")
    else:
        logger.debug("python-dotenv not available; skipping .env auto-load")


def parse_database_url(dsn: Optional[str]) -> Optional[Dict[str, Any]]:
    if not dsn:
        return None
    # Normalize: asyncpg expects scheme without +asyncpg, SQLAlchemy may use +asyncpg
    normalized = dsn.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(normalized)
    query = parse_qs(parsed.query)
    return {
        "raw": dsn,
        "normalized": normalized,
        "scheme": parsed.scheme,
        "username": parsed.username,
        "password": parsed.password,
        "hostname": parsed.hostname,
        "port": parsed.port,
        "database": parsed.path[1:] if parsed.path else "",
        "query": query,
    }


async def asyncpg_test(parsed: Dict[str, Any]) -> bool:
    if asyncpg is None:
        logger.warning("asyncpg not installed; skipping asyncpg test")
        return False

    dsn = parsed["normalized"]
    logger.info("Testing asyncpg.connect() with normalized dsn (scheme removed +asyncpg)")
    try:
        conn = await asyncpg.connect(dsn)
        await conn.close()
        logger.info("asyncpg: connection OK")
        return True
    except Exception:
        logger.exception("asyncpg: connection failed")
        return False


async def sqlalchemy_test(parsed: Dict[str, Any]) -> bool:
    if create_async_engine is None:
        logger.warning("SQLAlchemy async engine not available; skipping SQLAlchemy test")
        return False

    url = parsed["raw"]
    # Ensure SQLAlchemy has +asyncpg in scheme
    if parsed.get("scheme") == "postgresql" and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    logger.info("Testing SQLAlchemy async engine with URL (scheme may include +asyncpg)")
    try:
        engine = create_async_engine(url, echo=False, connect_args={"statement_cache_size": 0})
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        await engine.dispose()
        logger.info("SQLAlchemy async engine: connection OK")
        return True
    except Exception:
        logger.exception("SQLAlchemy async engine: connection failed")
        return False


async def run_tests() -> int:
    load_env()
    dburl = os.getenv("DATABASE_URL")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    logger.info("Starting DB connection test")
    logger.info("SUPABASE_URL: %s", mask_secret(supabase_url, left=8, right=4))
    logger.info("SUPABASE_KEY: %s", mask_secret(supabase_key, left=3, right=3))
    logger.info("DATABASE_URL present: %s", "yes" if dburl else "no")

    parsed = parse_database_url(dburl)
    if not parsed:
        logger.error("DATABASE_URL missing or invalid; aborting tests")
        return 1

    logger.info("Parsed DATABASE_URL: scheme=%s hostname=%s port=%s db=%s",
                parsed.get("scheme"), parsed.get("hostname"), parsed.get("port"), parsed.get("database"))

    host = parsed.get("hostname")
    port = parsed.get("port") or 5432
    if not host:
        logger.error("No hostname parsed from DATABASE_URL (this will cause socket.gaierror)")
        return 1

    # DNS resolution
    try:
        logger.info("Resolving host %s:%s...", host, port)
        addrs = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        logger.info("DNS resolution OK: found %s addresses (showing up to 3)", len(addrs))
        for i, a in enumerate(addrs[:3], start=1):
            logger.info("  %d: %s", i, a)
    except socket.gaierror:
        logger.exception("DNS resolution failed (socket.gaierror)")
        return 1
    except Exception:
        logger.exception("Unexpected DNS resolution error")
        return 1

    # Connection tests
    ok_asyncpg = await asyncpg_test(parsed)
    ok_sqla = await sqlalchemy_test(parsed)

    if ok_asyncpg or ok_sqla:
        logger.info("At least one connection test succeeded")
        return 0
    logger.error("All connection tests failed")
    return 1


def main() -> int:
    code = asyncio.run(run_tests())
    if code == 0:
        logger.info("DB connection test finished: SUCCESS")
    else:
        logger.error("DB connection test finished: FAILURE (exit code %s)", code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
