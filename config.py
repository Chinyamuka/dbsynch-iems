"""
dbsync configuration.

Reads ~/.dbsync.json. Writes it on first run via
`dbsync init`, or partially via `dbsync config set-local`.

Two database targets:

- Aiven (remote):  host, port, database, user, password,
                   sslmode, sslrootcert
- Local (Local Postgres):  local_uri — a full
                   postgresql:// connection string

Aiven settings use TLS with the Aiven CA certificate.
sslmode=verify-ca negotiates cleanly on WSL where
sslmode=require sometimes stalls.

Mode 0600 — readable only by the owner.
"""

import json
import os
import stat
from dataclasses import dataclass, asdict
from pathlib import Path


CONFIG_PATH = Path.home() / ".dbsync.json"


@dataclass
class Config:
    """Everything dbsync needs to talk to Aiven and local."""

    # ---- Aiven ----
    name: str = "IEMS Aiven"
    host: str = ""
    port: int = 28480
    database: str = "defaultdb"
    user: str = "avnadmin"
    password: str = ""
    sslmode: str = "verify-ca"
    sslrootcert: str = ""
    iems_path: str = ""
    timeout: int = 30

    # ---- Local ----
    local_uri: str = ""

    def uri(self) -> str:
        """Build the SQLAlchemy-compatible Aiven URI."""
        base = (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.sslmode}"
        )
        if self.sslrootcert:
            base += f"&sslrootcert={self.sslrootcert}"
        return base

    def display_uri(self) -> str:
        """Same Aiven URI with the password redacted."""
        base = (
            f"postgresql://{self.user}:***"
            f"@{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.sslmode}"
        )
        if self.sslrootcert:
            base += f"&sslrootcert={self.sslrootcert}"
        return base

    def display_local_uri(self) -> str:
        """Local URI with the password redacted."""
        if not self.local_uri:
            return "(not configured)"
        return _redact_uri(self.local_uri)


def _redact_uri(uri: str) -> str:
    """Replace the password segment of a postgresql:// URI."""
    try:
        # Split on the last '@' before the host
        at = uri.rfind("@")
        if at == -1:
            return uri
        scheme_and_user = uri[:at]
        rest = uri[at:]
        # scheme_and_user = "postgresql://user:password"
        colon = scheme_and_user.rfind(":")
        if colon == -1:
            return uri
        return scheme_and_user[:colon] + ":***" + rest
    except Exception:
        return uri


def load() -> Config:
    """Read the config from ~/.dbsync.json."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"No config found at {CONFIG_PATH}.\n"
            f"Run: python dbsync.py init"
        )

    with CONFIG_PATH.open() as f:
        data = json.load(f)

    # Filter to fields the dataclass knows about. This
    # lets old config files survive new fields being
    # added, and new fields being added here without
    # breaking old config files.
    allowed = set(Config.__dataclass_fields__.keys())
    filtered = {k: v for k, v in data.items() if k in allowed}
    return Config(**filtered)


def save(config: Config) -> None:
    """Write the config file with mode 0600."""
    CONFIG_PATH.write_text(json.dumps(asdict(config), indent=2))
    os.chmod(CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)


def exists() -> bool:
    return CONFIG_PATH.exists()
