"""
dbsync configuration.

Reads ~/.dbsync.json. Writes it on first run via
`dbsync init`.

The config file holds the Aiven connection details and
the path to the IEMS project (used by the 'upgrade'
command to shell out to Flask-Migrate).

Uses sslmode=verify-ca with the Aiven CA certificate
for maximum compatibility with WSL/OpenSSL quirks.
sslmode=require sometimes stalls on WSL during the SSL
handshake; verify-ca with the real CA negotiates
cleanly.

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
    """Everything dbsync needs to talk to Aiven."""
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

    def uri(self) -> str:
        """Build the SQLAlchemy-compatible connection URI."""
        base = (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.sslmode}"
        )
        if self.sslrootcert:
            base += f"&sslrootcert={self.sslrootcert}"
        return base

    def display_uri(self) -> str:
        """Same URI with the password redacted, for logging."""
        base = (
            f"postgresql://{self.user}:***"
            f"@{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.sslmode}"
        )
        if self.sslrootcert:
            base += f"&sslrootcert={self.sslrootcert}"
        return base


def load() -> Config:
    """
    Read the config from ~/.dbsync.json.

    Raises FileNotFoundError with a helpful message if
    the file does not exist.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"No config found at {CONFIG_PATH}.\n"
            f"Run: python dbsync.py init"
        )

    with CONFIG_PATH.open() as f:
        data = json.load(f)

    return Config(**data)


def save(config: Config) -> None:
    """Write the config file with mode 0600."""
    CONFIG_PATH.write_text(json.dumps(asdict(config), indent=2))
    os.chmod(CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)


def exists() -> bool:
    return CONFIG_PATH.exists()