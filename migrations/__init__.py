"""Database schema migrations for AIWiki."""

from migrations.runner import get_migration_status, run_migrations

__all__ = ["run_migrations", "get_migration_status"]
