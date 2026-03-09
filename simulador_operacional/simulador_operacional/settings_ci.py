from .settings import *  # noqa


# Isolated database for CI and local clean-environment checks.
DATABASES["default"]["NAME"] = BASE_DIR / "db.ci.v2.sqlite3"

# Dedicated migration track for clean CI environments.
MIGRATION_MODULES = {"app": "app.migrations_ci"}
