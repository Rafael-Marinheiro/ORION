from .settings import *  # noqa


# Isolated database for CI and local clean-environment checks.
DATABASES["default"]["NAME"] = BASE_DIR / "db.ci.v2.sqlite3"

# A trilha consolidada já é definida em settings.py.
