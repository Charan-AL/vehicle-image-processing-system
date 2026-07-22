"""
Database configuration and session management.
Sets up PostgreSQL connection, session factory, and ORM base class.

Components:
- Engine: Connection pool for PostgreSQL
- SessionLocal: Factory for creating database sessions
- Base: Declarative base for all ORM models
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator

load_dotenv()

# Read database configuration from environment variables
# Format: postgresql://username:password@host:port/database_name
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/vehicle_db"
)

# Create SQLAlchemy engine
# engine_args explanation:
# - create_engine(): Creates a database engine for PostgreSQL
# - echo=True: Prints SQL queries (useful for debugging, disable in production)
# - pool_size=5: Maximum number of connections in the pool
# - max_overflow=10: Additional connections beyond pool_size
# - pool_pre_ping=True: Tests connection before using it (handles stale connections)
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "False") == "True",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

# Create session factory
# sessionmaker() explanation:
# - autocommit=False: Requires explicit commit (safer)
# - autoflush=False: Requires explicit flush (prevents unwanted queries)
# - bind=engine: Binds sessions to the engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base for ORM models
# All database models will inherit from this Base class
Base = declarative_base()


def initialize_database() -> None:
    """Create missing tables and apply the small schema upgrades used by the app."""
    from app.models import AnalysisResult, Image

    Base.metadata.create_all(bind=engine)
    ensure_analysis_result_schema()


def ensure_analysis_result_schema() -> None:
    """Add the raw OCR output column to existing installations."""
    if not inspect(engine).has_table("analysis_results"):
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE analysis_results "
                "ADD COLUMN IF NOT EXISTS extracted_text TEXT"
            )
        )


# Dependency function to get database session
# Used in FastAPI dependency injection for routes
def get_db() -> Generator:
    """
    Get a database session for a request.

    Yields:
        Database session object

    Finally:
        Closes the session after request completes
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to test database connection
def test_connection() -> dict:
    """
    Test if the database connection is working.

    Returns:
        dict: Status and message about the connection
    """
    try:
        with engine.connect() as connection:
            connection.execute(__import__('sqlalchemy').text("SELECT 1"))
            return {
                "status": "success",
                "message": "Successfully connected to PostgreSQL",
                "database_url": DATABASE_URL
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to connect: {str(e)}",
            "database_url": DATABASE_URL
        }
